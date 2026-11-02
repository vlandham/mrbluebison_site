// Turns the scroll-snap photo strip on post pages into a carousel with
// prev/next arrows and dots. Without JS the strip still swipes/scrolls.
document.querySelectorAll(".carousel").forEach(function (carousel) {
  var track = carousel.querySelector(".carousel-track");
  var slides = Array.prototype.slice.call(track.children);
  var dots = Array.prototype.slice.call(carousel.querySelectorAll(".carousel-dots button"));
  var prev = carousel.querySelector(".carousel-prev");
  var next = carousel.querySelector(".carousel-next");
  if (slides.length < 2 || !prev || !next) return;

  [prev, next, carousel.querySelector(".carousel-dots")].forEach(function (el) { el.hidden = false; });

  function current() {
    return Math.round(track.scrollLeft / track.clientWidth);
  }

  function go(i) {
    var n = (i + slides.length) % slides.length; // wrap around at the ends
    track.scrollTo({ left: n * track.clientWidth, behavior: "smooth" });
    update(n);
  }

  function update(i) {
    if (typeof i !== "number") i = current();
    dots.forEach(function (d, j) {
      if (j === i) d.setAttribute("aria-current", "true");
      else d.removeAttribute("aria-current");
    });
  }

  prev.addEventListener("click", function () { go(current() - 1); });
  next.addEventListener("click", function () { go(current() + 1); });
  dots.forEach(function (d, j) { d.addEventListener("click", function () { go(j); }); });
  // Keep dots in sync when the user swipes/scrolls; wait for scrolling to settle
  // so a smooth scroll triggered by a click doesn't flicker the dots.
  var settle;
  track.addEventListener("scroll", function () {
    clearTimeout(settle);
    settle = setTimeout(update, 100);
  }, { passive: true });
  track.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") { e.preventDefault(); go(current() - 1); }
    if (e.key === "ArrowRight") { e.preventDefault(); go(current() + 1); }
  });
});
