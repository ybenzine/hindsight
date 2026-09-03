"""Root URL configuration for the Hindsight project.

Docs: https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path

from config.views import home

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
]
