$(function(){
    $("aside").on("click", "#load", upload_file);
    $("aside").on("click", "#full", {url: '/full_analysis'}, command);
    $("aside").on("click", "#hdead", {url: '/hdead_analysis'}, command);
    $("aside").on("click", "#delete", {url: '/delete_model'}, command);
}); 

function upload_file(event)
{
    if($("#fts")[0].files[0]) {
        var file = new FormData();
        file.append('file', $("#fts")[0].files[0]);
        $.ajax({
            url: '/upload',
            data: file,
            processData: false,
            contentType: false,
            type: 'POST',
            success: function(response) {
                $("main > textarea").text(response);
            }
        });
    } else {
        $("main > textarea").text("Model file is missing.");
    }
}

function command(event)
{
    if($("#fts")[0].files[0]) {
        $.ajax({
            url: event.data.url,
            data: {name: $("#fts")[0].files[0].name},
            type: 'POST',
            success: function(response) {
                $("main > textarea").text(response);
            },
            beforeSend: function(response) {
                $("main > textarea").text("Processing data...");
            }
        });
    } else {
        $("main > textarea").text("Invalid file");
    }
}

function model_loaded(event) {
    $("main textarea").text("Model loaded")
}
