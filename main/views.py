from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.forms import ExperienceForm, ProjectForm
from main.models import Experience, Project


def show_main(request):
    context = {
        "name": "Christiano H",
        "npm": "2506615280",
        "study_program": "S1 Ilmu Komputer",
        "bio": "Iya ini bio, gatau mau nulis apa soalnya abis dihujat sama Yasmin. Jadi yaudah sekarang gini aja deh :d (Yasmin jahat)",
        "project_list": Project.objects.all(),
    }
    return render(request, "index.html", context)


def show_experience(request):
    """Halaman publik /experience/ (read-only).

    Hanya menampilkan daftar experience; tiap kartu bisa diklik menuju halaman
    blog-nya. Tambah/hapus ada di `manage_experience`.
    """
    context = {
        "name": "Christiano H",
        "experience_list": Experience.objects.all().order_by("-started_at"),
    }
    return render(request, "experience.html", context)


def manage_experience(request):
    """Halaman manage /experience/manage/ (tambah & hapus experience)."""
    context = {
        "name": "Christiano H",
        "experience_list": Experience.objects.all().order_by("-started_at"),
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

    projects_json = serializers.serialize("json", projects)
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


def manage_projects(request):
    """Halaman manage /projects/manage/ (tambah & hapus project)."""
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


def create_experience(request):
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


def create_project(request):
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


def delete_experience(request, experience_id):
    """Hapus experience berdasarkan primary key-nya (UUID)."""
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Experience berhasil dihapus!")
        return redirect("main:manage_experience")

    return redirect("main:manage_experience")
