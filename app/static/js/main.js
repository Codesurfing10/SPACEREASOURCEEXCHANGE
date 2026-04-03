/* Space Resource Exchange — Main JS */

// ── Starfield ──────────────────────────────────────────────────────────────
(function () {
  const canvas = document.getElementById('starfield');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let stars = [];
  const STAR_COUNT = 200;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createStar() {
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.5 + 0.2,
      alpha: Math.random() * 0.8 + 0.2,
      speed: Math.random() * 0.15 + 0.02,
      twinkleSpeed: Math.random() * 0.015 + 0.005,
      twinkleDir: Math.random() > 0.5 ? 1 : -1,
    };
  }

  function init() {
    resize();
    stars = Array.from({ length: STAR_COUNT }, createStar);
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    stars.forEach((s) => {
      // Twinkle
      s.alpha += s.twinkleSpeed * s.twinkleDir;
      if (s.alpha > 1 || s.alpha < 0.1) s.twinkleDir *= -1;

      // Slow drift downward
      s.y += s.speed;
      if (s.y > canvas.height) {
        s.y = 0;
        s.x = Math.random() * canvas.width;
      }

      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(200, 220, 255, ${s.alpha})`;
      ctx.fill();
    });

    // Occasional shooting star
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', () => {
    resize();
    stars.forEach((s) => {
      if (s.x > canvas.width) s.x = Math.random() * canvas.width;
      if (s.y > canvas.height) s.y = Math.random() * canvas.height;
    });
  });

  init();
  draw();

  // Shooting stars
  function shootingStar() {
    const x = Math.random() * canvas.width;
    const y = Math.random() * (canvas.height / 2);
    const len = Math.random() * 120 + 60;
    const angle = Math.PI / 4 + (Math.random() - 0.5) * 0.4;
    let progress = 0;
    const speed = 0.04;

    function animShoot() {
      progress += speed;
      if (progress > 1) return;

      const px = x + Math.cos(angle) * len * progress;
      const py = y + Math.sin(angle) * len * progress;

      const grad = ctx.createLinearGradient(px - 40, py - 40, px, py);
      grad.addColorStop(0, 'rgba(0,255,231,0)');
      grad.addColorStop(1, `rgba(0,255,231,${0.8 * (1 - progress)})`);

      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(px, py);
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      requestAnimationFrame(animShoot);
    }

    animShoot();
  }

  setInterval(shootingStar, 3500);
})();
