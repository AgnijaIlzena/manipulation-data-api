from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload, name="upload"),
    path("debug-sentry/", views.debug_sentry, name="debug_sentry"),
]
