from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from main.forms import ExperienceForm, ProjectForm
from main.models import Experience, Project

import datetime


# Urutan decorator penting: `login_required` di luar `permission_required`
# supaya anonim diarahkan ke /login/ dan pengguna login tanpa hak dapat 403.


def show_main(request):
    last_login = request.COOKIES.get("last_login", 'Belum ada sesi login / Cookie tidak ditemukan')
    context = {
        "name": "ANO",
        "npm": "2506615280",
        "study_program": "S1 Ilmu Komputer",
        "bio": "Iya ini bio, gatau mau nulis apa soalnya abis dihujat sama Yasmin. Jadi yaudah sekarang gini aja deh :d (Yasmin jahat)",
        "project_list": Project.objects.all(),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def show_experience(request):
    """Halaman publik /experience/ (read-only); CRUD ada di `manage_experience`."""
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all().order_by("-started_at")

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)
    context = {
        "name": "ANO",
        "experience_list": experiences,
        "title_query": title_query,
    }
    return render(request, "experience.html", context)

@login_required
@permission_required("main.change_experience", raise_exception=True)
def manage_experience(request):
    """Halaman manage /experience/manage/: tambah, cari (`?title=`), & hapus.

    Butuh `change_experience`: Editor & Owner boleh, pengguna biasa 403, dan
    pengunjung tanpa login diarahkan ke /login/.
    """
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all().order_by("-started_at")

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)

    context = {
        "name": "ANO",
        "experience_list": experiences,
        # Untuk mengisi ulang kotak pencarian; filternya sudah dilakukan di atas.
        "title_query": title_query,
        # Menentukan tombol "Tambah" di manage.html: Editor tidak punya add_*.
        "can_add": request.user.has_perm("main.add_experience"),
    }
    return render(request, "experience_manage.html", context)


def show_experience_detail(request, title):
    experience = get_object_or_404(Experience, title=title)
    context = {
        "name": "ANO",
        "experience": experience,
    }
    return render(request, "experience_detail.html", context)

def get_projects_json(request):
    """Endpoint JSON daftar project; mendukung filter `?title=`."""
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    projects_json = serializers.serialize("json", projects, use_natural_foreign_keys=True)
    return HttpResponse(projects_json, content_type="application/json")


def _projects_from_json(request):
    """Ambil daftar Project lewat jalur JSON: `get_projects_json` -> deserialize.

    Sengaja lewat JSON (meniru arsitektur client-server & memaksa endpoint API
    teruji); filter `?title=` dibaca endpoint-nya. Dipakai bersama oleh
    `show_projects` dan `manage_projects`.
    """
    json_response = get_projects_json(request)

    # `deserialize` mengembalikan generator -> wajib dihabiskan jadi list.
    deserialized = serializers.deserialize("json", json_response.content.decode("utf-8"))
    return [obj.object for obj in deserialized]


def show_projects(request):
    context = {
        "name": "ANO",
        "project_list": _projects_from_json(request),
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "project.html", context)

@login_required
@permission_required("main.change_project", raise_exception=True)
def manage_projects(request):
    context = {
        "name": "ANO",
        "project_list": _projects_from_json(request),
        "title_query": request.GET.get("title", "").strip(),
        # Menentukan tombol "Tambah" di manage.html: Editor tidak punya add_*.
        "can_add": request.user.has_perm("main.add_project"),
    }
    return render(request, "project_manage.html", context)


def show_project_detail(request, title):
    project = get_object_or_404(Project, title=title)
    context = {
        "name": "ANO",
        "project": project,
    }
    return render(request, "project_detail.html", context)

@login_required
@permission_required("main.add_experience", raise_exception=True)
def create_experience(request):
    """Tambah experience baru; butuh `add_experience` (hanya Owner, Editor 403)."""
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience baru berhasil ditambahkan!")
        return redirect("main:manage_experience")

    context = {
        "name": "ANO",
        "form": form,
    }
    return render(request, "experience_form.html", context)

@login_required
@permission_required("main.add_project", raise_exception=True)
def create_project(request):
    """Tambah project baru; butuh `add_project` (hanya Owner, Editor 403)."""
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project baru berhasil ditambahkan!")
        return redirect("main:manage_projects")

    context = {
        "name": "ANO",
        "form": form,
    }
    return render(request, "project_form.html", context)


def get_experiences_json(request):
    """Endpoint JSON daftar experience (filter `?title=`)."""
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all()

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)

    experiences_json = serializers.serialize("json", experiences, use_natural_foreign_keys=True)
    return HttpResponse(experiences_json, content_type="application/json")

@login_required
@permission_required("main.delete_project", raise_exception=True)
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project berhasil dihapus!")
        return redirect("main:manage_projects")

    return redirect("main:manage_projects")

@login_required
@permission_required("main.delete_experience", raise_exception=True)
def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Experience berhasil dihapus!")
        return redirect("main:manage_experience")

    return redirect("main:manage_experience")

@login_required
@permission_required("main.change_experience", raise_exception=True)
def update_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience berhasil diperbarui!")
        return redirect("main:manage_experience")

    context = {
        "name": "ANO",
        "form": form,
        "experience": experience,
    }
    return render(request, "experience_update.html", context)

@login_required
@permission_required("main.change_project", raise_exception=True)
def update_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = ProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project berhasil diperbarui!")
        return redirect("main:manage_projects")

    context = {
        "name": "ANO",
        "form": form,
        "project": project,
    }
    return render(request, "project_update.html", context)

# Tanpa cek permission CRUD: cukup login (semua akun boleh memberi star).
@login_required(login_url="/login/")
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        if request.user in project.starred_by.all():
            project.starred_by.remove(request.user)
        else:
            project.starred_by.add(request.user)

    next_url = request.POST.get("next")
    if not next_url or not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        next_url = reverse("main:show_projects")
    return redirect(next_url)


# Kembar dari `toggle_star`, untuk Experience (cukup login, tanpa cek CRUD).
@login_required(login_url="/login/")
def toggle_experience_star(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        if request.user in experience.starred_by.all():
            experience.starred_by.remove(request.user)
        else:
            experience.starred_by.add(request.user)

    next_url = request.POST.get("next")
    if not next_url or not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        next_url = reverse("main:show_experience")
    return redirect(next_url)


def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "ANO",
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, form.get_user())
        response = redirect("main:show_main")
        response.set_cookie("last_login", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return response

    context = {
        "name": "ANO",
        "form": form,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie("last_login")
    return response