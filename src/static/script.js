$(function(){
    $("aside").on("change", "#fts", alter_title);
    $("aside").on("click", "#load" ,upload_file);
    $("aside").on("click", "#full", 
      {url: '/full_analysis', success:timed_update_textarea, 
        show:[
          $("#disambiguate"), $("#fopt"), $("#hdd"), 
          $("#full"), $("#hdead"), $("#delete"), $("#stop")
        ]
      }, command);

    $("aside").on("click", "#hdead", 
      {url: '/hdead_analysis', success:timed_update_textarea, 
        show:[$("#full"), $("#hdead"), $("#delete"), $("#stop")] 
      }, command);

    $("aside").on("click", "#delete", 
      {url: '/delete_model', success:update_textarea, show: [$("#fts-label")]}, command);
    $("aside").on("click", "#stop", 
      {url: '/stop', success:update_textarea, 
        show:[$("#full"), $("#hdead"), $("#delete")]}, command);
    $("aside").on("click", "#disambiguate", 
      {url: '/remove_ambiguities', success:update_textarea}, command);
    $("aside").on("click", "#fopt", 
      {url: '/remove_false_opt', success:update_textarea}, command);
    $("aside").on("click", "#hdd",
      {url: '/remove_dead_hidden', success:update_textarea,show:[
        $("#disambiguate"), $("#fopt"), $("#hdd"), 
          $("#full"), $("#fts"), $("#hdead"), $("#delete"), $("#load"),
$("#verify_properties"), $("#property_text_area")]}, command);
    $("aside").on("click", "#verify_properties", verify_property);
}); 

function alter_title() {
  let name = $("#fts").val().replace(/.*[\/\\]/, '');
  $("main > h2").text("Analysis of "+name);
  $("main > textarea").text(name+" selected, click load model to"+
    " upload the file");
  $("#load").slideDown();
}

function show_command(show)
{
  if(show) {
    $(".command").hide();
    for (element of show) {
      element.slideDown();
    }
  }
}

//Updates the main's textarea with the response value.
function update_textarea(show, response)
{
  $("main > textarea").text(response);
  show_command(show);
}

//Updates the main's textarea with the response value,
//and initiates the polling of process output.
function timed_update_textarea(show, response)
{
    $("main > textarea").text(response);
    $(".command").hide();
    $("#stop").slideDown();
    process_update(show, 1000);
}

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
                $("#full").slideDown();
                $("#hdead").slideDown();
                $("#delete").slideDown();
                $("#verify_properties").slideUp();
            },
            error: function(response) {
                $("main > textarea").text(response.responseText);
            },
            beforeSend: function() {
              $("main > textarea")
                .text("Checking if the provided dot file contains a FTS...");
            }
        });
    } else {
        $("main > textarea").text("Model file is missing.");
    }
}


function command(event)
{
    if(event.data.url.equals('/delete_model')){    
        $("#property_text_area").slideUp();
    }
 
    if($("#fts")[0].files[0]) {
        $.ajax({
            url: event.data.url,
            data: {name: $("#fts")[0].files[0].name},
            type: 'POST',
            success: function(response){
                event.data.success(event.data.show, response);
            },
            beforeSend: function(response) {
                $("main > textarea").text("Processing data...");
            },
            error: function(response) {
                $("main > textarea").text(response.responseText);
            }
        });
    } else {
        $("main > textarea").text("Invalid file");
    }
}

// Requests data at /yield to append inside the textarea,
// if the received status code is 206 (partial content) and response
// contains some data waits 1000 ms before requesting data again otherwise
// double wait value and waits 'wait'ms before requesting data again.
// If the received status code is 200 appends the data inside the textarea.
// On completed request scrolls to the bottom of the textarea to emulate
// terminal behaviour.
function process_update(show, wait)
{
    $.ajax({
        url: '/yield', 
        statusCode: {
            206: function(response) {
                $("main > textarea").append(response);
                if(response)
                    wait = 1000;
                else
                    wait = wait * 2;
                setTimeout(process_update.bind(null, show, wait), wait);
            },
            200: function(response) {
                $("main > textarea").append(response);
                show_command(show);
                $("#stop").hide();
            }
        },
        complete: function(response) {
            if(response) {
                $('main > textarea').scrollTop(
                    $('main > textarea')[0].scrollHeight
                );
            }
        }
    });
}

function verify_property()
{
    
    var prop = $("#property_text_area").val();
    if($("#fts")[0].files[0]) {
        $.ajax({
            url: '/verify_property',
            data: {name: $("#fts")[0].files[0].name, property: prop},
            type: 'POST',
            success: function(response){
                $("main > textarea").text(response);
                //event.data.success(event.data.show, response);
            },
            beforeSend: function(response) {
                $("main > textarea").text("Processing data...");
            },
            error: function(response) {
                $("main > textarea").text(response);
            }
        });
    } else {
        $("main > textarea").text("Invalid file");
    }
}

