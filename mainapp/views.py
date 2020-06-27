import json
import random

from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import *
from chat.views import get_contacts, get_chat_rooms, get_chat_room
from chat.views import get_recent_chats, other_user_party
from .models import Cohort, Question, Notification, Answer, Reply
from accounts.models import UserProfile
from data_structures.LinkedLists.SingleLinkedList import SingleLinkedList


@method_decorator(login_required,
                  name='dispatch')
class HomeView(ListView):
    template_name = 'mainapp/home.html'
    context_object_name = 'quiz_and_ans'
    model = Question

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        data = get_user_data(self.request.user)
        notificationsCount = Notification.objects.filter(recipient=self.request.user, seen=False).count()
        today = timezone.now()
        yesterday = today - timezone.timedelta(days=1)
        context.update({
            'active_link': 'home_link',
            'to_recommend': data['to_recommend'],
            'contacts': data['contacts'],
            'user_cohorts': data['user_cohorts'],
            'today': today.date(),
            'yesterday': yesterday,
            'unread_messages': data['unread_messages'],
            'unread_notifications': notificationsCount
        })
        return context

    def get_queryset(self):
        self.reslove_integrity()
        questions = get_user_data(self.request.user)['questions']
        qs = Question.objects.annotate(number_of_answers=Count('answer')).order_by('-time')
        return [(q, Answer.objects.filter(question=q).order_by('-time')) for q in qs if q in questions]

    def reslove_integrity(self):
        user = self.request.user
        profile = user.userprofile
        cohort1 = profile.study_field
        cohort2 = profile.current_interest
        if cohort1 and cohort1.members.filter(id=user.id).count() == 0:
            cohort1.members.add(user)
        if cohort2 and cohort2.members.filter(id=user.id).count() == 0:
            cohort1.members.add(user)


@method_decorator(login_required, name='dispatch')
class GroupsView(ListView):
    template_name = 'mainapp/all-groups.html'
    context_object_name = 'cohorts_list'
    model = Cohort

    def get_context_data(self, **kwargs):
        data = get_user_data(self.request.user)
        notificationsCount = Notification.objects.filter(recipient=self.request.user, seen=False).count()
        context = super(GroupsView, self).get_context_data(**kwargs)
        context.update({
            'active_link': 'groups_link',
            'contacts': data['contacts'],
            'user_cohorts': data['user_cohorts'],
            'unread_messages': data['unread_messages'],
            'unread_notifications': notificationsCount
        })
        return context

    def get_queryset(self):
        groups_to_display = get_recommendable(self.request.user)
        return groups_to_display


@login_required
def MessagesView(request):
    data = get_user_data(request.user)
    notificationsCount = Notification.objects.filter(recipient=request.user, seen=False).count()
    messages = get_recent_chats(request.user)
    return render(request, 'mainapp/messages.html',
                  {'active_link': 'messages_link',
                   'messages': messages,
                   'contacts': data['contacts'],
                   'user_cohorts': data['user_cohorts'],
                   'unread_notifications': notificationsCount
                   })


@method_decorator(login_required, name='dispatch')
class NotificationsView(ListView):
    template_name = 'mainapp/notifications.html'
    context_object_name = 'notifications'
    model = Notification

    def get_context_data(self, **kwargs):
        data = get_user_data(self.request.user)
        notifications = Notification.objects.filter(recipient=self.request.user, seen=False)
        for item in notifications:
            item.seen = True
            item.save()
        context = super(NotificationsView, self).get_context_data(**kwargs)
        context.update({
            'active_link': 'notifications_link',
            'contacts': data['contacts'],
            'user_cohorts': data['user_cohorts'],
            'unread_messages': data['unread_messages'],
        })
        return context

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-time')


@method_decorator(login_required, name='dispatch')
class ProfileView(DetailView):
    model = UserProfile
    template_name = 'mainapp/profile.html'

    def get_context_data(self, **kwargs):
        cohorts = self.request.user.cohorts.all()
        context = super(ProfileView, self).get_context_data(**kwargs)
        chatroom = get_chat_room(UserProfile.objects.get(id=self.kwargs['pk']).user.id, self.request.user.id)
        context.update({
            'cohorts': cohorts,
            'chatroom': chatroom,
            'active_link': 'home_link',
        })
        return context


@method_decorator(login_required, name='dispatch')
class UserGroupsView(ListView):
    template_name = 'mainapp/user-groups.html'
    context_object_name = 'user_cohorts'
    model = Cohort

    def get_queryset(self):
        user_cohorts = self.request.user.cohorts.all()
        all_cohorts = Cohort.objects.annotate(number_of_members=Count('members', distinct=True),
                                              total_posts=Count('question'))
        return [cohort for cohort in all_cohorts if cohort in user_cohorts]


def exitGroup(request):
    if request.method == 'POST':
        groupId = int(request.POST['cohort_id'])
        if groupId:
            try:
                cohort = Cohort.objects.get(id=groupId)
                cohort.members.remove(request.user)
                profile = request.user.userprofile
                if profile.current_interest == cohort:
                    profile.current_interest = None
                    profile.save()
            except Cohort.DoesNotExist:
                pass

    return redirect('mainapp:userGroupsView', pk=request.user.id)


def get_user_data(user):
    contacts = get_contacts(user)  # fetches users to display at quick-chat panel
    print(contacts)
    user_cohorts = user.cohorts.all()
    '''using a linked_list to dynamically store questions/posts that can be displayed to the user(newsfeed)'''
    ids_list = SingleLinkedList()
    cohorts_list = [cohort for cohort in user_cohorts]
    for cohort in cohorts_list:
        questions = Question.objects.filter(target_cohort=cohort).order_by('-time')[:100]
        if questions:
            for q in questions:
                ids_list.insert_at_end(q.id)
    questions_list = [Question.objects.get(id=quiz_id) for quiz_id in ids_list.display_list()]
    to_recommend = get_recommendable(user)
    return {'to_recommend': to_recommend[:100], 'contacts': contacts[0], 'unread_messages': contacts[1],
            'questions': questions_list[:100], 'user_cohorts': user_cohorts}


@login_required
def join_groups(request):
    if request.method == 'POST':
        to_join = request.POST.getlist('to_join')
        if to_join:
            to_join = list(map(int, to_join))
            for cohort_id in to_join:
                try:
                    cohort = Cohort.objects.get(id=cohort_id)
                    cohort.members.add(request.user)
                except Cohort.DoesNotExist:
                    print('Cohort not found')
            page = request.POST['page']
            if page == 'home':
                return redirect('mainapp:homeView')
            else:
                return redirect('mainapp:groupsView')

    return redirect('mainapp:homeView')


def get_recommendable(user):
    user_cohorts = user.cohorts.all()
    housing_cohort = user.userprofile.study_field
    all_cohorts = housing_cohort.get_descendants(include_self=False).annotate(number_of_members=Count('members'),
                                                                              total_posts=Count('question'))
    to_recommend = [cohort for cohort in all_cohorts if cohort not in user_cohorts]
    random.shuffle(to_recommend)
    return to_recommend[:20]


@csrf_exempt
@login_required
def create_post(request):
    if request.is_ajax() or request.method == 'POST':
        content = request.POST['question-text']
        target_group_id = request.POST['question-group']
        if target_group_id:
            target_group = get_object_or_404(Cohort, id=int(target_group_id))
            try:
                image = request.FILES['question-image']
                handle_uploaded_file(image, 'images')
                Question.objects.create(author=request.user, content=content,
                                        image='images' + '/' + image.name, target_cohort=target_group)
                response = {'message': 'success', 'code': 0}
            except MultiValueDictKeyError:
                if content:
                    Question.objects.create(author=request.user, content=content, target_cohort=target_group)
                    response = {'message': 'success', 'code': 0}
                else:
                    response = {'message': 'Content or Image is required', 'code': 1}
        else:
            response = {'message': 'Please select the target group', 'code': 1}
        if request.is_ajax():
            return JsonResponse(response)

    return redirect('mainapp:homeView')


@login_required
def add_answer(request):
    if request.method == 'POST':
        content = request.POST['answer']
        author = request.user
        question = Question.objects.get(id=int(request.POST['question']))
        new_answer = Answer(content=content, author=author, question=question)
        new_answer.save()
        question.save()

    return redirect('mainapp:homeView')


# saving the uploaded media file
def handle_uploaded_file(file, desired_location):
    with open(settings.MEDIA_ROOT + '/' + desired_location + '/' + file.name, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)


def number_of_members(cohort):
    return UserProfile.objects.filter(user_groups__contains=[cohort.id]).count()
