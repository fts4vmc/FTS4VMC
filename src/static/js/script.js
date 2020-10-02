$(function(){
    $("#fts").prop("disabled", false);
    $("#load").prop("disabled", false);
    $("main").on("click", "#graph_tab", show_graph);
    $("main").on("click", "#terminal_tab", show_terminal);
    $("aside").on("change", "#fts", alter_title);
    $("aside").on("click", "#load", upload_file);
    $("aside").on("click", "#full", 
        {url: '/full_analysis', success:timed_update_textarea, 
            show:[
                $("#disambiguate"), $("#fopt"), $("#hdd"), 
                $("#full"), $("#hdead"), $("#delete"), $("#stop"),
                $("#fts")
            ]
        }, command);

    $("aside").on("click", "#hdead", 
        {url: '/hdead_analysis', success:timed_update_textarea, 
            show:[$("#full"), $("#hdead"), $("#delete"),
              $("#stop"), $("#load"), $("#fts")] 
        }, command);

    $("aside").on("click", "#delete", 
        {url: '/delete_model', success:update_textarea,
          show: [$("#load"), $("#fts")]}, command);
    $("aside").on("click", "#stop", 
        {url: '/stop', success:update_textarea, 
            show:[
              $("#full"), $("#hdead"), 
              $("#delete"), $("#load"), $("#fts")
            ]
        }, command);
    $("aside").on("click", "#disambiguate", 
        {url: '/remove_ambiguities', success:update_textarea}, command);
    $("aside").on("click", "#fopt", 
        {url: '/remove_false_opt', success:update_textarea}, command);
    $("aside").on("click", "#hdd", 
        {url: '/remove_dead_hidden', success:update_textarea}, command);
}); 

function show_terminal()
{
    $("#image").hide();
    $("#terminal").slideDown();
}

function show_graph()
{
    request = {url:'/graph', type:'POST'};
    request['success'] = function(response)
    {
        $("#image").attr('src', response['source']);
    };
    request['error'] = function(response)
    {
        $("#message").text(response['text']);
    };
    $.ajax(request);
    $("#terminal").hide();
    $("#image").slideDown();
}

function alter_title() 
{
    let name = $("#fts").val().replace(/.*[\/\\]/, '');
    $("main > h2").text("Analysis of "+name);
    $("#terminal").text(name+" selected, click load model to"+
        " upload the file");
    $(".command").prop("disabled", true);
    $("#fts").prop("disabled", false);
    $("#load").prop("disabled", false);
}

function show_command(show)
{
    if(show) {
        $(".command").prop("disabled", true);
        for (element of show) {
            element.prop("disabled", false);
        }
    }
}

//Updates the main's textarea with the response value.
function update_textarea(show, response)
{
    $("#terminal").text(response['text']);
    show_command(show);
}

//Updates the main's textarea with the response value.
function update_textarea_graph()
{
}

//Updates the main's textarea with the response value,
//and initiates the polling of process output.
function timed_update_textarea(show, response)
{
    $("#terminal").text(response['text']);
    $(".command").prop("disabled", true);
    $("#stop").prop("disabled", false);
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
            $("#terminal").text(response['text']);
            $("#full").prop("disabled", false);
            $("#hdead").prop("disabled", false);
            $("#delete").prop("disabled", false);
        };
        request['error'] = function(response) {
            $("#terminal").text(response['text']);
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
            $("#terminal").text(response['text']);
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
        $("#terminal").append(response['text']);
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
        $("#terminal").append(response['text']);
        $("#message").text("");
        show_command(show);
        $("#stop").prop("disabled", true);
    };
    request['statusCode'] = statusCode;
    $.ajax(request);
}
