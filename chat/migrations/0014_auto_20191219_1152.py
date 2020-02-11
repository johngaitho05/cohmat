# Generated by Django 2.2.6 on 2019-12-19 08:52

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0013_auto_20191219_1150'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='time',
            field=models.CharField(default=datetime.datetime(2019, 12, 19, 8, 52, 50, 393279, tzinfo=utc), max_length=10),
        ),
        migrations.AlterField(
            model_name='message',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2019, 12, 19, 8, 52, 50, 392280, tzinfo=utc)),
        ),
    ]
