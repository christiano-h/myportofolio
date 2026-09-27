from django.urls import path

from main.views import (
    create_experience,
    create_project,
    delete_experience,
    delete_project,
    get_experiences_json,
    get_projects_json,
    logout_user,
    manage_experience,
    manage_projects,
    show_experience,
    show_experience_detail,
    show_main,
    show_project_detail,
    show_projects,
    toggle_star,
    update_experience,
    update_project,
    register,
    login_user,
)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),

    # === Halaman publik (read-only): hanya menampilkan, kartu bisa diklik ke blog ===
    path("experience/", show_experience, name="show_experience"),
    path("projects/", show_projects, name="show_projects"),

    # === Halaman manage (add & remove) ===
    path("experience/manage/", manage_experience, name="manage_experience"),
    path("experience/manage/add/", create_experience, name="create_experience"),
    path("experience/manage/<uuid:experience_id>/delete/", delete_experience, name="delete_experience"),
    path("experience/manage/<uuid:experience_id>/update/", update_experience, name="update_experience"),
    path("projects/manage/", manage_projects, name="manage_projects"),
    path("projects/manage/add/", create_project, name="create_project"),
    path("projects/manage/<int:project_id>/delete/", delete_project, name="delete_project"),
    path("projects/manage/<int:project_id>/update/", update_project, name="update_project"),

    # === Halaman blog (detail) ===
    path("experience/<path:title>/", show_experience_detail, name="show_experience_detail"),
    
    path("projects/<int:project_id>/star/", toggle_star, name="toggle_star"),
    path("projects/<path:title>/", show_project_detail, name="show_project_detail"),

    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),

    path("api/projects/", get_projects_json, name="get_projects_json"),
    path("api/experiences/", get_experiences_json, name="get_experiences_json"),
]
