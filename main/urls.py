from django.urls import path

from main.views import show_main, show_experience, show_experience_detail

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("experience/<uuid:pk>/", show_experience_detail, name="show_experience_detail"),
]
