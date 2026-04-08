// ── Theme Toggle ──────────────────────────────────────────────
const html        = document.documentElement;
const toggleBtn   = document.getElementById('themeToggle');
const STORAGE_KEY = 'suvera-theme';

function applyTheme(theme) {
  html.setAttribute('data-theme', theme);
  localStorage.setItem(STORAGE_KEY, theme);
}

// Restore saved preference (fall back to dark)
applyTheme(localStorage.getItem(STORAGE_KEY) || 'dark');

toggleBtn.addEventListener('click', () => {
  applyTheme(html.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
});

// ── Contact form — client-side handling ───────────────────────
const form = document.getElementById('contactForm');
const successMsg = document.getElementById('formSuccess');

form.addEventListener('submit', function (e) {
  e.preventDefault();

  const name    = form.name.value.trim();
  const email   = form.email.value.trim();
  const message = form.message.value.trim();

  if (!name || !email || !message) {
    successMsg.style.color = '#c0392b';
    successMsg.textContent = 'Please fill in all required fields.';
    return;
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    successMsg.style.color = '#c0392b';
    successMsg.textContent = 'Please enter a valid email address.';
    return;
  }

  // Simulate submission (replace with your real endpoint / API call)
  const submitBtn = form.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Sending…';

  setTimeout(() => {
    form.reset();
    successMsg.style.color = '';
    successMsg.textContent = 'Your message has been received. We\'ll be in touch.';
    submitBtn.disabled = false;
    submitBtn.textContent = 'Send Message';
  }, 1200);
});

// Subtle nav highlight on scroll
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav__links a');

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        navLinks.forEach((link) => {
          link.style.color =
            link.getAttribute('href') === `#${entry.target.id}`
              ? 'var(--gold-lt)'
              : '';
        });
      }
    });
  },
  { threshold: 0.4 }
);

sections.forEach((s) => observer.observe(s));
