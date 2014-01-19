$(window).load(function() {
  $('.image_link_thumb').hover(
    function() { $(this).addClass('hover').next().addClass('hover'); }, 
    function() { $(this).removeClass('hover').next().removeClass('hover'); }
    );

  $("#slider").responsiveSlides({
    auto: true,
    pager: true,
    nav: true,
    speed: 500,
    maxwidth: 800,
    namespace: "centered-btns"
  });
});

