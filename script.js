// Mobile nav toggle
const hamburger = document.getElementById('hamburger');
const nav = document.getElementById('nav');
hamburger.addEventListener('click', () => {
  nav.classList.toggle('open');
});
nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => nav.classList.remove('open')));

// Header shadow on scroll
const header = document.getElementById('header');
window.addEventListener('scroll', () => {
  header.classList.toggle('scrolled', window.scrollY > 10);
});

// Scroll reveal
const toReveal = document.querySelectorAll('.section__head, .card, .about__media, .about__content, .grid__item, .gallery__item, .testi, .contact__form, .contact__info');
toReveal.forEach(el => el.classList.add('reveal'));
const io = new IntersectionObserver((entries) => {
  entries.forEach((e, i) => {
    if (e.isIntersecting) {
      setTimeout(() => e.target.classList.add('in'), (i % 4) * 80);
      io.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });
toReveal.forEach(el => io.observe(el));

// Contact form -> skickar lead till backend (-> Telegram till din bror)
const form = document.getElementById('contactForm');
const note = document.getElementById('formNote');
form.addEventListener('submit', (e) => {
  e.preventDefault();
  const lead = {
    name: form.name.value,
    email: form.email.value,
    phone: form.phone.value,
    service: form.service.value,
    message: form.message.value,
    source: 'kontaktformulär',
  };
  // Backend (lead -> Telegram) körs på Render; sidan kan ligga på CDN (snabb, ingen kallstart)
  fetch('https://solidservice.onrender.com/api/lead', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lead),
  }).catch(() => {});
  note.textContent = 'Tack! Vi har tagit emot din förfrågan och återkommer inom 24 timmar.';
  note.classList.add('ok');
  form.reset();
});
