# Generated by Django 2.2.6 on 2020-03-12 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_auto_20200312_1118'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='school',
            field=models.CharField(default='', max_length=250),
            preserve_default=False,
        ),
    ]
