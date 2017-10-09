# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-27 18:20
from __future__ import unicode_literals

import cfp.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cfp', '0009_conference_schedule_publishing_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='talk',
            name='materials',
            field=models.FileField(help_text='You can use this field to share some materials related to your intervention.', null=True, upload_to=cfp.models.talks_materials_destination, verbose_name='Materials'),
        ),
        migrations.AddField(
            model_name='talk',
            name='video',
            field=models.URLField(blank=True, default='', max_length=1000, verbose_name='Video URL'),
        ),
    ]