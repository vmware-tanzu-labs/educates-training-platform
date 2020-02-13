from django.shortcuts import render

def index(request):
    return render(request, 'eduk8s/index.html')
