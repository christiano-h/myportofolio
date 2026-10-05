// Utilitas HTTP bersama untuk halaman AJAX (experience & projects).

function getCookie(name) {
    const cookieValue = document.cookie
        .split(';')
        .map((c) => c.trim())
        .find((c) => c.startsWith(name + '='));
    return cookieValue ? decodeURIComponent(cookieValue.split('=')[1]) : null;
}

// Meniru autoescape Django (django.utils.html.escape) — melindungi dari XSS.
function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
}

// POST JSON dengan token CSRF. Mengembalikan { ok, status, data }.
async function postJson(url, formData) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Accept': 'application/json',
        },
        body: formData,
    });

    let data = null;
    try { data = await response.json(); } catch (e) { data = null; }
    return { ok: response.ok, status: response.status, data };
}
