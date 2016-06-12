from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib import messages


@receiver(user_logged_in)
def on_user_logged_in(sender, request, **kwargs):
    messages.success(request, 'Welcome!', fail_silently=True)  # FIXME


@receiver(user_logged_out)
def on_user_logged_out(sender, request, **kwargs):
    messages.success(request, 'Goodbye!', fail_silently=True)  # FIXME
