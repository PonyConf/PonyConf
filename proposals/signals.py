from django.dispatch import Signal


__all__ = [ 'talk_added', 'talk_edited' ]


talk_added = Signal(providing_args=["sender", "instance", "author"])
talk_edited = Signal(providing_args=["sender", "instance", "author"])
