"""
Test untuk aplikasi main.

Cakupan:
1. Model    -> Experience (__str__, is_ongoing, PK UUID, default category)
               Project    -> __str__, PK integer, field opsional
2. Routing  -> reverse() semua nama URL, termasuk encoding judul
3. View     -> status code, template, isi context, penanganan 404
4. Template -> link kartu ke halaman detail, guard kondisional, teks fallback
5. Fixture  -> initial_data.json bisa dimuat dan semua datanya bisa dibuka

Jalankan: python manage.py test
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Project


class ExperienceModelTests(TestCase):
    """Perilaku Experience yang dipakai di admin, template, dan URL."""

    def test_str_menggabungkan_job_title_dan_title(self):
        exp = Experience.objects.create(title="SELARAS 5.0", job_title="Wakil Ketua")
        self.assertEqual(str(exp), "Wakil Ketua — SELARAS 5.0")

    def test_str_hanya_title_kalau_job_title_string_kosong(self):
        exp = Experience.objects.create(title="SELARAS 5.0", job_title="")
        self.assertEqual(str(exp), "SELARAS 5.0")

    def test_str_hanya_title_kalau_job_title_none(self):
        exp = Experience.objects.create(title="SELARAS 5.0")
        self.assertIsNone(exp.job_title)
        self.assertEqual(str(exp), "SELARAS 5.0")

    def test_is_ongoing_true_kalau_ended_at_belum_diisi(self):
        exp = Experience.objects.create(title="Retreat")
        self.assertIsNone(exp.ended_at)
        self.assertTrue(exp.is_ongoing)

    def test_is_ongoing_false_kalau_ended_at_sudah_diisi(self):
        exp = Experience.objects.create(title="Retreat", ended_at=timezone.now())
        self.assertFalse(exp.is_ongoing)

    def test_id_otomatis_uuid_dan_unik(self):
        a = Experience.objects.create(title="A")
        b = Experience.objects.create(title="B")
        self.assertEqual(len(str(a.id)), 36)
        self.assertNotEqual(a.id, b.id)

    def test_category_default_full_time(self):
        self.assertEqual(Experience.objects.create(title="A").category, "full-time")

    def test_category_bisa_diisi_choice_lain(self):
        exp = Experience.objects.create(title="A", category="volunteer")
        self.assertEqual(exp.category, "volunteer")


class ProjectModelTests(TestCase):
    def test_str_mengembalikan_title(self):
        self.assertEqual(str(Project.objects.create(title="SINTAKS")), "SINTAKS")

    def test_id_berupa_integer_auto_increment(self):
        self.assertIsInstance(Project.objects.create(title="SINTAKS").pk, int)

    def test_description_dan_content_opsional(self):
        project = Project.objects.create(title="SINTAKS")
        project.refresh_from_db()
        self.assertIsNone(project.description)
        self.assertIsNone(project.content)


class UrlRoutingTests(TestCase):
    def test_reverse_semua_url(self):
        kasus = [
            ("main:show_main", [], "/"),
            ("main:show_experience", [], "/experience/"),
            ("main:show_experience_detail", ["SELARAS 5.0"], "/experience/SELARAS%205.0/"),
            ("main:show_project_detail", ["SINTAKS"], "/project/SINTAKS/"),
            ("main:show_project_detail", ["Ini ikan apa?"], "/project/Ini%20ikan%20apa%3F/"),
        ]
        for nama, args, diharapkan in kasus:
            with self.subTest(nama=nama, args=args):
                self.assertEqual(reverse(nama, args=args), diharapkan)


class ShowMainViewTests(TestCase):
    def setUp(self):
        Project.objects.all().delete()
        Project.objects.create(
            title="SINTAKS",
            description="Ayooo semua daftar sintaks",
            thumbnail="/static/css/img/daftar_sintaks.jpg",
        )

    def test_status_template_dan_context(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertEqual(response.context["name"], "Christiano H")
        self.assertEqual(response.context["npm"], "2506615280")
        self.assertEqual(response.context["study_program"], "S1 Ilmu Komputer")
        self.assertTrue(response.context["bio"])

    def test_menampilkan_semua_project(self):
        Project.objects.create(title="SCUBAAAAA")
        response = self.client.get(reverse("main:show_main"))
        self.assertEqual(len(response.context["project_list"]), 2)
        self.assertContains(response, "SINTAKS")
        self.assertContains(response, "SCUBAAAAA")

    def test_kartu_project_punya_link_ke_halaman_detail(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(response, "project-card-link")
        self.assertContains(response, "/project/SINTAKS/")

    def test_project_tanpa_thumbnail_tidak_menambah_tag_img(self):
        sebelum = self.client.get(reverse("main:show_main")).content.decode().count("<img")
        Project.objects.create(title="Tanpa Gambar")
        sesudah = self.client.get(reverse("main:show_main")).content.decode().count("<img")
        self.assertEqual(sesudah, sebelum)

    def test_pesan_kosong_kalau_belum_ada_project(self):
        Project.objects.all().delete()
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(response, "Belum ada proyek untuk ditampilkan.")


class ShowExperienceViewTests(TestCase):
    def setUp(self):
        # Migrasi 0005 (seed RISTEK) juga jalan di DB test -> bersihkan dulu
        Experience.objects.all().delete()
        self.lama = Experience.objects.create(
            title="Pengalaman Lama", job_title="Staf Audit", summary="Ringkasan lama"
        )
        self.baru = Experience.objects.create(
            title="Pengalaman Baru", job_title="Ketua", summary="Ringkasan baru"
        )
        Experience.objects.filter(pk=self.lama.pk).update(
            started_at=timezone.now() - timedelta(days=30)
        )

    def test_status_dan_template(self):
        response = self.client.get(reverse("main:show_experience"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")

    def test_urutan_terbaru_dulu(self):
        response = self.client.get(reverse("main:show_experience"))
        judul = [e.title for e in response.context["experience_list"]]
        self.assertEqual(judul, ["Pengalaman Baru", "Pengalaman Lama"])

    def test_tidak_menampilkan_project(self):
        Project.objects.create(title="Project X")
        response = self.client.get(reverse("main:show_experience"))
        self.assertEqual(len(response.context["experience_list"]), 2)
        self.assertNotContains(response, "Project X")

    def test_kartu_punya_link_ke_halaman_detail(self):
        response = self.client.get(reverse("main:show_experience"))
        self.assertContains(response, "project-card-link")
        self.assertContains(response, "/experience/Pengalaman%20Baru/")

    def test_kicker_dan_jabatan_dirender_di_kartu(self):
        response = self.client.get(reverse("main:show_experience"))
        self.assertContains(response, "portfolio-kicker")
        self.assertContains(response, "Ketua")

    def test_kicker_tidak_dirender_kalau_job_title_kosong(self):
        Experience.objects.all().delete()
        Experience.objects.create(title="Tanpa Jabatan", summary="x")
        response = self.client.get(reverse("main:show_experience"))
        self.assertNotContains(response, "portfolio-kicker")

    def test_pesan_kosong_kalau_belum_ada_experience(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))
        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")


class DetailViewTests(TestCase):
    def setUp(self):
        self.exp = Experience.objects.create(
            title="SELARAS 5.0", job_title="Wakil Ketua",
            content="Baris pertama.\nBaris kedua.",
            thumbnail="/static/css/img/selaras.jpg")
        self.pro = Project.objects.create(
            title="SINTAKS", description="Deskripsi sintaks",
            content="Isi blog panjang.", thumbnail="/static/css/img/sintaks.jpg")

    def test_experience_detail_ok(self):
        r = self.client.get(reverse("main:show_experience_detail", args=[self.exp.title]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "experience_detail.html")
        self.assertEqual(r.context["experience"].pk, self.exp.pk)
        self.assertContains(r, "<p>Baris pertama.<br>Baris kedua.</p>")
        for k in ["detail-section", "detail-hero", "detail-body", "detail-back"]:
            self.assertContains(r, k)

    def test_experience_detail_404(self):
        self.assertEqual(self.client.get("/experience/X/").status_code, 404)

    def test_experience_detail_fallback_dan_guard(self):
        Experience.objects.filter(pk=self.exp.pk).update(content=None, job_title=None, thumbnail=None)
        r = self.client.get(reverse("main:show_experience_detail", args=[self.exp.title]))
        self.assertContains(r, "Belum ada deskripsi untuk pengalaman ini.")
        self.assertNotContains(r, "portfolio-kicker")
        self.assertNotContains(r, "detail-hero")

    def test_project_detail_ok(self):
        r = self.client.get(reverse("main:show_project_detail", args=[self.pro.title]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "project_detail.html")
        self.assertEqual(r.context["project"].pk, self.pro.pk)
        self.assertContains(r, "Isi blog panjang.")

    def test_project_detail_404(self):
        self.assertEqual(self.client.get("/project/X/").status_code, 404)

    def test_project_detail_fallback(self):
        Project.objects.filter(pk=self.pro.pk).update(content=None)
        r = self.client.get(reverse("main:show_project_detail", args=[self.pro.title]))
        self.assertContains(r, "Deskripsi sintaks")
        Project.objects.filter(pk=self.pro.pk).update(description=None)
        r = self.client.get(reverse("main:show_project_detail", args=[self.pro.title]))
        self.assertContains(r, "Belum ada deskripsi untuk proyek ini.")

    def test_judul_spasi_dan_ampersand(self):
        p = Project.objects.create(title="A & B")
        r = self.client.get(reverse("main:show_project_detail", args=[p.title]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "A &amp; B")


class FixtureTests(TestCase):
    fixtures = ["initial_data.json"]

    def test_jumlah_dan_title_unik(self):
        self.assertEqual(Experience.objects.count(), 5)
        self.assertEqual(Project.objects.count(), 3)
        for m in [Experience, Project]:
            j = list(m.objects.values_list("title", flat=True))
            self.assertEqual(len(j), len(set(j)))

    def test_semua_detail_bisa_dibuka(self):
        for e in Experience.objects.all():
            u = reverse("main:show_experience_detail", args=[e.title])
            self.assertEqual(self.client.get(u).status_code, 200, u)
        for p in Project.objects.all():
            u = reverse("main:show_project_detail", args=[p.title])
            self.assertEqual(self.client.get(u).status_code, 200, u)
