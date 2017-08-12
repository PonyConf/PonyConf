# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-01 15:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mailing.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('author', models.EmailField(blank=True, max_length=254)),
                ('content', models.TextField(blank=True)),
                ('token', models.CharField(default=mailing.models.generate_message_token, max_length=64, unique=True)),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='MessageCorrespondent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('token', models.CharField(default=mailing.models.generate_message_token, max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='MessageThread',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('token', models.CharField(default=mailing.models.generate_message_token, max_length=64, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='thread',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mailing.MessageThread'),
        ),
    ]