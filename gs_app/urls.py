from django.urls import path
from . import views

urlpatterns = [
     path("", views.index, name="index"),
     path('read_gs',views.read_gs,name="read_gs"),
     path("download", views.download, name="download"),
     path('/upload', views.upload_view, name="upload"),
]