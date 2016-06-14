from django.utils.crypto import get_random_string


def enum_to_choices(enum):
    return ((item.value, item.name) for item in list(enum))

def generate_user_uid():
    return get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')
