# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-11 17:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0018_talk_room'),
    ]

    operations = [
        migrations.AlterField(
            model_name='talk',
            name='room',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='planning.Room'),
        ),
        migrations.AlterField(
            model_name='talk',
            name='start_date',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]