"use strict";
$(function(){
    var hdead_show = [ $("#full"), $("#hdead"), $("#delete"), $("#mts"),
        $("#stop"), $("#download"), $("#fts"), $("#verify_properties"),
        $("#property_text_area"), $("#disambiguate")
    ];
    var full_show = [$("#disambiguate"), $("#fopt"), $("#hdd"), 
        $("#full"), $("#hdead"), $("#delete"), $("#stop"),
        $("#fts"), $("#verify_properties"), $("#mts"), $("#download"),
        $("#property_text_area")
    ];
    var stop_show = [$("#full"), $("#hdead"), $("#mts"),
        $("#delete"), $("#fts"), $("#download")];
    if(!window.location.pathname.endsWith('/'))
        window.history.pushState("", "FTS4VMC", window.location.pathname.concat('/'));
    $(window).on("beforeunload", {url: '/delete_model', success:delete_textarea,
          show: [$("#load"), $("#fts")]}, command);
    $("#fts").prop("disabled", false);
    $("#load").prop("disabled", false);
    $("main").on("click", "#graph_tab", show_graph);
    $("main").on("click", "#console_tab", {target: ".console"}, show_tab);
    $("main").on("click", "#summary_tab", {target: "#summary"}, show_tab);
    $("main").on("click", "#source_tab", {target: ".source"}, show_tab);
    $("main").on("click", "#counter_graph_tab", show_counter_graph);
    $("aside").on("click", "#mts", load_mts);
    $("aside").on("click", "#full", {url: '/full_analysis', 
        success:timed_update_textarea, show:full_show}, command);
    $("aside").on("click", "#hdead", {url: '/hdead_analysis',
        success:timed_update_textarea, show:hdead_show}, modal_command);
    $("aside").on("click", "#delete", 
        {url: '/delete_model', success:delete_textarea,
          show: [$("#load"), $("#fts")]}, command);
    $("aside").on("click", "#stop", {url: '/stop', success:update_textarea, 
        show:stop_show}, command);
    $("aside").on("click", "#disambiguate", {url: '/remove_ambiguities', 
        name:'all', success:update_textarea_graph}, solve);
    $("aside").on("click", "#fopt", {url: '/remove_false_opt', name:'fopt', 
        success:update_textarea_graph},solve);
    $("aside").on("click", "#hdd", 
        {url: '/remove_dead_hidden', name:'hdd', success:update_textarea_graph}, 
        solve);
    $("aside").on("click", "#verify_properties", verify_property);
    $("aside").on("click", "#show_explanation", show_counter_graph);
    $("aside").on("click", "#apply", apply_transform);
    $("body").on("click", "#mconfirm", {url: '/hdead_analysis', 
      success:timed_update_textarea, show:hdead_show}, command);
    $("body").on("click", "#mcancel", function() { $("#modal").hide();});
    keep_alive();
}); 

function load_mts()
{
  var tmp = $("#tmp-source").val();
  $("#tmp-source").val($("#source").text())
  $("#source").text(tmp);
  if($("main > h3").text() == 'FTS')
    $("main > h3").text('MTS');
  else if($("main > h3").text() == 'MTS')
    $("main > h3").text('FTS');
  if($("#tmp-source").attr('name') == "MTS") {
    $("#mts").text("View featured transition system");
    $("#tmp-source").attr('name', 'FTS')
  } else {
    $("#mts").text("View modal transition system");
    $("#tmp-source").attr('name', 'MTS')
  }
  var request = {url:full_url('/graph'), type:'POST'};
  request['success'] = show_graph;
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

function show_tab(target)
{
    $(".hideme").hide();
    if(target && target.data && target.data.target) {
      target = target.data.target;
    }
    $(target).show();
}

function delete_textarea(show, response)
{
  $("main > h2").text("FTS4VMC");
  update_textarea(show, response);
  $("#fts-label").removeClass("fts-label-disabled").addClass("command");
}

function update_textarea_graph(show, response)
{
  update_textarea(show, response, true);
}

//Updates the main's textarea with the response value.
function update_textarea(show, response, graph=false)
{
    $("#console").text(response['text']);
    show_command(show);
    create_summary($("#summary"), response)
    if(graph) {
      var request = {url:full_url('/graph'), type:'POST'};
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
}

function load_graph(response)
{
    if(response['source'])
      $("#image").attr('src', response['source']+"?random="+new Date().getTime());
    $("#image-div > p").text('').hide();
}

function show_graph()
{
    var request = {url:full_url('/graph'), type:'POST'};
    request['success'] = load_graph;
    request['error'] = function(response)
    {
        $("#image-div > p").text(response.responseJSON['text']).show();
        $("#image").attr('src', '');
    };
    $.ajax(request);
    $(".hideme").hide();
    $("#legend").show();
    $("#image").show();
}

function show_command(show)
{
    if(show) {
        $(".operation").prop("disabled", true);
        for (var element of show) {
            element.prop("disabled", false);
        }
    }
}


//Updates the main's textarea with the response value,
//and initiates the polling of process output.
function timed_update_textarea(show, response)
{
    $("#console").text(response['text']);
    $(".operation").prop("disabled", true);
    $("#stop").prop("disabled", false);
    process_update(show, 1000);
}

function modal_command(event)
{
    if(!$("#disambiguate").prop('disabled') && 
        !$('#fopt').prop('disabled') &&
        !$("#hdd").prop('disabled') && $("#modal").is(":hidden")){
        $("#modal").show();
        return;
    } else {
      command(event);
    }
}

function command(event)
{
    $("main > h3").text('FTS')
    if($("#fts")[0].files[0]) {
        var request = {url: full_url(event.data.url), data: {
          name: $("#fts")[0].files[0].name}, type: 'POST'};
        request['success'] = function(response){
            event.data.success(event.data.show, response);
            $("#mts").text("View modal transition system");
            $("#tmp-source").attr('name', 'MTS');
            if(response['graph']) {
                $("#source").text(response['graph']);
                $("#tmp-source").val(response['mts']);
            }
            $("#message").text("");
            $("#modal").hide();
        };
        request['beforeSend'] = function(response) {
            show_tab(".console");
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

function solve(event)
{
    $("main > h3").text('FTS');
    var request = {};
    request['url'] = full_url(event.data.url);
    request['type'] = 'POST';
    request['success'] = function(response){
        update_textarea_graph(event.data.show, response);
        $("#apply").prop('disabled', false);
        $("#apply").attr('value', event.data.name);
        $("#mts").text("View modal transition system");
        $("#tmp-source").attr('name', 'MTS');
        if(response['graph']) {
            $("#source").text(response['graph']);
            $("#tmp-source").val(response['mts']);
        }
        $("#message").text("");
        $("#modal").hide();
    };
    request['beforeSend'] = function(response) {
        show_tab(".console");
        $("#console").text("Processing data...");
    };
    request['error'] = function(response) {
        if(response.responseJSON) {
            $("#console").text(response.responseJSON['text']);
        }
        $("#message").text("");
    };
    $.ajax(request);
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
    var request = {url: full_url('/yield')};
    var statusCode = {};
    request['complete'] = function(response) {
        if(response) {
            $('#console').scrollTop(
                $('#console')[0].scrollHeight
            );
        }
    };
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
        $("main > h3").text('FTS')
        $("#console").append(resp['text']);
        $("#source").text(resp['graph']);
        $("#tmp-source").val(resp['mts']);
        $("#mts").text("View modal transition system");
        $("#tmp-source").attr('name', 'MTS');
        create_summary($("#summary"), resp)
        $("#message").text("");
        show_command(show);
        var req = {url:full_url('/graph'), type:'POST'};
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
    var request = {url: full_url('/keep_alive'), type:'POST'};
    $.ajax(request);
    setTimeout(keep_alive.bind(null), 300000);
}

function create_summary(target, data)
{
  target.empty();
  var main = $("<div></div>");
  target.append(main);
  if(data['nodes']){
    main.append("<p>Number of states: "+data['nodes']+"</p>");
  }
  if(data['edges']){
    main.append("<p>Number of transitions: "+data['edges']+"</p>");
  }
  if(data['ambiguities']){
    main.append("<h3>Ambiguities found</h3>");
    if(data['ambiguities']['hidden'] && data['ambiguities']['hidden'].length > 0){
      main.append("<h4>Hidden deadlock states</h4>");
      var list = $("<ul></ul>");
      main.append(list);
      for (var state of data['ambiguities']['hidden']) {
        list.append("<li>"+state+"</li>");
      }
    }
    if(data['ambiguities']['dead'] && data['ambiguities']['dead'].length > 0){
      main.append("<h4>Dead transitions</h4>");
      var dead = $("<table></table>");
      dead.append("<tr><th>Source state</th><th>Destination state</th>"+
        "<th>Label</th><th>Feature expression</th></tr>");
      main.append(dead);
      for (var transition of data['ambiguities']['dead']) {
        dead.append("<tr><td>"+transition.src+"</td><td>"+transition.dst+"</td>"+
          "<td>"+transition.label+"</td><td>"+transition.constraint+"</td></tr>");
      }
    }
    if(data['ambiguities']['false'] && data['ambiguities']['false'].length > 0){
      main.append("<h4>False optional transitions</h4>");
      var fopt = $("<table></table>");
      main.append(fopt);
      fopt.append("<tr><th>Source state</th><th>Destination state</th>"+
        "<th>Label</th><th>Feature expression</th></tr>");
      for (var transition of data['ambiguities']['false']) {
        fopt.append("<tr><td>"+transition.src+"</td><td>"+transition.dst+"</td>"+
          "<td>"+transition.label+"</td><td>"+transition.constraint+"</td></tr>");
      }
    }
  }
}

function verify_property()
{
    var prop = $("#property_text_area").val();
    var request = {url: full_url('/verify_property'), data: {property: prop},
        type: 'POST'};
    request['success'] = function(response){
        $("#console").text(response['formula']+":"+response['eval']+" "+
          response['details'])
        $("#vmc_formula").text(response['formula']);
        $("#vmc_eval").text(response['eval']);
        if(response['eval'] == "TRUE"){
            $("#vmc_eval").css("color","green");
            $("#vmc_formula").css("background-color","lightgreen");
            $("#vmc_details").css("background-color","lightgreen");
            $("#show_explanation").prop("disabled", true);
            $("#counter_graph_tab").prop("disabled", true);
        }
        else if(response['eval'] == "FALSE"){
            $("#vmc_eval").css("color","red");
            $("#vmc_formula").css("background-color","lightpink");
            $("#vmc_details").css("background-color","lightpink");
            $("#show_explanation").prop("disabled", false);
        }
        else{
            $("#vmc_eval").css("color","purple");
            $("#vmc_formula").css("background-color","plum");
            $("#vmc_details").css("background-color","plum");
            $("#show_explanation").prop("disabled", true);
            $("#counter_graph_tab").prop("disabled", true);
        }
        $("#vmc_details").text(response['details']);
        $(".hideme").hide();
        $("#evaluation_display").show();
    };
    request['beforeSend'] = function(response) {
        show_tab(".console");
        $("#console").text("Processing data...");
    };
    request['error'] = function(response) {
        $("#console").text(response.responseJSON['text']);
    };
    $.ajax(request);
}

function apply_transform()
{
    $("main > h3").text('FTS')
    var request = {};
    if($("#apply").attr('value') == 'all')
      request['url'] = full_url('/apply_all');
    else if($("#apply").attr('value') == 'fopt')
      request['url'] = full_url('/apply_fopt');
    else if($("#apply").attr('value') == 'hdd')
      request['url'] = full_url('/apply_hdd');
    else
      return;
    request['type'] = 'POST';
    request['success'] = function(response){
      $("#console").text(response['text']);
      $("#apply").prop('disabled', true);
    };
    request['error'] = function(response) {
      $("#console").text(response.responseJSON['text']);
    }
    $.ajax(request);
}

function full_url(url)
{
  if(url) {
    if(window.location.pathname != '/')
      if(window.location.pathname.endsWith('/'))
        return window.location.pathname.substring(0, window.location.pathname.length-1) + url;
      else
        return window.location.pathname + url;
    else
      return url;
  }
}

function load_counter_graph(response)
{
  $("#counter_graph_tab").prop("disabled", false);
  if(response['graph']) {
    $("#counter-div > p").text(response['text']).show();
    $("#counter_image").attr('src', response['graph']+"?random="+new Date().getTime()).show();
  }
  else if(response['text'] && !response['graph']) {
    $("#counter-div > p").text(response['text']).show();
    $("#counter_image").hide();
  }
  else if(response['explanation']) {
    $("#counter_image").hide();
    $("#counter-div > p").text('');
    for(var line in response['explanation']){
      $("#counter-div > p").append(response['explanation'][line]+'<br>');
    }
    $("#counter-div > p").show();
  }
}

function show_counter_graph()
{
    var request = {url:full_url('/counter_graph'), type:'POST'};
    request['data'] = {};
    request['data']['property'] = $("#property_text_area").val();
    request['success'] = load_counter_graph;
    request['error'] = function(response)
    {
        $("#counter-div > p").text(response.responseJSON['text']).show();
        $("#counter_image").attr('src', '').hide();
    };
    $.ajax(request);
    $(".hideme").hide();
}
