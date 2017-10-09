from __future__ import unicode_literals

import autoslug.fields
import colorful.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('cfp', '0012_talk_confirmed'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, verbose_name='Name')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='name')),
                ('color', colorful.fields.RGBColorField(default='#ffffff', verbose_name='Color')),
                ('inverted', models.BooleanField(default=False)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sites.Site')),
            ],
        ),
        migrations.AddField(
            model_name='talk',
            name='tags',
            field=models.ManyToManyField(to='cfp.Tag'),
        ),
    ]
