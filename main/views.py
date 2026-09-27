from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from django.contrib.auth.decorators import login_required  
from django.core.exceptions import PermissionDenied        

from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from main.forms import ExperienceForm, ProjectForm
from main.models import Experience, Project

import datetime


def show_main(request):
    last_login = request.COOKIES.get("last_login", 'Belum ada sesi login / Cookie tidak ditemukan')
    context = {
        "name": "Christiano H",
        "npm": "2506615280",
        "study_program": "S1 Ilmu Komputer",
        "bio": "Iya ini bio, gatau mau nulis apa soalnya abis dihujat sama Yasmin. Jadi yaudah sekarang gini aja deh :d (Yasmin jahat)",
        "project_list": Project.objects.all(),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def show_experience(request):
    """Halaman publik /experience/ (read-only).

    Hanya menampilkan daftar experience; tiap kartu bisa diklik menuju halaman
    blog-nya. Tambah/hapus ada di `manage_experience`.
    """
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all().order_by("-started_at")

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)
    context = {
        "name": "Christiano H",
        "experience_list": experiences,
        "title_query": title_query,
    }
    return render(request, "experience.html", context)

@login_required(login_url="/login/")
def manage_experience(request):
    """Halaman manage /experience/manage/ (tambah, cari, & hapus experience).

    Mendukung pencarian `?title=` supaya halaman ini bisa memakai kerangka yang
    sama dengan /projects/manage/ (`templates/manage.html`).
    """
    if not request.user.is_superuser:
        raise PermissionDenied
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all().order_by("-started_at")

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)

    context = {
        "name": "Christiano H",
        "experience_list": experiences,
        # Hanya untuk mengisi ulang kotak pencarian; penyaringan sesungguhnya
        # sudah dilakukan filter di atas.
        "title_query": title_query,
    }
    return render(request, "experience_manage.html", context)


def show_experience_detail(request, title):
    experience = get_object_or_404(Experience, title=title)
    context = {
        "name": "Christiano H",
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
    """Ambil daftar Project lewat jalur JSON (data + query `?title=`).

    Data sengaja TIDAK diambil langsung dari ORM. Alurnya:
    `get_projects_json` -> HTTP response JSON -> di-deserialize balik menjadi
    objek `Project` -> dikirim ke template. Pola ini meniru arsitektur
    client-server terpisah, sama seperti yang nanti dilakukan `fetch()` di
    browser, sekaligus memaksa endpoint API-nya teruji sejak sekarang.

    Redundant? Ya. Filter `?title=` tetap jalan karena `get_projects_json`
    sendiri yang membacanya, jadi query string tidak diolah dua kali.

    Dipakai bersama oleh halaman publik (`show_projects`) dan halaman manage
    (`manage_projects`) supaya tidak ada logika yang terduplikasi.
    """
    json_response = get_projects_json(request)

    # `deserialize` mengembalikan generator -> WAJIB dihabiskan jadi list,
    # kalau tidak isinya habis setelah sekali pakai.
    deserialized = serializers.deserialize("json", json_response.content.decode("utf-8"))
    return [obj.object for obj in deserialized]


def show_projects(request):
    """Halaman publik /projects/ (read-only).

    Kartunya memakai markup carousel yang sama dengan /experience/ sehingga
    tampilannya konsisten; tiap kartu mengarah ke blog `/project/<title>/`.
    Tambah/hapus ada di `manage_projects`.
    """
    context = {
        "name": "Christiano H",
        "project_list": _projects_from_json(request),
        # Hanya untuk mengisi ulang kotak pencarian; penyaringan sesungguhnya
        # sudah dilakukan `get_projects_json`.
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "project.html", context)

@login_required(login_url="/login/")
def manage_projects(request):
    """Halaman manage /projects/manage/ (tambah & hapus project)."""
    if not request.user.is_superuser:
        raise PermissionDenied
    context = {
        "name": "Christiano H",
        "project_list": _projects_from_json(request),
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "project_manage.html", context)


def show_project_detail(request, title):
    project = get_object_or_404(Project, title=title)
    context = {
        "name": "Christiano H",
        "project": project,
    }
    return render(request, "project_detail.html", context)

@login_required(login_url="/login/")
def create_experience(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience baru berhasil ditambahkan!")
        return redirect("main:manage_experience")

    context = {
        "name": "Christiano H",
        "form": form,
    }
    return render(request, "experience_form.html", context)

@login_required(login_url="/login/")
def create_project(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project baru berhasil ditambahkan!")
        return redirect("main:manage_projects")

    context = {
        "name": "Christiano H",
        "form": form,
    }
    return render(request, "project_form.html", context)


def get_experiences_json(request):
    title_query = request.GET.get("title", "").strip()
    experiences = Experience.objects.all()

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)

    experiences_json = serializers.serialize("json", experiences)
    return HttpResponse(experiences_json, content_type="application/json")

@login_required(login_url="/login/")
def delete_project(request, project_id):
    """Hapus project berdasarkan primary key-nya.

    Memakai pk, bukan judul, karena `<str:title>` tidak menerima karakter `/`
    (judul seperti "UI/UX Redesign" bikin `{% url %}` gagal alias 500) dan
    judul tidak dijamin unik (`get_object_or_404` bisa melempar
    `MultipleObjectsReturned`). Dengan pk, dua-duanya mustahil terjadi.
    """
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project berhasil dihapus!")
        return redirect("main:manage_projects")

    return redirect("main:manage_projects")

@login_required(login_url="/login/")
def delete_experience(request, experience_id):
    """Hapus experience berdasarkan primary key-nya (UUID)."""
    if not request.user.is_superuser:
        raise PermissionDenied
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Experience berhasil dihapus!")
        return redirect("main:manage_experience")

    return redirect("main:manage_experience")

@login_required(login_url="/login/")
def update_experience(request, experience_id):
    """Ubah experience berdasarkan primary key-nya.

    Memakai pk, bukan judul, mengikuti alasan `delete_experience`: judul tidak
    dijamin unik dan bisa berubah, sehingga URL berbasis judul tidak stabil
    (alamat lama mati setelah judul diubah, dan judul kembar membuat
    `get_object_or_404` melempar MultipleObjectsReturned alias 500).
    """
    if not request.user.is_superuser:
        raise PermissionDenied
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience berhasil diperbarui!")
        return redirect("main:manage_experience")

    context = {
        "name": "Christiano H",
        "form": form,
        "experience": experience,
    }
    return render(request, "experience_update.html", context)

@login_required(login_url="/login/")
def update_project(request, project_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    """Ubah project berdasarkan primary key-nya (alasan sama seperti experience)."""
    project = get_object_or_404(Project, pk=project_id)
    form = ProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project berhasil diperbarui!")
        return redirect("main:manage_projects")

    context = {
        "name": "Christiano H",
        "form": form,
        "project": project,
    }
    return render(request, "project_update.html", context)

# Tanpa cek is_superuser: semua akun yang sudah login boleh memberi star
@login_required(login_url="/login/")
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        # Kalau akun ini sudah pernah memberi star, batalkan star-nya.
        # Kalau belum, tambahkan star.
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


def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Christiano H",
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
        "name": "Christiano H",
        "form": form,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie("last_login")
    return response