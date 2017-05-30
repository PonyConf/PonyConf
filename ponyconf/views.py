from django.shortcuts import render


def home(request):
    return render(request, 'ponyconf/home.html')
