from django.contrib import admin
from django.urls import path
from App import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("image_details", views.image_details, name="image_details"),
    path('model_process', views.model_process, name="model_process"),
    path('model_process_image', views.model_process_image, name="model_process_image"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
