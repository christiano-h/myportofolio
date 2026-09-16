/**
 * Fokus kartu carousel `.portfolio-track`.
 *
 * Di desktop kartu berbaris sebagai grid dan efek "menyala" hanya muncul saat
 * hover. Di layar kecil (< 760px) track berubah jadi carousel, jadi kartu yang
 * paling dekat dengan titik tengah track ditandai `.is-active` supaya garis
 * glare-nya tampil tanpa perlu hover.
 *
 * Dipakai bersama oleh /experience/, /projects/, dan kedua halaman manage-nya
 * supaya skripnya tidak disalin empat kali di template.
 */
(function () {
    'use strict';

    // Batas lebar ini harus sama dengan breakpoint mobile di style.css.
    var MOBILE_MAX_WIDTH = 760;

    function clearActive(track) {
        var aktif = track.querySelectorAll('.is-active');
        Array.prototype.forEach.call(aktif, function (el) {
            el.classList.remove('is-active');
        });
    }

    function apply(track) {
        // Desktop (grid): biarkan glare hanya dari hover.
        if (window.innerWidth >= MOBILE_MAX_WIDTH) {
            clearActive(track);
            return;
        }

        var kartu = track.querySelectorAll('.project-card-outline');
        if (!kartu.length) return;

        var trackRect = track.getBoundingClientRect();
        var centerY = trackRect.top + trackRect.height / 2;
        var terdekat = kartu[0];
        var jarakTerdekat = Infinity;

        Array.prototype.forEach.call(kartu, function (c) {
            var r = c.getBoundingClientRect();
            var jarak = Math.abs(r.top + r.height / 2 - centerY);
            if (jarak < jarakTerdekat) {
                jarakTerdekat = jarak;
                terdekat = c;
            }
        });

        clearActive(track);
        terdekat.classList.add('is-active');
        var dalam = terdekat.querySelector('.project-card');
        if (dalam) dalam.classList.add('is-active');
    }

    function initTrack(track) {
        var ticking = false;

        function onScroll() {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(function () {
                apply(track);
                ticking = false;
            });
        }

        track.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('resize', function () { apply(track); });
        window.addEventListener('load', function () { apply(track); });
        apply(track);
    }

    function start() {
        var tracks = document.querySelectorAll('.portfolio-track');
        Array.prototype.forEach.call(tracks, initTrack);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();
