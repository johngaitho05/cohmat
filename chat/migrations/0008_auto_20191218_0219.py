# Generated by Django 2.2.6 on 2019-12-17 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_auto_20191218_0200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='time',
            field=models.CharField(default='02:19', max_length=10),
        ),
    ]
