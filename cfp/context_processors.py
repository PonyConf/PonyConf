from .utils import get_current_conf


def conference(request):
    return {'conference': get_current_conf(request)}
