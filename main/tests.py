"""
Test untuk aplikasi main.

Cakupan:
1. Model     -> Experience (__str__, is_ongoing, PK UUID, default category)
                Project    -> __str__, PK integer, field opsional
2. Routing   -> reverse() semua nama URL, termasuk encoding judul
3. View      -> status code, template, isi context, penanganan 404
4. Hapus     -> hanya POST yang menghapus, GET cuma redirect, 404 kalau pk tidak ada
5. JSON API  -> /api/projects/ & /api/experiences/ beserta filter ?title=
6. Template  -> link kartu ke halaman detail, guard kondisional, teks fallback
7. Fixture   -> initial_data.json bisa dimuat dan semua datanya bisa dibuka
8. Projects  -> /projects/ (publik, read-only) + hasil deserialize JSON & ?title=
                /projects/manage/ (tambah & hapus) & /projects/manage/add/
9. Experience-> /experience/ (publik, read-only)
                /experience/manage/ (tambah & hapus) & /experience/manage/add/
10. Navigasi -> navbar tanpa link Projects, dan `manage` tidak tertangkap
                sebagai <str:title>

Jalankan: python manage.py test
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Project

# UUID tetap untuk menguji rute /experience/<uuid:...>/delete/.
UUID_TEST = "3f1a4c6e-0000-4000-8000-000000000000"


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

    def test_tech_stack_dan_project_url_opsional(self):
        project = Project.objects.create(title="SINTAKS")
        project.refresh_from_db()
        self.assertIsNone(project.tech_stack)
        self.assertIsNone(project.project_url)

    def test_project_image_url_mengembalikan_thumbnail(self):
        project = Project.objects.create(
            title="SINTAKS", thumbnail="/static/css/img/daftar_sintaks.jpg"
        )
        self.assertEqual(project.project_image_url, "/static/css/img/daftar_sintaks.jpg")

    def test_project_image_url_none_kalau_thumbnail_kosong(self):
        self.assertIsNone(Project.objects.create(title="SINTAKS").project_image_url)


class UrlRoutingTests(TestCase):
    def test_reverse_semua_url(self):
        kasus = [
            ("main:show_main", [], "/"),
            ("main:show_experience", [], "/experience/"),
            ("main:show_experience_detail", ["SELARAS 5.0"], "/experience/SELARAS%205.0/"),
            ("main:show_project_detail", ["SINTAKS"], "/projects/SINTAKS/"),
            ("main:show_project_detail", ["Ini ikan apa?"], "/projects/Ini%20ikan%20apa%3F/"),
            ("main:show_project_detail", ["UI/UX Redesign"], "/projects/UI/UX%20Redesign/"),
            ("main:create_experience", [], "/experience/manage/add/"),
            ("main:show_projects", [], "/projects/"),
            ("main:create_project", [], "/projects/manage/add/"),
            ("main:manage_experience", [], "/experience/manage/"),
            ("main:manage_projects", [], "/projects/manage/"),
            ("main:delete_experience", [UUID_TEST], f"/experience/manage/{UUID_TEST}/delete/"),
            ("main:delete_project", [7], "/projects/manage/7/delete/"),
            ("main:get_projects_json", [], "/api/projects/"),
            ("main:get_experiences_json", [], "/api/experiences/"),
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
        self.assertContains(response, "/projects/SINTAKS/")

    def test_project_tanpa_thumbnail_tidak_menambah_tag_img(self):
        sebelum = self.client.get(reverse("main:show_main")).content.decode().count("<img")
        Project.objects.create(title="Tanpa Gambar")
        sesudah = self.client.get(reverse("main:show_main")).content.decode().count("<img")
        self.assertEqual(sesudah, sebelum)

    def test_pesan_kosong_kalau_belum_ada_project(self):
        Project.objects.all().delete()
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(response, "Belum ada proyek untuk ditampilkan.")


class ExperienceDataMixin:
    """Data contoh untuk test halaman Experience (publik & manage)."""

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


class ShowExperienceViewTests(ExperienceDataMixin, TestCase):
    """/experience/ -> halaman publik (read-only) bergaya carousel."""

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

    def test_tidak_ada_tombol_tambah_atau_hapus(self):
        """Halaman publik hanya menampilkan; aksinya ada di /experience/manage/."""
        response = self.client.get(reverse("main:show_experience"))
        self.assertNotContains(response, reverse("main:create_experience"))
        self.assertNotContains(response, "Tambah Experience")
        self.assertNotContains(
            response, reverse("main:delete_experience", args=[self.baru.pk])
        )


class ManageExperienceViewTests(ExperienceDataMixin, TestCase):
    """/experience/manage/ -> daftar + tombol tambah & hapus."""

    def test_status_dan_template(self):
        response = self.client.get(reverse("main:manage_experience"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_manage.html")

    def test_urutan_terbaru_dulu(self):
        response = self.client.get(reverse("main:manage_experience"))
        judul = [e.title for e in response.context["experience_list"]]
        self.assertEqual(judul, ["Pengalaman Baru", "Pengalaman Lama"])

    def test_ada_tombol_tambah_experience_ke_halaman_form(self):
        response = self.client.get(reverse("main:manage_experience"))
        self.assertContains(response, reverse("main:create_experience"))
        self.assertContains(response, "Tambah Experience")

    def test_setiap_kartu_punya_modal_hapus_berbasis_pk(self):
        response = self.client.get(reverse("main:manage_experience"))
        self.assertContains(
            response, reverse("main:delete_experience", args=[self.baru.pk])
        )
        self.assertContains(
            response, reverse("main:delete_experience", args=[self.lama.pk])
        )

    def test_tombol_hapus_berada_di_luar_link_kartu(self):
        """Kalau tombol ada di dalam <a>, klik hapus ikut menavigasi ke detail."""
        response = self.client.get(reverse("main:manage_experience")).content.decode()
        penutup_link = response.index("</a>", response.index("project-card-link"))
        posisi_modal = response.index(reverse("main:delete_experience", args=[self.baru.pk]))
        self.assertGreater(posisi_modal, penutup_link)


class DetailViewTests(TestCase):
    def setUp(self):
        # Migrasi 0006 juga men-seed data fixture ke DB test -> bersihkan dulu
        Experience.objects.all().delete()
        Project.objects.all().delete()
        self.exp = Experience.objects.create(
            title="SELARAS 5.0", job_title="Wakil Ketua",
            content="Baris pertama.\nBaris kedua.",
            thumbnail="/static/css/img/selaras.jpg")
        self.pro = Project.objects.create(
            title="SINTAKS", description="Deskripsi sintaks",
            content="Isi blog panjang.", thumbnail="/static/css/img/sintaks.jpg",
            project_url="https://example.com/demo-proyek")

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

    def test_project_detail_menampilkan_tombol_lihat_project(self):
        r = self.client.get(reverse("main:show_project_detail", args=[self.pro.title]))
        self.assertContains(r, "Lihat Project")
        self.assertContains(r, "https://example.com/demo-proyek")

    def test_project_detail_tanpa_project_url_tidak_ada_tombol(self):
        Project.objects.filter(pk=self.pro.pk).update(project_url=None)
        r = self.client.get(reverse("main:show_project_detail", args=[self.pro.title]))
        self.assertNotContains(r, "Lihat Project")

    def test_project_detail_404(self):
        self.assertEqual(self.client.get("/projects/X/").status_code, 404)

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

    def test_project_detail_judul_berisi_slash(self):
        """`<path:title>` membuat judul "UI/UX Redesign" bisa dibuka."""
        p = Project.objects.create(title="UI/UX Redesign", content="Isi blog.")
        r = self.client.get(reverse("main:show_project_detail", args=[p.title]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Isi blog.")

    def test_experience_detail_judul_berisi_slash(self):
        e = Experience.objects.create(title="Kerja/Magang", summary="Ringkasan")
        r = self.client.get(reverse("main:show_experience_detail", args=[e.title]))
        self.assertEqual(r.status_code, 200)


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


class DeleteViewTests(TestCase):
    """delete_project & delete_experience: hanya POST yang menghapus.

    URL-nya memakai primary key, bukan judul. Karena itu test di sini
    sekaligus mengunci dua perbaikan: judul berisi "/" tidak lagi membuat
    `{% url %}` gagal (500), dan judul duplikat tidak lagi melempar
    `MultipleObjectsReturned`.
    """

    def setUp(self):
        Experience.objects.all().delete()
        Project.objects.all().delete()
        self.project = Project.objects.create(title="UI/UX Redesign")
        self.experience = Experience.objects.create(title="SELARAS 5.0")

    def test_delete_project_post_menghapus_dan_redirect(self):
        url = reverse("main:delete_project", args=[self.project.pk])
        r = self.client.post(url, follow=True)
        self.assertRedirects(r, reverse("main:manage_projects"))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertContains(r, "Project berhasil dihapus!")

    def test_delete_project_get_tidak_menghapus(self):
        url = reverse("main:delete_project", args=[self.project.pk])
        r = self.client.get(url, follow=True)
        self.assertRedirects(r, reverse("main:manage_projects"))
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_delete_project_pk_tidak_ada_404(self):
        self.assertEqual(self.client.post("/projects/manage/999999/delete/").status_code, 404)

    def test_delete_project_pk_bukan_angka_404(self):
        self.assertEqual(self.client.post("/projects/manage/X/delete/").status_code, 404)

    def test_delete_project_judul_berisi_slash_tetap_bisa_dihapus(self):
        """Judul "UI/UX Redesign" dulu bikin `{% url %}` gagal karena `/`."""
        self.assertIn("/", self.project.title)
        self.client.post(reverse("main:delete_project", args=[self.project.pk]))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_delete_project_judul_duplikat_tidak_melempar_multiple_objects(self):
        kembar = Project.objects.create(title="UI/UX Redesign")
        self.client.post(reverse("main:delete_project", args=[kembar.pk]))
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
        self.assertFalse(Project.objects.filter(pk=kembar.pk).exists())

    def test_delete_experience_post_menghapus_dan_redirect(self):
        url = reverse("main:delete_experience", args=[self.experience.pk])
        r = self.client.post(url, follow=True)
        self.assertRedirects(r, reverse("main:manage_experience"))
        self.assertFalse(Experience.objects.filter(pk=self.experience.pk).exists())
        self.assertContains(r, "Experience berhasil dihapus!")

    def test_delete_experience_get_tidak_menghapus(self):
        url = reverse("main:delete_experience", args=[self.experience.pk])
        r = self.client.get(url, follow=True)
        self.assertRedirects(r, reverse("main:manage_experience"))
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())

    def test_delete_experience_pk_tidak_ada_404(self):
        url = reverse("main:delete_experience", args=[UUID_TEST])
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_delete_experience_bukan_uuid_404(self):
        """`<uuid:...>` menolak "X", jadi rute ini tidak menabrak rute lain."""
        self.assertEqual(self.client.post("/experience/manage/X/delete/").status_code, 404)


class ProjectDataMixin:
    """Data contoh untuk test halaman Projects (publik & manage)."""

    def setUp(self):
        Project.objects.all().delete()
        self.sintaks = Project.objects.create(
            title="SINTAKS",
            description="Daftar sintaks",
            thumbnail="/static/css/img/daftar_sintaks.jpg",
            tech_stack="Django, PostgreSQL",
            project_url="https://github.com/christiano-h/sintaks",
        )
        Project.objects.create(title="SCUBAAAAA")


class ShowProjectsViewTests(ProjectDataMixin, TestCase):
    """/projects/ -> halaman publik (read-only) bergaya carousel + ?title=."""

    def test_status_dan_template(self):
        r = self.client.get(reverse("main:show_projects"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "project.html")

    def test_menampilkan_semua_project_tanpa_filter(self):
        r = self.client.get(reverse("main:show_projects"))
        self.assertEqual(len(r.context["project_list"]), 2)
        self.assertEqual(r.context["title_query"], "")
        self.assertContains(r, "SINTAKS")
        self.assertContains(r, "SCUBAAAAA")

    def test_search_title_memfilter_abaikan_besar_kecil_huruf(self):
        r = self.client.get(reverse("main:show_projects"), {"title": "sint"})
        self.assertEqual([p.title for p in r.context["project_list"]], ["SINTAKS"])
        self.assertEqual(r.context["title_query"], "sint")
        self.assertNotContains(r, "SCUBAAAAA")

    def test_search_tanpa_hasil_menampilkan_pesan_khusus(self):
        r = self.client.get(reverse("main:show_projects"), {"title": "zzz"})
        self.assertContains(r, "Tidak ada proyek dengan nama tersebut.")

    def test_tanpa_data_dan_tanpa_search_menampilkan_pesan_lain(self):
        Project.objects.all().delete()
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, "Belum ada proyek yang ditambahkan.")

    def test_kartu_menampilkan_thumbnail_dan_tech_stack(self):
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, "/static/css/img/daftar_sintaks.jpg")
        self.assertContains(r, "Django, PostgreSQL")

    def test_kartu_daftar_tidak_menautkan_langsung_ke_url_eksternal(self):
        """Tautan luar hanya di halaman detail, supaya alurnya dua langkah."""
        r = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(r, "https://github.com/christiano-h/sintaks")

    def test_tanpa_thumbnail_tidak_menambah_tag_img(self):
        sebelum = self.client.get(reverse("main:show_projects")).content.decode().count("<img")
        Project.objects.create(title="Tanpa Gambar")
        sesudah = self.client.get(reverse("main:show_projects")).content.decode().count("<img")
        self.assertEqual(sesudah, sebelum)

    def test_tanpa_tech_stack_dan_deskripsi_tidak_menulis_none(self):
        Project.objects.all().delete()
        Project.objects.create(title="Kosong")
        r = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(r, "None")
        self.assertNotContains(r, 'class="experience-category"')
        self.assertNotContains(r, 'class="experience-description"')

    def test_ada_form_pencarian_judul(self):
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, "project-search__input")
        self.assertContains(r, 'name="title"')

    def test_tidak_ada_tombol_tambah_atau_hapus(self):
        """Halaman publik hanya menampilkan; aksinya ada di /projects/manage/."""
        r = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(r, reverse("main:create_project"))
        self.assertNotContains(r, "Tambah Proyek")
        self.assertNotContains(r, reverse("main:delete_project", args=[self.sintaks.pk]))


    def test_hasil_deserialize_json_berisi_objek_project(self):
        """`show_projects` mengirim objek Project hasil deserialize, bukan QuerySet."""
        r = self.client.get(reverse("main:show_projects"))
        daftar = r.context["project_list"]
        self.assertIsInstance(daftar, list)
        self.assertEqual(len(daftar), 2)
        for p in daftar:
            self.assertIsInstance(p, Project)
            # Instance baru hasil deserialize, bukan hasil query DB.
            self.assertTrue(p._state.adding)

    def test_deserialize_tetap_hormati_filter_title(self):
        r = self.client.get(reverse("main:show_projects"), {"title": "sint"})
        self.assertEqual([p.title for p in r.context["project_list"]], ["SINTAKS"])


class ManageProjectsViewTests(ProjectDataMixin, TestCase):
    """/projects/manage/ -> daftar + tombol tambah & hapus."""

    def test_status_dan_template(self):
        r = self.client.get(reverse("main:manage_projects"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "project_manage.html")

    def test_ada_tombol_tambah_project_ke_halaman_form(self):
        r = self.client.get(reverse("main:manage_projects"))
        self.assertContains(r, reverse("main:create_project"))
        self.assertContains(r, "Tambah Proyek")

    def test_setiap_kartu_punya_modal_hapus_berbasis_pk(self):
        r = self.client.get(reverse("main:manage_projects"))
        self.assertContains(r, reverse("main:delete_project", args=[self.sintaks.pk]))

    def test_tombol_hapus_berada_di_luar_link_kartu(self):
        """Kalau tombol ada di dalam <a>, klik hapus ikut menavigasi ke detail."""
        r = self.client.get(reverse("main:manage_projects")).content.decode()
        penutup_link = r.index("</a>", r.index("project-card-link"))
        posisi_modal = r.index(reverse("main:delete_project", args=[self.sintaks.pk]))
        self.assertGreater(posisi_modal, penutup_link)

    def test_search_title_juga_berlaku_di_halaman_manage(self):
        r = self.client.get(reverse("main:manage_projects"), {"title": "sint"})
        self.assertEqual([p.title for p in r.context["project_list"]], ["SINTAKS"])
        self.assertEqual(r.context["title_query"], "sint")

    def test_pakai_jalur_deserialize_json_yang_sama(self):
        """Manage memakai helper `_projects_from_json` yang sama dengan publik."""
        r = self.client.get(reverse("main:manage_projects"))
        daftar = r.context["project_list"]
        self.assertIsInstance(daftar, list)
        for p in daftar:
            self.assertIsInstance(p, Project)
            self.assertTrue(p._state.adding)

    def test_tidak_menampilkan_project_yang_tidak_cocok(self):
        r = self.client.get(reverse("main:manage_projects"), {"title": "zzz"})
        self.assertContains(r, "Tidak ada proyek dengan nama tersebut.")


class CreateProjectViewTests(TestCase):
    """/projects/add/ -> ProjectForm, hanya POST valid yang menyimpan."""

    def setUp(self):
        Project.objects.all().delete()

    def test_get_menampilkan_form(self):
        r = self.client.get(reverse("main:create_project"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "project_form.html")
        self.assertIn("form", r.context)

    def test_post_valid_menyimpan_dan_redirect_ke_daftar(self):
        r = self.client.post(
            reverse("main:create_project"),
            {
                "title": "Proyek Baru",
                "tech_stack": "Django",
                "thumbnail": "",
                "project_url": "https://example.com",
                "description": "Deskripsi",
                "content": "Konten",
            },
            follow=True,
        )
        self.assertRedirects(r, reverse("main:manage_projects"))
        self.assertTrue(Project.objects.filter(title="Proyek Baru").exists())
        self.assertContains(r, "Project baru berhasil ditambahkan!")

    def test_post_title_kosong_tidak_menyimpan(self):
        r = self.client.post(reverse("main:create_project"), {"title": ""})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Project.objects.exists())


class JsonApiViewTests(TestCase):
    """/api/projects/ & /api/experiences/ -> JSON, dengan filter ?title=."""

    def setUp(self):
        Experience.objects.all().delete()
        Project.objects.all().delete()
        Project.objects.create(title="SINTAKS")
        Project.objects.create(title="SCUBAAAAA")

    def test_projects_json_mengembalikan_seluruh_data(self):
        r = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/json")
        self.assertEqual(len(r.json()), 2)

    def test_projects_json_filter_title_abaikan_besar_kecil_huruf(self):
        r = self.client.get(reverse("main:get_projects_json"), {"title": "sintak"})
        self.assertEqual([d["fields"]["title"] for d in r.json()], ["SINTAKS"])

    def test_experiences_json_filter_title(self):
        Experience.objects.create(title="SELARAS 5.0")
        Experience.objects.create(title="RISTEK")
        r = self.client.get(reverse("main:get_experiences_json"), {"title": "ristek"})
        self.assertEqual([d["fields"]["title"] for d in r.json()], ["RISTEK"])


class CreateExperienceViewTests(TestCase):
    """/experience/add/ -> ExperienceForm, hanya POST valid yang menyimpan."""

    def setUp(self):
        Experience.objects.all().delete()

    def test_get_menampilkan_form(self):
        r = self.client.get(reverse("main:create_experience"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "experience_form.html")
        self.assertIn("form", r.context)

    def test_post_valid_menyimpan_dan_redirect_ke_daftar(self):
        r = self.client.post(
            reverse("main:create_experience"),
            {
                "title": "RISTEK",
                "job_title": "Anggota",
                "category": "full-time",
                "thumbnail": "",
                "summary": "Ringkasan",
                "content": "Konten",
                "ended_at": "",
            },
            follow=True,
        )
        self.assertRedirects(r, reverse("main:manage_experience"))
        self.assertTrue(Experience.objects.filter(title="RISTEK").exists())
        self.assertContains(r, "Experience baru berhasil ditambahkan!")

    def test_post_title_kosong_tidak_menyimpan(self):
        r = self.client.post(reverse("main:create_experience"), {"title": ""})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Experience.objects.exists())


class NavigasiDanRuteManageTests(TestCase):
    """Navbar dengan link Profile/Project/Experience + rute `manage` tidak menabrak `<str:title>`."""

    def setUp(self):
        Experience.objects.all().delete()
        Project.objects.all().delete()

    def test_navbar_punya_profile_project_dan_experience(self):
        for nama in ["main:show_main", "main:show_experience", "main:show_projects"]:
            with self.subTest(halaman=nama):
                r = self.client.get(reverse(nama))
                self.assertContains(r, reverse("main:show_projects"))
                self.assertContains(r, reverse("main:show_experience"))

    def test_manage_projects_tidak_404(self):
        """Sebelum perbaikan urutan urlpatterns, "manage" tertangkap `<str:title>`."""
        self.assertEqual(self.client.get("/projects/manage/").status_code, 200)

    def test_manage_experience_tidak_tertangkap_sebagai_title(self):
        self.assertEqual(self.client.get("/experience/manage/").status_code, 200)
        self.assertTemplateUsed(
            self.client.get("/experience/manage/"), "experience_manage.html"
        )

    def test_halaman_publik_tidak_pakai_body_class_manage_page(self):
        for nama in ["main:show_experience", "main:show_projects"]:
            with self.subTest(halaman=nama):
                r = self.client.get(reverse(nama))
                self.assertNotContains(r, "manage-page")

