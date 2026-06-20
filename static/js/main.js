/* Bellerophon GemInclusion — main.js */

/* ---- Mobile nav ---- */
(function () {
  const toggle = document.querySelector('.nav-toggle');
  const menu   = document.getElementById('nav-menu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!open));
    menu.classList.toggle('is-open', !open);
  });

  document.addEventListener('click', (e) => {
    if (!toggle.contains(e.target) && !menu.contains(e.target)) {
      toggle.setAttribute('aria-expanded', 'false');
      menu.classList.remove('is-open');
    }
  });
})();

/* ---- Inclusion filters ---- */
(function () {
  const grid       = document.getElementById('inclusion-grid');
  const noResults  = document.getElementById('no-results');
  const selHost    = document.getElementById('filter-host');
  const selOrigin  = document.getElementById('filter-origin');
  const selTreat   = document.getElementById('filter-treatment');
  const btnReset   = document.getElementById('filter-reset');

  if (!grid) return;

  const cards = Array.from(grid.querySelectorAll('.inclusion-card'));

  /* Populate filter options from existing cards */
  function populateFilter(select, attr) {
    const values = new Set();
    cards.forEach(c => {
      const v = (c.dataset[attr] || '').trim();
      if (v) values.add(v);
    });
    const sorted = [...values].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
    sorted.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v.charAt(0).toUpperCase() + v.slice(1);
      select.appendChild(opt);
    });
  }

  if (selHost)   populateFilter(selHost,   'host');
  if (selOrigin) populateFilter(selOrigin, 'origin');
  if (selTreat)  populateFilter(selTreat,  'treatment');

  function applyFilters() {
    const host    = selHost   ? selHost.value.toLowerCase()   : '';
    const origin  = selOrigin ? selOrigin.value.toLowerCase() : '';
    const treat   = selTreat  ? selTreat.value.toLowerCase()  : '';

    let visible = 0;
    cards.forEach(card => {
      const matchHost   = !host   || card.dataset.host   === host;
      const matchOrigin = !origin || card.dataset.origin === origin;
      const matchTreat  = !treat  || card.dataset.treatment === treat;

      if (matchHost && matchOrigin && matchTreat) {
        card.hidden = false;
        visible++;
      } else {
        card.hidden = true;
      }
    });

    if (noResults) noResults.hidden = visible > 0;
  }

  [selHost, selOrigin, selTreat].forEach(sel => {
    if (sel) sel.addEventListener('change', applyFilters);
  });

  if (btnReset) {
    btnReset.addEventListener('click', () => {
      if (selHost)   selHost.value   = '';
      if (selOrigin) selOrigin.value = '';
      if (selTreat)  selTreat.value  = '';
      applyFilters();
    });
  }
})();

/* ---- Lightbox ---- */
(function () {
  const lb       = document.getElementById('lightbox');
  const lbImg    = document.getElementById('lightbox-img');
  const lbCap    = document.getElementById('lightbox-caption');
  const lbClose  = lb && lb.querySelector('.lightbox-close');
  const backdrop = lb && lb.querySelector('.lightbox-backdrop');

  if (!lb) return;

  function openLightbox(src, alt, caption) {
    lbImg.src = '';
    lbImg.alt = alt || '';
    if (lbCap) lbCap.textContent = caption || alt || '';
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    /* Load full image after opening */
    lbImg.src = src;
    lb.focus();
  }

  function closeLightbox() {
    lb.hidden = true;
    lbImg.src = '';
    document.body.style.overflow = '';
  }

  /* Trigger elements */
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('.lightbox-trigger, .single-photo-wrap .single-photo');
    if (!trigger) return;
    e.preventDefault();
    const src     = trigger.dataset.full || trigger.src;
    const alt     = trigger.alt;
    const caption = trigger.dataset.caption || alt;
    openLightbox(src, alt, caption);
  });

  if (lbClose)  lbClose.addEventListener('click',  closeLightbox);
  if (backdrop) backdrop.addEventListener('click',  closeLightbox);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !lb.hidden) closeLightbox();
  });
})();
