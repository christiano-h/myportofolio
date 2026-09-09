from django.shortcuts import render

from main.models import Experience


def show_main(request):
    context = {
        "name": "Christiano H",
        "npm": "2506615280",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Halo semuanya :D Selamat datang di website apapun ini terserah presepsi kalian, maaf"
            "yah gak sebagus punya kalian. Makasih sudah ngestalk sampai sini (づ◡﹏◡)づ"
        ),
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Christiano H",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)