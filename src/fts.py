import os
import pdb
import sys
import time
import subprocess
import shutil
import pydot
import string
import random
import pathlib
import time
from multiprocessing import Process, Queue
from src.disambiguator import Disambiguator
from src.analyser import z3_analyse_hdead, z3_analyse_full, load_dot
from src.process_manager import ProcessManager
from flask import make_response, session, send_from_directory
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

from src.translator import Translator

UPLOAD_FOLDER = os.path.relpath("uploads")
ALLOWED_EXTENSIONS = {'dot'}
PATH_TO_VMC = './vmc.linux-executable'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'\xb1\xa8\xc0W\x0c\xb3M\xd6\xa0\xf4\xabSmz=\x83'

def is_fts(file_path):
    """Check if the given file_path refers to an dot file containing an FTS.
    Return True on success, False otherwise"""
    with open(file_path, 'r') as source:
        try:
            load_dot(source)
            return True
        except:
            return False

def delete_output_file():
    if 'output' in session:
        try:
            os.remove(session['output'])
        except:
            pass
        try:
            os.remove(session['graph'])
        except:
            pass

def full_analysis_worker(fts_file, out_file, out_graph, queue):
    dead = [] 
    false = [] 
    hidden = []
    fts_source = open(fts_file, 'r')
    sys.stdout = open(out_file, 'w')
    fts = load_dot(fts_source)
    z3_analyse_full(fts)
    for transition in fts._set_dead:
        dead.append({'src':transition._in._id, 'dst':transition._out._id,
            'label':str(transition._label), 'constraint':str(transition._constraint)})
    for transition in fts._set_false_optional:
        false.append({'src':transition._in._id, 'dst':transition._out._id,
            'label':str(transition._label), 'constraint':str(transition._constraint)})
    for state in fts._set_hidden_deadlock:
        hidden.append(state._id)
    fts_source.seek(0,0)
    queue.put({'ambiguities':{'dead': dead, 'false': false, 'hidden': hidden}})
    fts.report()
    sys.stdout.close()
    fts_source.close()

def hdead_analysis_worker(fts_file, out_file, out_graph, queue):
    hidden = []
    fts_source = open(fts_file, 'r')
    sys.stdout = open(out_file, 'w')
    fts = load_dot(fts_source)
    z3_analyse_hdead(fts)
    for state in fts._set_hidden_deadlock:
        hidden.append(state._id)
    fts_source.seek(0,0)
    queue.put({'ambiguities':{'dead':[], 'false':[], 'hidden': hidden}})
    fts.report()
    sys.stdout.close()
    fts_source.close()

def check_session():
    if ('timeout' in session and session['timeout'] is not None 
            and session['timeout'] > time.time()):
        return True
    return False

@app.route('/keep_alive', methods=['POST'])
def update_session_timeout():
    tmp = ['output', 'graph', 'model']
    if check_session():
        session['timeout'] = time.time()+600
        for target in tmp:
            if target in session and os.path.isfile(session[target]):
                try:
                    pathlib.Path(session[target]).touch()
                except:
                    pass
    return {'text':'ok'}, 200

def new_session():
    if 'output' in session and session['output']:
        delete_output_file()
    now = time.time()
    session['position'] = 0
    session['timeout'] = now+600
    session['output'] = ''.join(random.SystemRandom().choice(
                string.ascii_uppercase + string.digits) for _ in range(32))
    session['graph'] = os.path.join('src', 'static', session['output']+'.jpg')
    session['model'] = os.path.join(UPLOAD_FOLDER, session['output']+'.dot')
    session['output'] = os.path.join('tmp', session['output']+'-output')
    session['ambiguities'] = {}

def close_session():
    pm = ProcessManager.get_instance()
    session.pop('timeout', None)
    session.pop('position', None)
    if 'id' in session and session['id']:
        pm.end_process(session['id'])
    delete_output_file()
    session.pop('id', None)
    session.pop('output', None)
    session.pop('ambiguities', None)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/yield')
def get_output():
    pm = ProcessManager.get_instance()
    if not check_session():
        delete_output_file()
        return {"text":'\nSession timed-out'}, 404
    elif not 'id' in session or not pm.process_exists(session['id']):
        delete_output_file()
        return {"text":''}, 404
    else:
        with open(session['output']) as out:
            if pm.is_alive(session['id']):
                out.seek(session['position'])
                result = out.read(4096)
                session['position'] = out.tell()
                return {"text":result}, 206
            else:
                out.seek(session['position'])
                result = out.read()
                os.remove(session['output'])
                queue = ProcessManager.get_instance().get_queue(session['id'])
                payload = {}
                payload['text'] = result
                payload['edges'], payload['nodes'] = get_graph_number(session['model'])
                if(queue):
                    tmp = queue.get()
                    session['ambiguities'] = tmp['ambiguities']
                    payload['ambiguities'] = tmp['ambiguities']
                    ProcessManager.get_instance().delete_queue(session['id'])
                    try:
                        dis = Disambiguator.from_file(session['model'])
                        payload['value'] = dis.get_graph()
                        dis.highlight_ambiguities(tmp['ambiguities']['dead'], 
                                tmp['ambiguities']['false'], 
                                tmp['ambiguities']['hidden'])
                        draw_graph(dis.get_graph())
                        return payload, 200
                    except:
                        return payload, 200
                return payload, 200

@app.route('/upload', methods=['POST'])
def upload_file():
    close_session()
    new_session()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER);
    if not os.path.exists(os.path.dirname(session['output'])):
        os.makedirs(os.path.dirname(session['output']))
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return {"text":'No file part'}, 400
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return {"text": 'No selected file'}, 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if(filename.split(".")[-1].lower() == "dot"):
                file_path = session['model']
                file.save(file_path)
                if(not is_fts(file_path)):
                    os.remove(file_path)
                    return {"text":"The given file is not a FTS or contains errors"}, 400
                with open(file_path, 'r') as graph:
                    draw_graph(graph.read())
                return {"text": "Model loaded"}, 200
        else:
            return {"text": "Incompatible file format"}, 400
    return {"text": "Invalid request"}, 400

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("main.html")

@app.route('/full_analysis', methods=['POST'])
def full_analyser():
    pm = ProcessManager.get_instance()
    queue = Queue()
    update_session_timeout()
    file_path = session['model']
    if os.path.isfile(file_path):
        thread = Process(target=full_analysis_worker,
                args=[file_path, session['output'], session['graph'], queue])
        session['id'] = str(thread.name)
        pm.add_process(session['id'], thread)
        pm.add_queue(session['id'], queue)
        pm.start_process(session['id'])
        session['position'] = 0
        return "Processing data..."
    return {"text": 'File not found'}, 400

@app.route('/hdead_analysis', methods=['POST'])
def hdead_analyser():
    pm = ProcessManager.get_instance()
    queue = Queue()
    update_session_timeout()
    file_path = session['model']
    if os.path.isfile(file_path):
        thread = Process(target=hdead_analysis_worker,
                args=[file_path, session['output'], session['graph'], queue])
        session['id'] = str(thread.name)
        pm.add_process(key=session['id'], process=thread)
        pm.add_queue(session['id'], queue)
        pm.start_process(session['id'])
        session['position'] = 0
        return "Processing data..."
    return {"text": 'File not found'}, 400

@app.route('/delete_model', methods=['POST'])
def delete_model():
    file_path = session['model']
    close_session()
    try:
        os.remove(file_path)
    except OSError as e:  ## if failed, report it back to the user ##
        print ("Error: %s - %s." % (e.filename, e.strerror))
        return {"text": "An error occured while deleting the file model"}, 400
    else:
        return {"text":"Model file deleted"}, 200

@app.route('/stop', methods=['POST'])
def stop_process():
    pm = ProcessManager.get_instance()
    session.pop('position', None)
    if 'id' in session and session['id']:
        pm.end_process(session['id'])
    delete_output_file()
    session.pop('id', None)
    session.pop('ambiguities', None)
    session.pop('ambiguities', None)
    return {"text":'Stopped process'}, 200

@app.route('/remove_ambiguities', methods=['POST'])
def disambiguate():
    pm = ProcessManager.get_instance()
    if not check_session():
        return {"text": "No ambiguities data available execute a full analysis first"}, 400
    if not session['ambiguities']:
        queue = pm.get_queue(session['id'])
        if not queue:
            return {"text": "No ambiguities data available execute a full analysis first"}, 400
        else: 
            session['ambiguities'] = queue.get()
    payload = {}
    file_path = session['model']
    if os.path.isfile(file_path):
        dis = Disambiguator.from_file(file_path)
        dis.remove_transitions(session['ambiguities']['dead'])
        dis.set_true_list(session['ambiguities']['false'])
        dis.solve_hidden_deadlocks(session['ambiguities']['hidden'])
        pm.delete_queue(session['id'])
        graph = dis.get_graph()
        payload['text'] = graph
        payload['edges'], payload['nodes'] = get_string_graph_number(graph)
        draw_graph(graph)
        return payload, 200
    return {"text": 'File not found'}, 400

@app.route('/remove_false_opt', methods=['POST'])
def solve_fopt():
    pm = ProcessManager.get_instance()
    if not check_session():
        return {"text": "No ambiguities data available execute a full analysis first"}, 400
    if not session['ambiguities']:
        queue = pm.get_queue(session['id'])
        if not queue:
            return {"text": "No ambiguities data available execute a full analysis first"}, 400
        else: 
            session['ambiguities'] = queue.get()
    payload = {}
    file_path = session['model']
    if os.path.isfile(file_path):
        dis = Disambiguator.from_file(file_path)
        dis.set_true_list(session['ambiguities']['false'])
        pm.delete_queue(session['id'])
        graph = dis.get_graph()
        payload['text'] = graph
        payload['edges'], payload['nodes'] = get_string_graph_number(graph)
        draw_graph(graph)
        return payload, 200
    return {"text": 'File not found'}, 400

@app.route('/remove_dead_hidden', methods=['POST'])
def solve_hdd():
    pm = ProcessManager.get_instance()
    if not check_session():
        return {"text": "No ambiguities data available execute a full analysis first"}, 400
    if not session['ambiguities']:
        queue = pm.get_queue(session['id'])
        if not queue:
            return {"text": "No ambiguities data available execute a full analysis first"}, 400
        else: 
            session['ambiguities'] = queue.get()
    payload = {}
    file_path = session['model']
    if os.path.isfile(file_path):
        dis = Disambiguator.from_file(file_path)
        dis.remove_transitions(session['ambiguities']['dead'])
        dis.solve_hidden_deadlocks(session['ambiguities']['hidden'])
        pm.delete_queue(session['id'])
        graph = dis.get_graph()
        payload['text'] = graph
        payload['edges'], payload['nodes'] = get_string_graph_number(graph)
        draw_graph(graph)
        return payload, 200
    return {"text": 'File not found'}, 400

@app.route('/verify_property', methods=['POST'])
def verify_property():
    pm = ProcessManager.get_instance()
    if not session['ambiguities']:
        queue = pm.get_queue(session['id'])
        if not queue:
            return make_response( "No ambiguities data available execute a full analysis first", "400")
    if not (len(session['ambiguities']['hidden']) == 0):
        return make_response("Hidden deadlocks detected. It is necessary to remove them before checking the property", "400")

    fname = secure_filename(request.form['name'])
    fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)

    actl_property = request.form['property']
    if (len(actl_property) == 0):
        return make_response('Missing property to be verified', "400")

    if os.path.isfile(fpath):
        t = Translator()
        t.load_model(fpath)
        t.translate()

        vmc_string = t.get_output()
        
        session_tmp_folder = str(session['id']) + '_tmp'
        os.mkdir(session_tmp_folder)

        session_tmp_model = session_tmp_folder + '/model.txt'
        session_tmp_properties = session_tmp_folder + '/properties.txt'

        vmc_file = open(session_tmp_model,"w+")
        vmc_file.write(vmc_string)
        vmc_file.close()
        prop_file = open(session_tmp_properties,"w+")
        prop_file.write(actl_property)
        prop_file.close()
        result = subprocess.check_output(PATH_TO_VMC + ' ' + session_tmp_model + ' '+ session_tmp_properties, shell=True)
        shutil.rmtree(session_tmp_folder)
        return result
    return make_response( 'File not found', "400")

def draw_graph(source, target=None):
    try:
        graph = pydot.graph_from_dot_data(source)[0]
    except:
        return False
    if(len(graph.get_edges()) <= 300):
        jpg = graph.create_jpg()
        if target:
            with open(os.path.join('src','static', target)+'.jpg','wb') as out:
                out.write(jpg)
                return True
        else:
            with open(session['graph'],'wb') as out:
                out.write(jpg)
                return True
    return False

@app.route('/graph', methods=['POST'])
def get_graph():
    if check_session(): 
        if os.path.isfile(session['graph']):
            return {"source":os.path.join('static', os.path.basename(session['graph']))}, 200
    return {"text":"No graph data available"}, 400

def delete_old_file(fmt, timeout, path):
    for f in os.listdir(path):
        f = os.path.join(path, f)
        if f.split('.')[-1] == fmt:
            try:
                if os.stat(f).st_mtime + timeout < time.time():
                    os.remove(f)
            except:
                pass

def deleter():
    while True:
        time.sleep(900)
        delete_old_file('jpg', 900, os.path.join('src', 'static'))
        delete_old_file('dot', 900, os.path.join('uploads'))

def start_deleter():
    pm = ProcessManager.get_instance()
    thread = Process(target=deleter)
    pm.add_process('deleter', thread)
    pm.start_process('deleter')

def get_graph_number(graph_source):
    node = list()
    try:
        graph = pydot.graph_from_dot_file(graph_source)[0]
    except:
        return 0, 0

    for edge in graph.get_edges():
        if edge.get_source() not in node:
            node.append(edge.get_source())
        if edge.get_destination() not in node:
            node.append(edge.get_destination())
    return len(graph.get_edges()), len(node)

def get_string_graph_number(graph_source):
    node = list()
    try:
        graph = pydot.graph_from_dot_data(graph_source)[0]
    except:
        return 0, 0

    for edge in graph.get_edges():
        if edge.get_source() not in node:
            node.append(edge.get_source())
        if edge.get_destination() not in node:
            node.append(edge.get_destination())
    return len(graph.get_edges()), len(node)
