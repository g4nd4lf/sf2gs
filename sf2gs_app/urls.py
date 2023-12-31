from django.urls import path
from . import views

urlpatterns = [
     path("", views.index, name="index"),
     path("upload", views.upload_index, name="upload"),
     path("upload-file", views.upload_file, name="upload-file"),
     path("plot", views.plot_view, name="plot"),
     path("download", views.download_view, name="download-sf2gs"),
     path("updatedb",views.updatedb,name="updatedb")
]