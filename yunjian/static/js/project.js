/* Project specific Javascript goes here. */

// 向上滚动的函数
$(function () {
    $('#BackTop').click(function () {
        $('html,body').animate({scrollTop: 0}, 500);
    });
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('#BackTop').fadeIn(300);
        } else {
            $('#BackTop').stop().fadeOut(300);
        }
    }).scroll();
});
