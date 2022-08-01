"use strict";
$(function(){
    $("aside").on("click", "#download", download);
    $("aside").on("click", "#load", upload_file);
    $("aside").on("change", "#fts", alter_title);
});

function alter_title() 
{
    $("main > h3").text('FTS')
    let name = $("#fts").val().replace(/.*[\/\\]/, '');
    $("main > h2").text("Analysis of "+name);
    $("#console").text(name+" selected, click load model to"+
        " upload the file");
    $(".operation").prop("disabled", true);
    $("#fts").prop("disabled", false);
    $("#load").prop("disabled", false);
}

function upload_file(event)
{
    $("main > h3").text('FTS')
    if($("#fts")[0].files[0]) {
        var file = new FormData();
        file.append('file', $("#fts")[0].files[0]);
        var request = {url: full_url('/upload'), data: file, processData: false,
            contentType: false, type: 'POST'};
        request['success'] = function(response) {
            $("#console").text(response['text']);
            create_summary($("#summary"), response);
            $("#source").text(response['graph']);
            $("#tmp-source").val(response['mts']);
            $("#tmp-source").attr('name', 'MTS');
            $("#full").prop("disabled", false);
            $("#hdead").prop("disabled", false);
            $("#delete").prop("disabled", false);
            $("#mts").prop("disabled", false);
            $("#download").prop("disabled", false);
            $("#verify_properties").prop("disabled", true);
            $("#load").prop("disabled", true);
            $("#fts").prop("disabled", true);
            $("#fts-label").removeClass("command").addClass("fts-label-disabled");
        };
        request['error'] = function(response) {
          if(response.responseJSON && response.responseJSON['text'])
            $("#console").text(response.responseJSON['text']);
        };
        request['beforeSend'] = function() {
          $("#console")
            .text("Checking if the provided dot file contains a FTS...");
          var message = "\nFile bigger than 1MB are refused by the server.\n"+
            "If the file is smaller than 1MB please wait otherwise"+
            " try uploading a smaller file.";
          $("#console").append(message);
        };
        $.ajax(request);
    } else {
        $("#console").text("Model file is missing.");
    }
}

function download()
{
  var request = {url:full_url('/download'), type:'POST'};
  request['success'] = function(response) {
    $("a").attr('href', response['source']);
    $("a").attr('download', response['name']);
    document.getElementById('downloader').click();
  }
  request['error'] = function(response) {
    $("#message").text(response.responseJSON['text']).show().fadeOut(2000);
  }
  request['data'] = {};
  if($("#console:visible").length){
    request['data']['target'] = 'console';
    request['data']['main'] = $("#console").text();
  }
  if($("#source:visible").length){
    request['data']['target'] = 'source';
    request['data']['main'] = $("#source").text();
  }
  if($("#image:visible").length){
    request['data']['target'] = 'graph';
    request['data']['main'] = $("#image").attr('src');
  }
  if($("#summary:visible").length){
    request['data']['target'] = 'summary';
    request['data']['main'] = $("#summary").html();
  }

  if($("#counter_image:visible").length){
    var a = $("<a>")
      .attr("href", $("#counter_image")[0].src)
      .attr("download", "img.png")
      .appendTo("body");
    a[0].click();
    a.remove();
    return;
  }
  $.ajax(request);
}
