/* ══════════════════════════════════════════════════════
   SUVERA — Main Script
   1. Header scroll state
   2. Scroll reveal (IntersectionObserver)
   3. Parallax: image break + statement bg
   4. Mobile nav toggle
   5. Contact form (Formspree + success state)
══════════════════════════════════════════════════════ */

'use strict';


/* ─────────────────────────────────────────────
   1. HEADER — background appears on scroll
───────────────────────────────────────────── */
(function () {
  const header = document.getElementById('header');
  if (!header) return;

  const update = () => header.classList.toggle('scrolled', window.scrollY > 40);

  window.addEventListener('scroll', update, { passive: true });
  update();
}());


/* ─────────────────────────────────────────────
   2. SCROLL REVEAL
───────────────────────────────────────────── */
(function () {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
  );

  els.forEach((el) => io.observe(el));
}());


/* ─────────────────────────────────────────────
   3. PARALLAX
   image break (.parallax) + statement bg (.parallax-stmt)
   Uses rAF with a ticking guard for smooth, low-cost animation.
───────────────────────────────────────────── */
(function () {
  const breakEl = document.querySelector('.parallax');
  const stmtEl  = document.querySelector('.parallax-stmt');
  if (!breakEl && !stmtEl) return;

  let ticking = false;

  function calcOffset(el, strength) {
    const rect = el.parentElement.getBoundingClientRect();
    const vh   = window.innerHeight;
    if (rect.bottom < -80 || rect.top > vh + 80) return null;
    const progress = (vh - rect.top) / (vh + rect.height);
    return ((progress - 0.5) * strength).toFixed(2);
  }

  function tick() {
    if (breakEl) {
      const y = calcOffset(breakEl, 110);
      if (y !== null) breakEl.style.transform = `translateY(${y}px)`;
    }
    if (stmtEl) {
      const y = calcOffset(stmtEl, 80);
      if (y !== null) stmtEl.style.transform = `translateY(${y}px)`;
    }
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(tick); ticking = true; }
  }, { passive: true });

  window.addEventListener('resize', () => {
    if (!ticking) { requestAnimationFrame(tick); ticking = true; }
  }, { passive: true });

  tick();
}());


/* ─────────────────────────────────────────────
   4. MOBILE NAV TOGGLE
───────────────────────────────────────────── */
(function () {
  const btn   = document.querySelector('.header__menu-btn');
  const nav   = document.getElementById('mobileNav');
  if (!btn || !nav) return;

  const links = nav.querySelectorAll('a');

  function openMenu() {
    btn.setAttribute('aria-expanded', 'true');
    nav.setAttribute('aria-hidden',   'false');
    nav.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    btn.setAttribute('aria-expanded', 'false');
    nav.setAttribute('aria-hidden',   'true');
    nav.classList.remove('open');
    document.body.style.overflow = '';
  }

  btn.addEventListener('click', () => {
    btn.getAttribute('aria-expanded') === 'true' ? closeMenu() : openMenu();
  });

  links.forEach((link) => link.addEventListener('click', closeMenu));

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('open')) closeMenu();
  });
}());


/* ─────────────────────────────────────────────
   5. CONTACT FORM
   Submits to Formspree (replace YOUR_FORM_ID in the
   action attribute with a real Formspree endpoint).
   Shows inline success message on completion.
───────────────────────────────────────────── */
(function () {
  const form    = document.getElementById('contactForm');
  const success = document.getElementById('formSuccess');
  if (!form || !success) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = form.querySelector('[type="submit"]');
    const original = btn.textContent;
    btn.textContent = 'Sending\u2026';
    btn.disabled = true;

    try {
      const res = await fetch(form.action, {
        method:  'POST',
        body:    new FormData(form),
        headers: { Accept: 'application/json' },
      });

      if (res.ok) {
        form.reset();
        success.hidden = false;
        btn.closest('.form-submit').style.display = 'none';
        success.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        throw new Error('Server error');
      }
    } catch {
      btn.textContent = original;
      btn.disabled    = false;
      alert(
        'There was a problem sending your enquiry.\n' +
        'Please email us directly at info@suvera.com.au'
      );
    }
  });
}());
