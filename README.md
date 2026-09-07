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


> AI disclosure : [ristek.link/AI-DISCLOSURE-PBP](https://ristek.link/AI-DISCLOSURE-PBP)