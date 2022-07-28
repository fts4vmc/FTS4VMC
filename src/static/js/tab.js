"use strict";
$(function(){
    $("main").on("click", ".tab button", tab);
});

function tab() {
  $(".tab button").removeClass("selected-tab");
  $(".tab button").addClass("tab-button");
  $(this).removeClass("tab-button");
  $(this).addClass("selected-tab");
}
