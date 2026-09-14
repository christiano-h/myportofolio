# Ano - Portfolio

Website portofolio pribadi berbasis **Django** untuk keperluan tugas Pemrograman Berbasis Platform (PBP).

--- 

Nama : Christiano Hosea Imannuel

NPM : 2506615280

Kelas : PBP B

---

### Tugas 1

1. **Penggunaan Elemen Semantik HTML5**
   Yes, saya menggunakan elemen semantik HTML5 pada struktur web ini seperti `<header>`, `<main>`, `<section>`, `<article>`, dan `<footer>`. 

   Elemen tersebut membantu saya dalam membangun static web karena memberikan "makna" yang jelas pada struktur dokumen daripada cuman menggunakan `<div>`. 
   
   Penjelasan : 

   - `<section>` membantu saya untuk memisahkan bagian  utama yang berdiri sendiri, yaitu bagian profil (`id="profile"`) dan daftar proyek (`id="projects"`). 

   - `<article>` digunakan sebagai wrapper setiap kartu portofolio (`.portfolio-card`) karena setiap proyek merupakan konten yang berdiri sendiri.

   Selain membuat kode lebih rapi, hal tersebut juga meningkatkan readability dan lebih mudah untuk di-maintain.

2. **Tantangan Responsivitas dan Evaluasi Tata Letak**
   Tantangan terbesar adalah menjaga agar elemen terlihat pas di layar HP tapi juga bagus di layar desktop. Saya mengevaluasi tampilan menggunakan media query (`@media`) dengan beberapa penyesuaian :

   - **Hero/Profil:** Pada desktop saya menggunakan grid dua kolom (`1.3fr 1fr`), saat beralih ke mobile (`max-width: 600px`), tata letak juga diubah jadi satu kolom vertikal. Saya memposisikannya dengan menempatkan identitas nama di atas, diikuti foto, lalu detail/bio (sesuai dengan template yang diberikan pada tutorial).

   - **Daftar Proyek:** Pada desktop (`min-width: 760px`), proyek dirender menggunakan grid yang responsif (`auto-fill`). Tapi menurut saya kalau berpindah ke view di mobile, ngestack kartu ke bawah akan membuat halaman panjang, jadinya saya mengubah susunan menjadi carousel horizontal (*horizontal scroll snap*) supaya ukuran gambar (*aspect ratio* 16:9) tetap proporsional dan nyaman dilihat satu per satu.

3. **Batasan Static Web dan Rencana Fungsionalitas Dinamis**
   Sebagai static web, batasan yang saya rasakan ada pada skalabilitas. Setiap kali ingin menambahkan proyek baru, saya harus mengedit file HTML (*hardcode*) dan mengcopy-paste blok kode `<article>` secara manual berulang-ulang. 

   Fungsionalitas dinamis yang ingin saya tambahkan pada proyek yakni memisahkan data proyek ke dalam *database* atau file JSON, agar kartu portofolio bisa di-*generate* secara otomatis dan tidak harus ribet copy-paste berkali-kali.

---

### Tugas 2

1. **Alur Permintaan Halaman Experience (dari Request sampai Tampil di Browser)**

   Ketika saya membuka `/experience/`, urutan yang terjadi adalah:

   1. **Browser** mengirim HTTP request `GET /experience/`.
   2. **`portofolio/settings.py`** menjadi titik awal konfigurasi. `ROOT_URLCONF = 'portofolio.urls'` yang memberitahu Django file URL utama yang harus dibaca. `INSTALLED_APPS` juga memuat `'main'`, sehingga Django mengenali aplikasi `main` beserta model, migrasi, dan templatenya.
   3. **`portofolio/urls.py` (urls.py proyek)** berperan sebagai *router tingkat proyek*:
      ```python
      urlpatterns = [
          path("admin/", admin.site.urls),
          path("", include("main.urls")),
      ]
      ```
      Karena ada `include("main.urls")`, semua request yang bukan `admin/` diteruskan ke `main/urls.py`. Jadi file ini hanya memilah "request ini masuk aplikasi mana", bukan menentukan halaman spesifik.
   4. **`main/urls.py` (urls.py aplikasi)** memetakan path di dalam aplikasi ke fungsi view:
      ```python
      app_name = "main"
      urlpatterns = [
          path("", show_main, name="show_main"),
          path("experience/", show_experience, name="show_experience"),
          path("experience/<str:title>/", show_experience_detail, name="show_experience_detail"),
          path("project/<str:title>/", show_project_detail, name="show_project_detail"),
      ]
      ```
      Path `experience/` cocok, sehingga Django memanggil `show_experience`. `app_name = "main"` memberi *namespace*, sehingga di template saya menulis `{% url 'main:show_experience' %}`. Bagian `<str:title>` pada route detail adalah *path converter* yang menangkap judul dari URL dan mengirimkannya sebagai argumen ke view.
   5. **`main/views.py` — fungsi `show_experience`** menjembatani model dan template:
      ```python
      def show_experience(request):
          context = {
              "name": "Christiano H",
              "experience_list": Experience.objects.all().order_by("-started_at"),
          }
          return render(request, "experience.html", context)
      ```
      Di sini **model** dipakai. `Experience.objects.all().order_by("-started_at")` bukan perintah Python biasa, Django menerjemahkannya menjadi SQL kurang lebih `SELECT * FROM main_experience ORDER BY started_at DESC`, lalu menjalankannya ke database (SQLite di lokal, PostgreSQL di PWS). Hasilnya `QuerySet` berisi objek `Experience`, masing-masing punya atribut sesuai field di `models.py` (`title`, `job_title`, `summary`, `thumbnail`, dst). Objek itu disusun ke `context` sebagai `experience_list`.
   6. **`render(request, "experience.html", context)`** memanggil template. Django mencarinya sesuai `TEMPLATES` di `settings.py` baris 63, yaitu `DIRS = [BASE_DIR / 'templates']`, sehingga ketemu `templates/experience.html`.
   7. **Template** mengubah objek menjadi HTML. `{% for exp in experience_list %}` mengulang tiap objek, lalu `{{ exp.title }}`, `{{ exp.job_title }}`, `{{ exp.summary }}` mencetak atribut model. `{% url 'main:show_experience_detail' exp.title %}` memakai *reverse URL*, jadi link detail dibangun dari nama route dan tidak perlu ditulis manual. Nilai juga di-*escape* otomatis (mis. `&` menjadi `&amp;`, `<` menjadi `&lt;`) untuk mencegah HTML injection.
   8. **`HttpResponse`** berisi HTML akhir dikirim balik ke browser. Browser me-render HTML tersebut dan meminta aset tambahan (`/static/css/style.css`) untuk menampilkan tampilan akhir.

   Ringkasnya: **urls.py proyek** memilih aplikasi -> **urls.py aplikasi** memilih view -> **view** mengambil data lewat **model** -> **template** menampilkannya.

2. **Kenapa Data Portofolio Disimpan di Model, Bukan Ditulis Langsung di Template?**

   Pada Tugas 1 data project masih di-*hardcode* di HTML, sehingga menambah data berarti copy-paste blok `<article>` berulang. Di Tugas 2 data dipindahkan ke model `Experience`. Alasannya:

   - **Sentralisasi data** Data hanya hidup di satu tempat, yakni database. Halaman daftar, halaman detail, dan admin membaca sumber yang sama, jadi tidak mungkin ada data yang berbeda antar halaman.

   - **Template jadi bersih dan tak redundant.** `templates/experience.html` hanya berisi satu blok kartu di dalam `{% for %}`. Mau 6 ataupun 67 experience, ukuran template tidak berubah. Di Tugas 1, 67 proyek berarti 67 blok `<article>` yang harus dijaga manual.

   - **Penambahan data lebih mudah** Cukup lewat Django admin (`/admin/`) atau `python manage.py shell`. Contoh nyatanya: menambahkan "RISTEK Fasilkom UI" tadi hanya butuh satu data baru — tidak ada satu pun file template yang diubah, dan salah ketik pun tidak sampai merusak struktur HTML.

   - **Perubahan desain tidak menyentuh data.** Saat menukar posisi judul dan jabatan pada kartu, yang saya edit hanya template dan CSS. Datanya tidak disentuh sama sekali, dan seluruh kartu ikut berubah serempak.

   - **Ada validasi dan tipe data.** Model memaksa tipe yang benar: `title` dibatasi `max_length=100`, `thumbnail` bertipe `URLField`, `category` dibatasi daftar pilihan (`choices`). Jaminan seperti ini tidak ada kalau data ditulis mentah di HTML.

   - **Pengolahan data dilakukan oleh database.** `order_by("-started_at")` dieksekusi oleh database, sehingga urutan dan filter tetap efisien walaupun data bertambah banyak. Template tidak perlu memuat logika pengurutan.

   - **Aman dikelola bersama.** Orang lain (atau saya sendiri beberapa bulan kemudian) bisa menambah data lewat admin tanpa perlu paham HTML/CSS, sehingga risiko kesalahan lebih kecil.

   Dampaknya terasa saat *deploy*: karena data ada di model, saya bisa mengubahnya di PWS melalui Django admin tanpa `git push`. Kalau data tertanam di template, setiap perubahan sekecil apa pun memaksa push ulang.

   Kekurangannya, menyimpan di model menambah lapisan (model + migrasi + query), jadi untuk konten yang benar-benar statis dan jarang berubah, HTML langsung bisa lebih sederhana. Namun untuk daftar portofolio yang isinya terus bertambah, keuntungannya jauh lebih besar.

3. **Perbedaan `makemigrations` dan `migrate`**

   Kedua perintah ini sering dianggap sama, padahal tugasnya berbeda.

   **`makemigrations`** bertugas membaca `models.py`, membandingkannya dengan file migrasi terakhir, lalu **membuat file migrasi baru** yang berisi instruksi perubahan. Perintah ini **tidak menyentuh database sama sekali** — hasilnya hanya file Python baru di `main/migrations/`.

   **`migrate`** bertugas **menjalankan** file migrasi yang belum diterapkan ke database. Perintah inilah yang benar-benar mengubah tabel: menambah kolom, mengubah tipe field, sekaligus menjalankan migrasi data. Analoginya seperti memasak resep yang sudah ditulis.

   Jadi urutannya selalu `makemigrations` dulu, baru `migrate`. Ringkasnya:

   - `makemigrations` = membaca model lalu menghasilkan file migrasi. Database **tidak** berubah.
   - `migrate` = menjalankan file migrasi tersebut. Database **berubah**.

   Karena `makemigrations` tidak menyentuh database, mengubah `models.py` lalu langsung menjalankan server akan menyebabkan error. Ini pernah saya alami sendiri: setelah menambahkan field `job_title` pada model `Experience`, halaman `/experience/` error `no such column: main_experience.job_title` karena kolom itu belum ada di database.

   **Contoh 1 — menambah field baru:**
   ```python
   class Project(models.Model):
       title = models.CharField(max_length=100)
       description = models.TextField(blank=True, null=True)
       content = models.TextField(blank=True, null=True)   # field baru
       thumbnail = models.URLField(blank=True, null=True)
   ```
   ```bash
   python manage.py makemigrations main   
   python manage.py migrate               
   ```
   Kalau hanya `makemigrations` yang dijalankan, file migrasinya ada tetapi database belum berubah, sehingga query yang men-SELECT kolom `content` akan error `no such column`.

   **Contoh 2 — mengubah field yang sudah ada:** mengubah `Project.title` menjadi `unique=True` juga butuh keduanya, dan `makemigrations` akan menghasilkan `AlterField`.

   **Catatan saat deploy:** file migrasi adalah bagian dari kode, jadi harus di-*commit* dan di-*push*. Sebaliknya, `makemigrations` tidak pernah dijalankan otomatis di server, karena migrasi adalah artefak yang harus saya tinjau dan uji dulu di lokal. Untuk memastikan tidak ada model yang belum termigrasi, saya memakai `python manage.py makemigrations --check --dry-run`.

> AI disclosure : [ristek.link/AI-DISCLOSURE-PBP](https://ristek.link/AI-DISCLOSURE-PBP)