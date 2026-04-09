// ── Theme Toggle ───────────────────────────────────────────────
const html        = document.documentElement;
const toggleBtn   = document.getElementById('themeToggle');
const STORAGE_KEY = 'suvera-theme';

function applyTheme(theme) {
  html.setAttribute('data-theme', theme);
  localStorage.setItem(STORAGE_KEY, theme);
}
applyTheme(localStorage.getItem(STORAGE_KEY) || 'dark');

toggleBtn.addEventListener('click', () => {
  applyTheme(html.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
});

// ── Custom Cursor ──────────────────────────────────────────────
const cursor = document.createElement('div');
cursor.className = 'cursor';
document.body.appendChild(cursor);

document.addEventListener('mousemove', e => {
  cursor.style.transform = `translate(calc(${e.clientX}px - 50%), calc(${e.clientY}px - 50%))`;
});

document.addEventListener('mouseover', e => {
  const hoverable = e.target.closest('a, button, input, select, textarea, [role="button"], .service-row__summary');
  cursor.classList.toggle('cursor--hover', !!hoverable);
});

// ── Nav background on scroll ───────────────────────────────────
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('nav--scrolled', window.scrollY > 50);
}, { passive: true });

// ── Scroll Reveal ──────────────────────────────────────────────
const revealEls = document.querySelectorAll('.reveal');

const revealObserver = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
);

revealEls.forEach(el => revealObserver.observe(el));

// ── Nav active link on scroll ──────────────────────────────────
const sections  = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav__links a');

const sectionObserver = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => {
          link.style.color =
            link.getAttribute('href') === `#${entry.target.id}` ? 'var(--fg)' : '';
        });
      }
    });
  },
  { threshold: 0.35 }
);
sections.forEach(s => sectionObserver.observe(s));

// ── Services Accordion ────────────────────────────────────────
document.querySelectorAll('.service-row__summary').forEach(summary => {
  summary.addEventListener('click', () => {
    const row = summary.closest('.service-row');
    const isOpen = row.classList.contains('is-open');
    document.querySelectorAll('.service-row').forEach(r => r.classList.remove('is-open'));
    if (!isOpen) row.classList.add('is-open');
  });
});

// ── Contact Form ───────────────────────────────────────────────
const form       = document.getElementById('contactForm');
const successMsg = document.getElementById('formSuccess');

form.addEventListener('submit', function (e) {
  e.preventDefault();

  const name    = form.name.value.trim();
  const email   = form.email.value.trim();
  const message = form.message.value.trim();

  if (!name || !email || !message) {
    successMsg.style.color = '#b04040';
    successMsg.textContent = 'Please complete all required fields.';
    return;
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    successMsg.style.color = '#b04040';
    successMsg.textContent = 'Please enter a valid email address.';
    return;
  }

  const submitBtn = form.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Sending…';

  setTimeout(() => {
    form.reset();
    successMsg.style.color = '';
    successMsg.textContent = 'Thank you. We have received your enquiry and will be in touch within one business day.';
    submitBtn.disabled = false;
    submitBtn.textContent = 'Send Enquiry';
  }, 1200);
});
