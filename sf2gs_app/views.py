from django.shortcuts import render

def index(request):
    return render(request, "sf2gs_app/index.html")