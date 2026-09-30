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
8. Projects  -> /projects/ (publik, read-only) dirender JS dari endpoint JSON
                /projects/manage/ (tambah & hapus) & /projects/manage/add/
9. Experience-> /experience/ (publik, read-only)
                /experience/manage/ (tambah & hapus) & /experience/manage/add/
10. Navigasi -> navbar tanpa link Projects, dan `manage` tidak tertangkap
                sebagai <str:title>
11. Autentikasi -> register/login/logout, cookie `last_login`, redirect ke
                /login/?next=... untuk pengunjung tanpa login
12. Otorisasi -> matriks 4 peran: anonim (redirect), pengguna biasa (hanya
                baca + star), Editor (boleh ubah, tidak boleh tambah/hapus),
                Owner/superuser (semua)
13. Star      -> toggle POST, satu star per pengguna, dan hak aksesnya
14. API aman  -> JSON tidak membocorkan data user/password

Jalankan: python manage.py test
"""

from datetime import timedelta

from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Project

# UUID tetap untuk menguji rute /experience/<uuid:...>/delete/.
UUID_TEST = "3f1a4c6e-0000-4000-8000-000000000000"

# Sentinela di templates/project.html: kartu dibangun JS, jadi URL per-project
# dibuat dari template URL ber-sentinel ini lalu sentinelanya diganti pk/judul asli
# yang datang dari endpoint JSON. Nilainya harus sama dengan template tersebut.
PROJECT_ID_SENTINEL = 999999999
PROJECT_TITLE_SENTINEL = "PROJECT_TITLE_SENTINEL"

# Permission pembentuk peran "Editor": boleh MENGUBAH, tidak boleh menambah
# (`add_*`) atau menghapus (`delete_*`).
PERMISSION_EDITOR = ["change_project", "change_experience"]


def buat_grup_editor():
    """Buat/ambil grup "Editor" berisi PERMISSION_EDITOR untuk app main.

    Di environment nyata grup ini dibuat manual lewat Django Admin; test membuat
    grupnya sendiri supaya hasilnya tidak bergantung pada isi DB.
    """
    grup, _ = Group.objects.get_or_create(name="Editor")
    grup.permissions.set(
        Permission.objects.filter(
            content_type__app_label="main", codename__in=PERMISSION_EDITOR
        )
    )
    return grup


def buat_user_editor(username="editor"):
    """Pengguna biasa yang dinaikkan jadi Editor lewat grup "Editor"."""
    user = User.objects.create_user(username=username, password="rahasia-editor")
    user.groups.add(buat_grup_editor())
    return user


class AuthenticatedTestCase(TestCase):
    """Base untuk test halaman manage/CRUD yang kini dilindungi login & permission.

    Login sebagai superuser (= pemilik portofolio) supaya test lama tetap fokus
    menguji perilaku halaman. Matriks hak aksesnya diuji terpisah di
    ManageAccessTests dan EditorAccessTests.
    """

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="rahasia-owner"
        )
        self.client.force_login(self.admin)


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
            ("main:update_experience", [UUID_TEST], f"/experience/manage/{UUID_TEST}/update/"),
            ("main:update_project", [7], "/projects/manage/7/update/"),
            ("main:get_projects_json", [], "/api/projects/"),
            ("main:get_experiences_json", [], "/api/experiences/"),
            ("main:register", [], "/register/"),
            ("main:login", [], "/login/"),
            ("main:logout", [], "/logout/"),
            ("main:toggle_star", [7], "/projects/7/star/"),
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
        self.assertEqual(response.context["name"], "ANO")
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
        super().setUp()
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


class ManageExperienceViewTests(ExperienceDataMixin, AuthenticatedTestCase):
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


class DeleteViewTests(AuthenticatedTestCase):
    """delete_project & delete_experience: hanya POST yang menghapus.

    URL-nya memakai primary key, bukan judul. Karena itu test di sini
    sekaligus mengunci dua perbaikan: judul berisi "/" tidak lagi membuat
    `{% url %}` gagal (500), dan judul duplikat tidak lagi melempar
    `MultipleObjectsReturned`.
    """

    def setUp(self):
        super().setUp()
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
        super().setUp()
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
        """Kartu dirender JS, jadi daftarnya datang dari endpoint JSON."""
        r = self.client.get(reverse("main:show_projects"))
        self.assertEqual(r.context["title_query"], "")
        data = self.client.get(reverse("main:get_projects_json")).json()
        self.assertEqual(
            [d["fields"]["title"] for d in data], ["SINTAKS", "SCUBAAAAA"]
        )

    def test_search_title_memfilter_abaikan_besar_kecil_huruf(self):
        r = self.client.get(reverse("main:show_projects"), {"title": "sint"})
        self.assertEqual(r.context["title_query"], "sint")
        data = self.client.get(reverse("main:get_projects_json"), {"title": "sint"}).json()
        self.assertEqual([d["fields"]["title"] for d in data], ["SINTAKS"])

    def test_search_tanpa_hasil_menampilkan_pesan_khusus(self):
        r = self.client.get(reverse("main:show_projects"), {"title": "zzz"})
        self.assertContains(r, "Tidak ada proyek dengan nama tersebut.")

    def test_tanpa_data_dan_tanpa_search_menampilkan_pesan_lain(self):
        Project.objects.all().delete()
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, "Belum ada proyek yang ditambahkan.")

    def test_kartu_menampilkan_thumbnail_dan_tech_stack(self):
        """Data kartu datang dari endpoint JSON, lalu dirender kartu JS."""
        data = self.client.get(reverse("main:get_projects_json")).json()
        sintaks = next(d for d in data if d["fields"]["title"] == "SINTAKS")
        self.assertEqual(
            sintaks["fields"]["project_image_url"], "/static/css/img/daftar_sintaks.jpg"
        )
        self.assertEqual(sintaks["fields"]["tech_stack"], "Django, PostgreSQL")
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, "portfolio-img")
        self.assertContains(r, "portfolio-kicker")

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


    def test_halaman_publik_menyiapkan_wadah_dan_endpoint_ajax(self):
        """Halaman publik kini kerangka AJAX: wadah #grid + endpoint JSON.

        Data tidak lagi dikirim lewat context (`project_list`), melainkan di-fetch
        `project.html` dari `/api/projects/`.
        """
        r = self.client.get(reverse("main:show_projects"))
        self.assertNotIn("project_list", r.context)
        self.assertContains(r, reverse("main:get_projects_json"))
        self.assertContains(r, 'id="grid"')

    def test_kartu_builder_pakai_markup_komponen_project_card(self):
        """Kartu JS wajib memakai class yang sama dengan components/project_card.html,
        supaya outline, glare, hover, dan carousel HP (`.project-card-outline`) tetap
        berperilaku seperti versi server-rendered."""
        r = self.client.get(reverse("main:show_projects"))
        for kelas in [
            "project-card-outline",
            "project-card-link",
            "portfolio-card project-card",
            "portfolio-img",
            "portfolio-title",
            "portfolio-kicker",
            "portfolio-desc",
        ]:
            with self.subTest(kelas=kelas):
                self.assertContains(r, kelas)


class ManageProjectsViewTests(ProjectDataMixin, AuthenticatedTestCase):
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
        """Manage memakai helper `_projects_from_json` (jalur endpoint JSON)."""
        r = self.client.get(reverse("main:manage_projects"))
        daftar = r.context["project_list"]
        self.assertIsInstance(daftar, list)
        for p in daftar:
            self.assertIsInstance(p, Project)
            self.assertTrue(p._state.adding)

    def test_tidak_menampilkan_project_yang_tidak_cocok(self):
        r = self.client.get(reverse("main:manage_projects"), {"title": "zzz"})
        self.assertContains(r, "Tidak ada proyek dengan nama tersebut.")


class CreateProjectViewTests(AuthenticatedTestCase):
    """/projects/add/ -> ProjectForm, hanya POST valid yang menyimpan."""

    def setUp(self):
        super().setUp()
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


class JsonApiNoLeakTests(TestCase):
    """JSON API tidak membocorkan identitas user (poin 14 docstring modul).

    `/api/experiences/` masih memakai serializer Django (M2M `starred_by` dikirim
    sebagai natural key / username), sedangkan `/api/projects/` memakai payload
    custom: username-nya ada di `starred_by_names`, bukan pk user.
    """

    def setUp(self):
        Experience.objects.all().delete()
        Project.objects.all().delete()
        self.user = User.objects.create_user(
            "penggemar", email="penggemar@example.com", password="rahasia-user"
        )
        self.project = Project.objects.create(title="SINTAKS")
        self.experience = Experience.objects.create(title="RISTEK")
        self.project.starred_by.add(self.user)
        self.experience.starred_by.add(self.user)

    def _get_json(self, nama):
        r = self.client.get(reverse(f"main:{nama}"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/json")
        return r

    def test_starred_by_berisi_username_bukan_pk_user(self):
        data_exp = self._get_json("get_experiences_json").json()
        self.assertEqual(data_exp[0]["fields"]["starred_by"], [["penggemar"]])

        data_proj = self._get_json("get_projects_json").json()
        self.assertEqual(data_proj[0]["fields"]["starred_by_names"], "penggemar")
        # Payload project tidak mengirim M2M mentah (yang bisa membawa pk user).
        self.assertNotIn("starred_by\":", self._get_json("get_projects_json").content.decode())

    def test_payload_tidak_memuat_kolom_pribadi_user(self):
        for nama in ["get_projects_json", "get_experiences_json"]:
            with self.subTest(endpoint=nama):
                teks = self._get_json(nama).content.decode()
                for terlarang in ["password", "email", "last_login", "is_superuser"]:
                    self.assertNotIn(terlarang, teks)

    def test_starred_by_kosong_tetap_list_kosong(self):
        self.project.starred_by.clear()
        data = self._get_json("get_projects_json").json()
        self.assertEqual(data[0]["fields"]["starred_by_names"], "")


class CreateExperienceViewTests(AuthenticatedTestCase):
    """/experience/add/ -> ExperienceForm, hanya POST valid yang menyimpan."""

    def setUp(self):
        super().setUp()
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


class NavigasiDanRuteManageTests(AuthenticatedTestCase):
    """Navbar dengan link Profile/Project/Experience + rute `manage` tidak menabrak `<str:title>`."""

    def setUp(self):
        super().setUp()
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



class UpdateProjectViewTests(AuthenticatedTestCase):
    """Halaman update /projects/manage/<pk>/update/.

    Memakai primary key seperti delete_project, jadi judul bebas diubah dan
    tidak terpengaruh judul kembar.
    """

    def setUp(self):
        super().setUp()
        Project.objects.all().delete()
        self.project = Project.objects.create(
            title="SINTAKS", description="Deskripsi lama", tech_stack="Django",
            thumbnail="/static/css/img/sintaks.jpg",
            project_url="https://example.com/lama")

    def test_get_menampilkan_data_lama(self):
        r = self.client.get(reverse("main:update_project", args=[self.project.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "project_update.html")
        self.assertContains(r, "value=\"SINTAKS\"")
        self.assertContains(r, "Deskripsi lama")

    def test_post_valid_mengubah_record_yang_sama(self):
        r = self.client.post(
            reverse("main:update_project", args=[self.project.pk]),
            {"title": "SINTAKS BARU", "tech_stack": "Django, PostgreSQL",
             "thumbnail": "https://example.com/gambar.jpg",
             "project_url": "https://example.com/baru",
             "description": "Deskripsi baru", "content": "Isi baru"},
            follow=True)
        self.assertRedirects(r, reverse("main:manage_projects"))
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().pk, self.project.pk)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "SINTAKS BARU")
        self.assertEqual(self.project.description, "Deskripsi baru")
        self.assertContains(r, "Project berhasil diperbarui!")

    def test_post_tidak_valid_menampilkan_error_dan_mempertahankan_input(self):
        r = self.client.post(
            reverse("main:update_project", args=[self.project.pk]),
            {"title": "", "description": "masih ini"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors)
        self.assertContains(r, "masih ini")
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "SINTAKS")

    def test_tombol_batal_menuju_manage(self):
        r = self.client.get(reverse("main:update_project", args=[self.project.pk]))
        self.assertContains(r, reverse("main:manage_projects"))

    def test_update_boleh_mengubah_judul(self):
        url = reverse("main:update_project", args=[self.project.pk])
        self.client.post(url, {"title": "Judul/Baru", "description": "x"})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Judul/Baru")

    def test_update_tetap_bekerja_saat_ada_judul_kembar(self):
        kembar = Project.objects.create(title="SINTAKS")
        self.client.post(
            reverse("main:update_project", args=[kembar.pk]),
            {"title": "SINTAKS", "description": "yang diubah"})
        kembar.refresh_from_db()
        self.assertEqual(kembar.description, "yang diubah")
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, "Deskripsi lama")

    def test_pk_tidak_ada_404(self):
        r = self.client.get(reverse("main:update_project", args=[999999]))
        self.assertEqual(r.status_code, 404)

    def test_pk_bukan_angka_404(self):
        self.assertEqual(self.client.get("/projects/manage/X/update/").status_code, 404)

    def test_kartu_manage_menuju_form_update(self):
        r = self.client.get(reverse("main:manage_projects"))
        self.assertContains(r, reverse("main:update_project", args=[self.project.pk]))

    def test_kartu_publik_tetap_menuju_detail(self):
        """Kartu JS menaut ke halaman detail lewat template URL ber-sentinel judul."""
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(
            r, reverse("main:show_project_detail", args=[PROJECT_TITLE_SENTINEL])
        )
        self.assertContains(r, "project-card-link")
        self.assertNotContains(r, reverse("main:update_project", args=[self.project.pk]))

    def test_data_baru_tampil_di_daftar_dan_detail(self):
        self.client.post(
            reverse("main:update_project", args=[self.project.pk]),
            {"title": "TERBARU", "description": "deskripsi anyar"})
        data = self.client.get(reverse("main:get_projects_json")).json()
        self.assertEqual([d["fields"]["title"] for d in data], ["TERBARU"])
        self.assertContains(
            self.client.get(reverse("main:show_project_detail", args=["TERBARU"])),
            "deskripsi anyar")


class UpdateExperienceViewTests(AuthenticatedTestCase):
    """Halaman update /experience/manage/<pk>/update/ (pk UUID, seperti delete)."""

    def setUp(self):
        super().setUp()
        Experience.objects.all().delete()
        self.experience = Experience.objects.create(
            title="RISTEK", job_title="Anggota", summary="Ringkasan lama")

    def test_get_menampilkan_data_lama(self):
        r = self.client.get(reverse("main:update_experience", args=[self.experience.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "experience_update.html")
        self.assertContains(r, "value=\"RISTEK\"")
        self.assertContains(r, "Ringkasan lama")

    def test_post_valid_mengubah_record_yang_sama(self):
        r = self.client.post(
            reverse("main:update_experience", args=[self.experience.pk]),
            {"title": "RISTEK BARU", "job_title": "Ketua", "category": "volunteer",
             "thumbnail": "", "summary": "Ringkasan baru", "content": "", "ended_at": ""},
            follow=True)
        self.assertRedirects(r, reverse("main:manage_experience"))
        self.assertEqual(Experience.objects.count(), 1)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "RISTEK BARU")
        self.assertEqual(self.experience.job_title, "Ketua")
        self.assertContains(r, "Experience berhasil diperbarui!")

    def test_post_tidak_valid_mempertahankan_input(self):
        r = self.client.post(
            reverse("main:update_experience", args=[self.experience.pk]),
            {"title": "", "summary": "masih ini"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors)
        self.assertContains(r, "masih ini")

    def test_pk_tidak_ada_404(self):
        r = self.client.get(reverse("main:update_experience", args=[UUID_TEST]))
        self.assertEqual(r.status_code, 404)

    def test_pk_bukan_uuid_404(self):
        self.assertEqual(self.client.get("/experience/manage/X/update/").status_code, 404)

    def test_kartu_manage_menuju_form_update(self):
        r = self.client.get(reverse("main:manage_experience"))
        self.assertContains(r, reverse("main:update_experience", args=[self.experience.pk]))

    def test_kartu_publik_tetap_menuju_detail(self):
        r = self.client.get(reverse("main:show_experience"))
        self.assertContains(r, reverse("main:show_experience_detail", args=[self.experience.title]))
        self.assertNotContains(r, reverse("main:update_experience", args=[self.experience.pk]))

class ManageAccessTests(TestCase):
    """Matriks hak akses halaman manage & CRUD.

    Anonim -> 302 ke /login/?next=...
    Pengguna biasa -> 403 di semua aksi CRUD, tapi tetap boleh baca & star.
    """

    AKSI_CRUD = [
        "manage_projects",
        "manage_experience",
        "create_project",
        "create_experience",
        "delete_project",
        "delete_experience",
        "update_project",
        "update_experience",
    ]

    def setUp(self):
        super().setUp()
        Experience.objects.all().delete()
        Project.objects.all().delete()
        self.project = Project.objects.create(title="SINTAKS")
        self.experience = Experience.objects.create(title="RISTEK")

    def _url(self, nama):
        if nama in ("delete_project", "update_project"):
            return reverse(f"main:{nama}", args=[self.project.pk])
        if nama in ("delete_experience", "update_experience"):
            return reverse(f"main:{nama}", args=[self.experience.pk])
        return reverse(f"main:{nama}")

    def test_anonim_diarahkan_ke_login_beserta_next(self):
        for nama in self.AKSI_CRUD:
            with self.subTest(view=nama):
                r = self.client.get(self._url(nama))
                self.assertEqual(r.status_code, 302)
                self.assertTrue(r["Location"].startswith("/login/"), r["Location"])

    def test_anonim_tetap_bisa_membaca_halaman_publik(self):
        for nama in ["show_main", "show_projects", "show_experience"]:
            with self.subTest(view=nama):
                self.assertEqual(self.client.get(reverse(f"main:{nama}")).status_code, 200)

    def test_pengguna_biasa_ditolak_403(self):
        self.client.force_login(
            User.objects.create_user("biasa", password="rahasia-biasa")
        )
        for nama in self.AKSI_CRUD:
            with self.subTest(view=nama):
                self.assertEqual(self.client.get(self._url(nama)).status_code, 403)

    def test_pengguna_biasa_tidak_bisa_mengubah_lewat_post(self):
        self.client.force_login(
            User.objects.create_user("biasa", password="rahasia-biasa")
        )
        r = self.client.post(reverse("main:create_project"), {"title": "Curang"})
        self.assertEqual(r.status_code, 403)
        self.assertFalse(Project.objects.filter(title="Curang").exists())

    def test_pengguna_biasa_tetap_bisa_memberi_star(self):
        user = User.objects.create_user("biasa", password="rahasia-biasa")
        self.client.force_login(user)
        self.client.post(reverse("main:toggle_star", args=[self.project.pk]))
        self.assertTrue(self.project.starred_by.filter(pk=user.pk).exists())


class EditorAccessTests(TestCase):
    """Peran Editor: boleh mengubah data, tidak boleh menambah/menghapus."""

    def setUp(self):
        super().setUp()
        Experience.objects.all().delete()
        Project.objects.all().delete()
        self.project = Project.objects.create(title="SINTAKS")
        self.experience = Experience.objects.create(title="RISTEK")
        self.editor = buat_user_editor()
        self.client.force_login(self.editor)

    def test_editor_hanya_punya_permission_change(self):
        self.assertEqual(
            set(self.editor.get_all_permissions()),
            {"main.change_project", "main.change_experience"},
        )

    def test_editor_boleh_masuk_halaman_manage(self):
        for nama in ["manage_projects", "manage_experience"]:
            with self.subTest(view=nama):
                self.assertEqual(self.client.get(reverse(f"main:{nama}")).status_code, 200)

    def test_editor_boleh_mengubah_project(self):
        r = self.client.post(
            reverse("main:update_project", args=[self.project.pk]),
            {"title": "SINTAKS BARU", "tech_stack": "", "thumbnail": "",
             "project_url": "", "description": "diubah editor", "content": ""},
            follow=True,
        )
        self.assertRedirects(r, reverse("main:manage_projects"))
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "SINTAKS BARU")

    def test_editor_boleh_mengubah_experience(self):
        r = self.client.post(
            reverse("main:update_experience", args=[self.experience.pk]),
            {"title": "RISTEK BARU", "job_title": "Ketua", "category": "volunteer",
             "thumbnail": "", "summary": "diubah editor", "content": "", "ended_at": ""},
            follow=True,
        )
        self.assertRedirects(r, reverse("main:manage_experience"))
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "RISTEK BARU")

    def test_editor_tidak_boleh_menambah_atau_menghapus(self):
        kasus = [
            ("create_project", []),
            ("create_experience", []),
            ("delete_project", [self.project.pk]),
            ("delete_experience", [self.experience.pk]),
        ]
        for nama, args in kasus:
            with self.subTest(view=nama):
                r = self.client.post(reverse(f"main:{nama}", args=args))
                self.assertEqual(r.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())

    def test_tombol_tambah_dan_hapus_tidak_muncul_untuk_editor(self):
        r = self.client.get(reverse("main:manage_projects"))
        self.assertNotContains(r, reverse("main:create_project"))
        self.assertNotContains(r, "Tambah Proyek")
        self.assertNotContains(r, reverse("main:delete_project", args=[self.project.pk]))
        # Tombol Ubah tetap ada supaya Editor bisa menjalankan tugasnya.
        self.assertContains(r, reverse("main:update_project", args=[self.project.pk]))
        self.assertContains(r, "Ubah Proyek")

    def test_owner_melihat_tombol_tambah_ubah_dan_hapus(self):
        owner = User.objects.create_superuser("owner", "owner@example.com", "rahasia-owner")
        self.client.force_login(owner)
        r = self.client.get(reverse("main:manage_projects"))
        self.assertContains(r, reverse("main:create_project"))
        self.assertContains(r, "Tambah Proyek")
        self.assertContains(r, reverse("main:delete_project", args=[self.project.pk]))
        self.assertContains(r, reverse("main:update_project", args=[self.project.pk]))

    def test_editor_tidak_melihat_tombol_tambah_di_halaman_publik(self):
        """Tombol+modal Tambah hanya untuk `add_project`; Editor tidak punya izin itu.

        Sebelumnya kondisinya digabung dengan `change_project`, jadi Editor melihat
        tombol yang `popovertarget`-nya menunjuk modal yang tidak dirender (tombol mati).
        """
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, reverse("main:manage_projects"))
        self.assertNotContains(r, "Tambah Proyek")
        self.assertNotContains(r, 'id="add-project-modal"')

    def test_owner_melihat_tombol_dan_modal_tambah_di_halaman_publik(self):
        owner = User.objects.create_superuser("owner2", "owner2@example.com", "rahasia-owner")
        self.client.force_login(owner)
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, "Tambah Proyek")
        self.assertContains(r, 'id="add-project-modal"')


class ToggleStarViewTests(TestCase):
    """toggle_star: satu star per pengguna, wajib login, `next` divalidasi."""

    def setUp(self):
        super().setUp()
        Project.objects.all().delete()
        self.project = Project.objects.create(title="SINTAKS")
        self.url = reverse("main:toggle_star", args=[self.project.pk])
        self.user = User.objects.create_user("penggemar", password="rahasia-user")

    def test_anonim_diarahkan_ke_login_dan_star_tidak_berubah(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("/login/"), r["Location"])
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_post_menambah_lalu_post_kedua_membatalkan(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"next": reverse("main:show_projects")})
        self.assertEqual(self.project.starred_by.count(), 1)
        self.client.post(self.url, {"next": reverse("main:show_projects")})
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_satu_pengguna_maksimal_satu_star(self):
        """Relasi M2M bikin star kedua dari user yang sama tidak menambah baris."""
        self.client.force_login(self.user)
        self.client.post(self.url)
        self.project.starred_by.add(self.user)
        self.assertEqual(self.project.starred_by.filter(pk=self.user.pk).count(), 1)

    def test_dua_pengguna_berbeda_menambah_dua_star(self):
        lain = User.objects.create_user("lain", password="rahasia-user")
        self.project.starred_by.add(self.user, lain)
        self.assertEqual(self.project.starred_by.count(), 2)

    def test_next_internal_dihormati(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url, {"next": reverse("main:show_experience")})
        self.assertRedirects(r, reverse("main:show_experience"))

    def test_next_ke_host_luar_diabaikan(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url, {"next": "https://jahat.example.com/"})
        self.assertRedirects(r, reverse("main:show_projects"))

    def test_get_tidak_mengubah_star(self):
        self.client.force_login(self.user)
        self.client.get(self.url)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_anonim_melihat_tautan_login_bukan_form_star(self):
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, "Login untuk memberi star")
        self.assertNotContains(r, self.url)

    def test_pengguna_login_melihat_form_star_bercsrf(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("main:show_projects"))
        # URL star kartu dibangun dari sentinel id; id aslinya datang dari JSON.
        self.assertContains(r, reverse("main:toggle_star", args=[PROJECT_ID_SENTINEL]))
        self.assertContains(r, "csrfmiddlewaretoken")
        self.assertContains(r, "button-star")

    def test_status_star_tampil_setelah_diberi(self):
        self.project.starred_by.add(self.user)
        self.client.force_login(self.user)
        r = self.client.get(reverse("main:show_projects"))
        self.assertContains(r, "is-starred")
        self.assertContains(r, "Unstar")


class ToggleStarExperienceViewTests(TestCase):
    """toggle_experience_star: kembar `toggle_star`, tapi untuk Experience."""

    def setUp(self):
        super().setUp()
        Experience.objects.all().delete()
        self.experience = Experience.objects.create(title="RISTEK", job_title="Anggota")
        self.url = reverse("main:toggle_experience_star", args=[self.experience.pk])
        self.user = User.objects.create_user("penggemar", password="rahasia-user")

    def test_anonim_diarahkan_ke_login_dan_star_tidak_berubah(self):
        r = self.client.post(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("/login/"), r["Location"])
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_post_menambah_lalu_post_kedua_membatalkan(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"next": reverse("main:show_experience")})
        self.assertEqual(self.experience.starred_by.count(), 1)
        self.client.post(self.url, {"next": reverse("main:show_experience")})
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_next_ke_host_luar_diabaikan(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url, {"next": "https://jahat.example.com/"})
        self.assertRedirects(r, reverse("main:show_experience"))

    def test_rute_star_tidak_tertangkap_rute_detail(self):
        """`experience/<path:title>/` juga cocok dengan URL ini, jadi urutannya penting."""
        self.assertEqual(self.url, f"/experience/{self.experience.pk}/star/")
        # Anonim -> 302 ke login. Kalau rute detail yang menang, hasilnya 404.
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_halaman_publik_menampilkan_tombol_star(self):
        r = self.client.get(reverse("main:show_experience"))
        self.assertContains(r, "Login untuk memberi star")
        self.assertNotContains(r, self.url)

        self.client.force_login(self.user)
        r = self.client.get(reverse("main:show_experience"))
        self.assertContains(r, self.url)
        self.assertContains(r, "csrfmiddlewaretoken")
        self.assertContains(r, "button-star")

    def test_status_star_tampil_setelah_diberi(self):
        self.experience.starred_by.add(self.user)
        self.client.force_login(self.user)
        r = self.client.get(reverse("main:show_experience"))
        self.assertContains(r, "is-starred")
        self.assertContains(r, "Unstar")

    def test_tombol_star_juga_muncul_di_halaman_manage(self):
        self.client.force_login(buat_user_editor())
        r = self.client.get(reverse("main:manage_experience"))
        self.assertContains(r, self.url)
        self.assertContains(r, "csrfmiddlewaretoken")

class ProjectXssGuardTests(AuthenticatedTestCase):
    """ProjectForm membuang tag HTML, dan halaman publik tidak pernah memuatnya mentah."""

    payload = '<img src="x" onerror="alert(\'XSS!\')">'

    def setUp(self):
        super().setUp()
        Project.objects.all().delete()

    def test_form_menolak_judul_yang_hanya_tag_html(self):
        r = self.client.post(reverse("main:create_project"), {"title": self.payload})
        self.assertTrue(r.context["form"].errors)
        self.assertIn("tidak boleh hanya berisi tag HTML", r.content.decode())
        self.assertEqual(Project.objects.count(), 0)

    def test_form_membersihkan_tag_pada_judul_tech_stack_dan_deskripsi(self):
        self.client.post(reverse("main:create_project"), {
            "title": "Halo <b>dunia</b>",
            "tech_stack": "Django <script>x</script>",
            "description": "<i>Ringkas</i>",
        })
        p = Project.objects.get()
        self.assertEqual(p.title, "Halo dunia")
        self.assertEqual(p.tech_stack, "Django x")
        self.assertEqual(p.description, "Ringkas")

    def test_halaman_publik_tidak_memuat_tag_mentah(self):
        """Data disuntik langsung ke DB (melewati form) untuk menguji jalur render."""
        Project.objects.create(title=self.payload)
        r = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(r, self.payload)
        # kartu dibangun JS, jadi yang boleh ada adalah pemanggilan escapeHtml
        self.assertContains(r, "escapeHtml(")
