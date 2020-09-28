$(function(){
    $("aside").on("change", "#fts", alter_title);
    $("aside").on("click", "#load", upload_file);
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
        {url: '/remove_dead_hidden', success:update_textarea}, command);
}); 

function alter_title() {
    let name = $("#fts").val().replace(/.*[\/\\]/, '');
    $("main > h2").text("Analysis of "+name);
    $("#terminal").text(name+" selected, click load model to"+
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
    $("#terminal").text(response);
    show_command(show);
}

//Updates the main's textarea with the response value.
function update_textarea_graph(show, response)
{
    $("#terminal").text(response);
    show_command(show);
    request = {url: '/graph', data: $("#terminal").val(), type: 'GET'};
    xhr.responseType = "blob";
    response['success'] = test;
    xhr.send();
}

function test(e) {
    var urlCreator = window.URL || window.webkitURL;
    var imageUrl = urlCreator.createObjectURL(this.response);
    document.querySelector("#image").src = imageUrl;
}

//Updates the main's textarea with the response value,
//and initiates the polling of process output.
function timed_update_textarea(show, response)
{
    $("#terminal").text(response);
    $(".command").hide();
    $("#stop").slideDown();
    process_update(show, 1000);
}

function upload_file(event)
{
    if($("#fts")[0].files[0]) {
        var file = new FormData();
        file.append('file', $("#fts")[0].files[0]);
        request = {url: '/upload', data: file, processData: false,
            contentType: false, type: 'POST'};
        request['success'] = function(response) {
            $("#terminal").text(response);
            $("#full").slideDown();
            $("#hdead").slideDown();
            $("#delete").slideDown();
        };
        request['error'] = function(response) {
            $("#terminal").text(response.responseText);
        };
        request['beforeSend'] = function() {
            $("#terminal")
                .text("Checking if the provided dot file contains a FTS...");
        };
        $.ajax(request);
    } else {
        $("#terminal").text("Model file is missing.");
    }
}

function command(event)
{
    if($("#fts")[0].files[0]) {
        request = {url: event.data.url, data: {name: $("#fts")[0].files[0].name},
            type: 'POST'};
        request['success'] = function(response){
            event.data.success(event.data.show, response);
            $("#message").text("");
        };
        request['beforeSend'] = function(response) {
            $("#terminal").text("Processing data...");
        };
        request['error'] = function(response) {
            $("#terminal").text(response.responseText);
            $("#message").text("");
        };
        $.ajax(request);
    } else {
        $("#terminal").text("Invalid file");
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
    request = {url: '/yield'};
    request['complete'] = function(response) {
        if(response) {
            $('#terminal').scrollTop(
                $('#terminal')[0].scrollHeight
            );
        }
    };
    statusCode = {};
    statusCode['206'] = function(response) {
        $("#terminal").append(response);
        if(response)
            wait = 1000;
        else
            wait = wait * 2;
        if(wait > 16000)
            wait = 4000;
        $("#message").text("Next update in "+wait/1000+" seconds.");
        setTimeout(process_update.bind(null, show, wait), wait);
    };
    statusCode['200'] = function(response) {
        $("#terminal").append(response);
        $("#message").text("");
        show_command(show);
        $("#stop").hide();
    };
    request['statusCode'] = statusCode;
    $.ajax(request);
}
