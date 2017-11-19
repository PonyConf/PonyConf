from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Profile(models.Model):

    user = models.OneToOneField(User)
    phone_number = models.CharField(max_length=16, blank=True, default='', verbose_name=_('Phone number'))
    sms_prefered = models.BooleanField(default=False, verbose_name=_('SMS prefered'))
    biography = models.TextField(blank=True, verbose_name=_('Biography'))

    twitter = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Twitter'))
    linkedin = models.CharField(max_length=100, blank=True, default='', verbose_name=_('LinkedIn'))
    github = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Github'))
    website = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Website'))
    facebook = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Facebook'))
    mastodon = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Mastodon'))

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_absolute_url(self):
        return reverse('profile')
