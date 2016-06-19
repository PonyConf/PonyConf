from django.dispatch import Signal

new_talk = Signal(providing_args=["sender", "instance"])
