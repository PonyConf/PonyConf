from django.utils.crypto import get_random_string


def generate_user_uid():
    return get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')
