$(function(){
    $(window).on("beforeunload", {url: '/delete_model', success:update_textarea,
          show: [$("#load"), $("#fts")]}, command);
    $("#fts").prop("disabled", false);
    $("#load").prop("disabled", false);
    $("main").on("click", "#graph_tab", show_graph);
    $("main").on("click", "#console_tab", show_console);
    $("main").on("click", "#summary_tab", show_summary);
    $("main").on("click", "#source_tab", show_source);
    $("aside").on("change", "#fts", alter_title);
    $("aside").on("click", "#load", upload_file);
    $("aside").on("click", "#mts", load_mts);
    $("aside").on("click", "#download", download);
    $("aside").on("click", "#full", 
        {url: '/full_analysis', success:timed_update_textarea, 
            show:[
                $("#disambiguate"), $("#fopt"), $("#hdd"), 
                $("#full"), $("#hdead"), $("#delete"), $("#stop"),
                $("#fts"), $("#verify_properties"), $("#mts"), $("#download")
            ]
        }, command);

    $("aside").on("click", "#hdead", 
        {url: '/hdead_analysis', success:timed_update_textarea, 
            show:[$("#full"), $("#hdead"), $("#delete"), $("#mts"),
              $("#stop"), $("#download"), $("#fts"), $("#verify_properties")] 
        }, command);

    $("aside").on("click", "#delete", 
        {url: '/delete_model', success:update_textarea,
          show: [$("#load"), $("#fts")]}, command);
    $("aside").on("click", "#stop", 
        {url: '/stop', success:update_textarea, 
            show:[
              $("#full"), $("#hdead"), $("#mts"),
              $("#delete"), $("#fts"), $("#download")
            ]
        }, command);
    $("aside").on("click", "#disambiguate", 
        {url: '/remove_ambiguities', success:update_textarea_graph}, command);
    $("aside").on("click", "#fopt", 
        {url: '/remove_false_opt', success:update_textarea_graph}, command);
    $("aside").on("click", "#hdd", 
        {url: '/remove_dead_hidden', success:update_textarea_graph, show:[
                $("#disambiguate"), $("#fopt"), $("#hdd"), 
                $("#full"), $("#hdead"), $("#delete"), $("#stop"),
                $("#fts"), $("#verify_properties"), $("#mts"), $("#property_text_area")]}, command);
    $("aside").on("click", "#verify_properties", verify_property);
    $("aside").on("click", "#show_explanation", show_explanation);
    keep_alive();
}); 

function load_mts()
{
  tmp = $("#tmp-source").val();
  $("#tmp-source").val($("#source").text())
  $("#source").text(tmp);
  if($("#tmp-source").attr('name') == "MTS") {
    $("#mts").text("View featured transition system");
    $("#tmp-source").attr('name', 'FTS')
  } else {
    $("#mts").text("View modal transition system");
    $("#tmp-source").attr('name', 'MTS')
  }
  request = {url:'/reload_graph', type:'POST'};
  request['success'] = load_graph;
  request['data'] = {'src': tmp};
  request['error'] = function(resp)
  {
      if(resp.responseJSON) {
          $("#image-div > p").text(resp.responseJSON['text']);
      }
      $("#image").attr('src', '');
  };
  $.ajax(request);
}

function show_console()
{
    $("#image-div *").hide();
    $("#legend").hide();
    $("#summary").hide();
    $(".source").hide();
    $(".console").show();
}

function show_summary()
{
    $("#image-div *").hide();
    $("#legend").hide();
    $(".console").hide();
    $(".source").hide();
    $("#summary").show();
}

function show_source()
{
    $("#image-div *").hide();
    $("#legend").hide();
    $(".console").hide();
    $("#summary").hide();
    $(".source").show();
}

function update_textarea_graph(show, response)
{
    $("#console").text(response['text']);
    show_command(show);
    create_summary($("#summary"), response)
    request = {url:'/graph', type:'POST'};
    request['success'] = load_graph;
    request['error'] = function(resp)
    {
        if(resp.responseJSON) {
            $("#image-div > p").text(resp.responseJSON['text']);
        }
        $("#image").attr('src', '');
    };
    $.ajax(request);
}

function load_graph(response)
{
    $("#image").attr('src', '');
    $("#image").attr('src', response['source']+"?random="+new Date().getTime());
    $("#image-div > p").text('').hide();
}

function show_graph()
{
    request = {url:'/graph', type:'POST'};
    request['success'] = load_graph;
    request['error'] = function(response)
    {
        $("#image-div > p").text(response.responseJSON['text']).show();
        $("#image").attr('src', '');
    };
    $.ajax(request);
    $(".console").hide();
    $("#summary").hide();
    $(".source").hide();
    $("#legend").show();
    $("#image").show();
}

function alter_title() 
{
    let name = $("#fts").val().replace(/.*[\/\\]/, '');
    $("main > h2").text("Analysis of "+name);
    $("#console").text(name+" selected, click load model to"+
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
    $("#console").text(response['text']);
    show_command(show);
    create_summary($("#summary"), response)
}

//Updates the main's textarea with the response value,
//and initiates the polling of process output.
function timed_update_textarea(show, response)
{
    $("#console").text(response['text']);
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
        };
        request['error'] = function(response) {
            $("#console").text(response.responseJSON['text']);
        };
        request['beforeSend'] = function() {
            $("#console")
                .text("Checking if the provided dot file contains a FTS...");
        };
        $.ajax(request);
    } else {
        $("#console").text("Model file is missing.");
    }
}

function command(event)
{
    if($("#fts")[0].files[0]) {
        request = {url: event.data.url, data: {name: $("#fts")[0].files[0].name},
            type: 'POST'};
        request['success'] = function(response){
            event.data.success(event.data.show, response);
            $("#mts").text("View modal transition system");
            $("#tmp-source").attr('name', 'MTS');
            if(response['graph']) {
                $("#source").text(response['graph']);
                $("#tmp-source").val(response['mts']);
            }
            $("#message").text("");
        };
        request['beforeSend'] = function(response) {
            show_console();
            $("#console").text("Processing data...");
        };
        request['error'] = function(response) {
            if(response.responseJSON) {
                $("#console").text(response.responseJSON['text']);
            }
            $("#message").text("");
        };
        $.ajax(request);
    } else {
        $("#console").text("Invalid file");
    }
}

// Requests data at /yield to append inside the textarea,
// if the received status code is 206 (partial content) and response
// contains some data waits 1000 ms before requesting data again otherwise
// double wait value and waits 'wait'ms before requesting data again.
// If the received status code is 200 appends the data inside the textarea.
// On completed request scrolls to the bottom of the textarea to emulate
// console behaviour.
function process_update(show, wait)
{
    request = {url: '/yield'};
    request['complete'] = function(response) {
        if(response) {
            $('#console').scrollTop(
                $('#console')[0].scrollHeight
            );
        }
    };
    statusCode = {};
    statusCode['206'] = function(response) {
        $("#console").append(response['text']);
        if(response['text'])
            wait = 1000;
        else
            wait = wait * 2;
        if(wait > 16000)
            wait = 4000;
        if(wait > 1000)
            $("#message").text("Next update in "+wait/1000+" seconds.").show().fadeOut(1000);
        setTimeout(process_update.bind(null, show, wait), wait);
    };
    statusCode['200'] = function(resp) {
        $("#console").append(resp['text']);
        $("#source").text(resp['graph']);
        $("#tmp-source").val(resp['mts']);
        $("#mts").text("View modal transition system");
        $("#tmp-source").attr('name', 'MTS');
        create_summary($("#summary"), resp)
        $("#message").text("");
        show_command(show);
        req = {url:'/graph', type:'POST'};
        req['success'] = load_graph;
        req['error'] = function(resp)
        {
          $("#image-div > p").text(resp.responseJSON['text']);
          $("#image").attr('src', '');
        };
        $.ajax(req);
        $("#stop").prop("disabled", true);
    };
    request['statusCode'] = statusCode;
    $.ajax(request);
}

function keep_alive()
{
    request = {url: '/keep_alive', type:'POST'};
    $.ajax(request);
    setTimeout(keep_alive.bind(null), 300000);
}

function create_summary(target, data)
{
  target.empty();
  main = $("<div></div>");
  target.append(main);
  if(data['nodes']){
    main.append("<p>Number of nodes: "+data['nodes']+"</p>");
  }
  if(data['edges']){
    main.append("<p>Number of edges: "+data['edges']+"</p>");
  }
  if(data['ambiguities']){
    main.append("<h3>Ambiguities found</h3>");
    if(data['ambiguities']['dead']){
      main.append("<h4>Dead transition</h4>");
      list = $("<ul></ul>");
      main.append(list);
      for (transition of data['ambiguities']['dead']) {
        list.append("<li>("+transition.src+", "+transition.dst+"): "+
          transition.label+" | "+transition.constraint+"</li>");
      }
    }
    if(data['ambiguities']['false']){
      main.append("<h4>False optional</h4>");
      list = $("<ul></ul>");
      main.append(list);
      for (transition of data['ambiguities']['false']) {
        list.append("<li>("+transition.src+", "+transition.dst+"): "+
          transition.label+" | "+transition.constraint+"</li>");
      }
    }
    if(data['ambiguities']['hidden']){
      main.append("<h4>Hidden deadlock</h4>");
      list = $("<ul></ul>");
      main.append(list);
      for (state of data['ambiguities']['hidden']) {
        list.append("<li>"+state+"</li>");
      }
    }
  }
}

function verify_property()
{
    if($("#fts")[0].files[0]) {
        var prop = $("#property_text_area").val();
        request = {url: 'verify_property', data: {name: $("#fts")[0].files[0].name, property: prop},
            type: 'POST'};
        request['success'] = function(response){
            $("#show_explanation").prop("disabled", false);
            $("#console").text(response['text']);
        };
        request['beforeSend'] = function(response) {
            show_console();
            $("#console").text("Processing data...");
        };
        request['error'] = function(response) {
            $("#console").text(response['text']);
        };
        $.ajax(request);
    } else {
        $("#console").text("Invalid file");
    }
}

function download()
{
  request = {url:'/download', type:'POST'};
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
  $.ajax(request);
}

function show_explanation()
{
    $("#console").text('debug');
    request = {url: 'explanation', data:{msg: 'show_exp'} ,type: 'POST'};
    
    request['success'] = function(response){
        $("#console").text(response['text']);
    };
    request['error'] = function(response) {
        $("#console").text(response['text']);
    }
    $.ajax(request);
}
