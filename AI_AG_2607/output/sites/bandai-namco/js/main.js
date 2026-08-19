(function () {
  'use strict';

  // 모바일 내비게이션 토글
  var toggle = document.querySelector('.nav-toggle');
  var menu = document.getElementById('nav-menu');

  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var expanded = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expanded));
      menu.classList.toggle('is-open');
    });

    menu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        toggle.setAttribute('aria-expanded', 'false');
        menu.classList.remove('is-open');
      });
    });
  }

  // 카운트업 애니메이션 (실적 하이라이트)
  var countEls = document.querySelectorAll('.count-up');
  var countObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var el = entry.target;
      var target = parseInt(el.dataset.target, 10) || 0;
      var suffix = el.dataset.suffix || '';
      var duration = 1400;
      var start = null;

      function step(timestamp) {
        if (start === null) start = timestamp;
        var progress = Math.min((timestamp - start) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        var current = Math.round(target * eased);
        el.textContent = current.toLocaleString('ko-KR') + suffix;
        if (progress < 1) {
          window.requestAnimationFrame(step);
        }
      }
      window.requestAnimationFrame(step);
      countObserver.unobserve(el);
    });
  }, { threshold: 0.5 });

  countEls.forEach(function (el) { countObserver.observe(el); });

  // 실적 그래프 바 애니메이션
  var bars = document.querySelectorAll('.bar-chart__bar');
  var barObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var bar = entry.target;
      var height = bar.dataset.height || 0;
      bar.style.setProperty('--pct', height + '%');
      barObserver.unobserve(bar);
    });
  }, { threshold: 0.4 });

  bars.forEach(function (bar) { barObserver.observe(bar); });
})();
