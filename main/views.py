from django.shortcuts import get_object_or_404, render

from main.models import Experience


def show_main(request):
    context = {
        "name": "Christiano H",
        "npm": "2506615280",
        "study_program": "S1 Ilmu Komputer",
        "bio": "Iya ini bio, gatau mau nulis apa soalnya abis dihujat sama Yasmin. Jadi yaudah sekarang gini aja deh :d (Yasmin jahat)",
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Christiano H",
        "experience_list": Experience.objects.all().order_by("-started_at"),
    }
    return render(request, "experience.html", context)


def show_experience_detail(request, pk):
    experience = get_object_or_404(Experience, pk=pk)
    context = {
        "name": "Christiano H",
        "experience": experience,
    }
    return render(request, "experience_detail.html", context)
