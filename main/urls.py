from django.urls import path

from main.views import show_main, show_experience, show_experience_detail, show_project_detail

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("experience/<str:title>/", show_experience_detail, name="show_experience_detail"),
    path("project/<str:title>/", show_project_detail, name="show_project_detail"),
]
