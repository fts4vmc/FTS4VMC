$(function(){
    $("aside").on("click", "#load", upload_file);
    $("aside").on("click", "#full", 
      {url: '/full_analysis', success:timed_update_textarea}, command);
    $("aside").on("click", "#hdead", 
      {url: '/hdead_analysis', success:timed_update_textarea}, command);
    $("aside").on("click", "#delete", 
      {url: '/delete_model', success:update_textarea}, command);
    $("aside").on("click", "#stop", 
      {url: '/stop', success:update_textarea}, command);
    $("aside").on("click", "#disambiguate", 
      {url: '/remove_ambiguities', success:update_textarea}, command);
    $("aside").on("click", "#fopt", 
      {url: '/remove_false_opt', success:update_textarea}, command);
    $("aside").on("click", "#hdd", 
      {url: '/remove_dead_hidden', success:update_textarea}, command);
}); 

//Updates the main's textarea with the response value.
function update_textarea(response)
{
    $("main > textarea").text(response);
}

//Updates the main's textarea with the response value,
//and initiates the polling of process output.
function timed_update_textarea(response)
{
    $("main > textarea").text(response);
    process_update(1000);
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
            success: event.data.success,
            beforeSend: function(response) {
                $("main > textarea").text("Processing data...");
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
function process_update(wait)
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
                setTimeout(process_update.bind(null, wait), wait);
            },
            200: function(response) {
                $("main > textarea").append(response);
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
