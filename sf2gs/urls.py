from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sf2gs/', include('sf2gs_app.urls') ),
    path('sf2gs/gs', include('gs_app.urls') )   
]
