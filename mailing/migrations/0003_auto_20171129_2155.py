# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-29 21:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mailing.models


def forward(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Message = apps.get_model("mailing", "Message")
    MessageAuthor = apps.get_model("mailing", "MessageAuthor")
    for message in Message.objects.using(db_alias).all():
        message.new_author, _ = MessageAuthor.objects.using(db_alias).get_or_create(author_type=message.author_type, author_id=message.author_id)
        message.save()


def backward(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Message = apps.get_model("mailing", "Message")
    ContentType = apps.get_model("contenttypes", "ContentType")
    for message in Message.objects.using(db_alias).all():
        author_type = message.new_author.author_type
        message.author_type = message.new_author.author_type
        message.author_id = message.new_author.author_id
        AuthorType = apps.get_model(author_type.app_label, author_type.model)
        author = AuthorType.objects.get(pk=message.author_id)
        if author_type.model == 'conference':
            message.from_email = author.contact_email
        else:
            message.from_email = author.email
        message.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('mailing', '0002_message_author'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageAuthor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_id', models.PositiveIntegerField(blank=True, null=True)),
                ('token', models.CharField(default=mailing.models.generate_message_token, max_length=64, unique=True)),
                ('author_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='new_author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='mailing.MessageAuthor'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='message',
            name='from_email',
            field=models.EmailField(blank=True, null=True),
        ),
        migrations.RunPython(forward, backward),
        migrations.RemoveField(
            model_name='message',
            name='author_id',
        ),
        migrations.RemoveField(
            model_name='message',
            name='author_type',
        ),
        migrations.RemoveField(
            model_name='message',
            name='from_email',
        ),
        migrations.RenameField(
            model_name='message',
            old_name='new_author',
            new_name='author',
        ),
        migrations.AlterField(
            model_name='message',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mailing.MessageAuthor'),
        ),
        migrations.AddField(
            model_name='message',
            name='in_reply_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mailing.Message'),
        ),
        migrations.AddField(
            model_name='message',
            name='subject',
            field=models.CharField(blank=True, max_length=1000),
        ),
    ]
