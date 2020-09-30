import os
import sys
import time
import pydot
from multiprocessing import Process, Queue
from src.disambiguator import Disambiguator
from src.analyser import z3_analyse_hdead, z3_analyse_full, load_dot
from src.process_manager import ProcessManager
from flask import make_response, session, send_from_directory
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.relpath("uploads")
ALLOWED_EXTENSIONS = {'dot'}

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
            os.remove(session['output']+"-output")
        except FileNotFoundError:
            pass

def full_analysis_worker(fts_file, out_file, queue):
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
    queue.put({'dead': dead, 'false': false, 'hidden': hidden})
    fts.report()
    sys.stdout.close()

def hdead_analysis_worker(fts_file, out_file, queue):
    hidden = []
    fts_source = open(fts_file, 'r')
    sys.stdout = open(out_file, 'w')
    fts = load_dot(fts_source)
    z3_analyse_hdead(fts)
    for state in fts._set_hidden_deadlock:
        hidden.append(state._id)
    queue.put({'hidden': hidden})
    fts.report()
    sys.stdout.close()

def check_session():
    pm = ProcessManager.get_instance()
    if ('timeout' in session and session['timeout'] is not None 
            and 'id' in session and pm.process_exists(session['id'])):
        if session['timeout'] > time.time():
            return True
    return False

def new_session():
    now = time.time()
    session['position'] = 0
    session['timeout'] = now+60*60
    session['output'] = os.path.join('tmp', str(now))
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
    if not check_session():
        delete_output_file()
        return make_response(('\nSession timed-out', "404"))
    pm = ProcessManager.get_instance()
    if not pm.process_exists(session['id']):
        delete_output_file()
        return make_response(('', "404"))
    else:
        with open(session['output']+"-output") as out:
            if pm.is_alive(session['id']):
                out.seek(session['position'])
                result = out.read(4096)
                session['position'] = out.tell()
                return make_response((result, "206"))
            else:
                out.seek(session['position'])
                result = out.read()
                os.remove(session['output']+"-output")
                queue = ProcessManager.get_instance().get_queue(session['id'])
                if(queue):
                    session['ambiguities'] = queue.get()
                    ProcessManager.get_instance().delete_queue(session['id'])
                return make_response((result, "200"))

@app.route('/upload', methods=['POST'])
def upload_file():
    new_session()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER);
    if not os.path.exists(os.path.dirname(session['output']+"-output")):
        os.makedirs(os.path.dirname(session['output']+"-output"))
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return make_response( 'No file part', "400")
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return make_response( 'No selected file', "400")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if(filename.split(".")[-1].lower() == "dot"):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                if(not is_fts(file_path)):
                    os.remove(file_path)
                    return make_response( "The given file is not a FTS or contains errors", "400")
                with open(file_path, 'r') as graph:
                    draw_graph(graph.read())
                return make_response( "Model loaded", "200")
        else:
            return make_response( "Incompatible file format", "400")
    return make_response( "Invalid request", "400")

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("main.html")

@app.route('/full_analysis', methods=['POST'])
def full_analyser():
    pm = ProcessManager.get_instance()
    queue = Queue()
    close_session()
    new_session()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        thread = Process(target=full_analysis_worker,
                args=[file_path, session['output']+"-output", queue])
        session['id'] = str(thread.name)
        pm.add_process(session['id'], thread)
        pm.add_queue(session['id'], queue)
        pm.start_process(session['id'])
        return "Processing data..."
    return make_response( 'File not found', "400")

@app.route('/hdead_analysis', methods=['POST'])
def hdead_analyser():
    pm = ProcessManager.get_instance()
    queue = Queue()
    close_session()
    new_session()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        thread = Process(target=hdead_analysis_worker,
                args=[file_path, session['output']+"-output", queue])
        session['id'] = str(thread.name)
        pm.add_process(key=session['id'], process=thread)
        pm.add_queue(session['id'], queue)
        pm.start_process(session['id'])
        return "Processing data..."
    return make_response( 'File not found', "400")

@app.route('/delete_model', methods=['POST'])
def delete_model():
    graph_path = session['output']+'.jpg'
    close_session()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        if os.path.isfile(graph_path):
            os.remove(graph_path)
        os.remove(file_path)
    except OSError as e:  ## if failed, report it back to the user ##
        print ("Error: %s - %s." % (e.filename, e.strerror))
        return make_response( "An error occured while deleting the file model", "400")
    else:
        return "Model file deleted"

@app.route('/stop', methods=['POST'])
def stop_process():
    close_session()
    return 'Stopped process'

@app.route('/remove_ambiguities', methods=['POST'])
def disambiguate():
    pm = ProcessManager.get_instance()
    if not check_session():
        return make_response( "No ambiguities data available execute a full analysis first", "400")
    if not session['ambiguities']:
        queue = pm.get_queue(session['id'])
        if not queue:
            return make_response( "No ambiguities data available execute a full analysis first", "400")
        else: 
            session['ambiguities'] = queue.get()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        dis = Disambiguator(file_path)
        dis.remove_transitions(session['ambiguities']['dead'])
        dis.set_true_list(session['ambiguities']['false'])
        dis.solve_hidden_deadlocks(session['ambiguities']['hidden'])
        pm.delete_queue(session['id'])
        graph = dis.get_graph()
        draw_graph(graph)
        return graph
    return make_response( 'File not found', "400")

@app.route('/remove_false_opt', methods=['POST'])
def solve_fopt():
    pm = ProcessManager.get_instance()
    if not check_session():
        return make_response( "No ambiguities data available execute a full analysis first", "400")
    if not session['ambiguities']:
        queue = pm.get_queue(session['id'])
        if not queue:
            return make_response( "No ambiguities data available execute a full analysis first", "400")
        else: 
            session['ambiguities'] = queue.get()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        dis = Disambiguator(file_path)
        dis.set_true_list(session['ambiguities']['false'])
        pm.delete_queue(session['id'])
        graph = dis.get_graph()
        draw_graph(graph)
        return graph
    return make_response( 'File not found', "400")

@app.route('/remove_dead_hidden', methods=['POST'])
def solve_hdd():
    pm = ProcessManager.get_instance()
    if not check_session():
        return make_response( "No ambiguities data available execute a full analysis first", "400")
    if not session['ambiguities']:
        queue = pm.get_queue(session['id'])
        if not queue:
            return make_response( "No ambiguities data available execute a full analysis first", "400")
        else: 
            session['ambiguities'] = queue.get()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        dis = Disambiguator(file_path)
        dis.remove_transitions(session['ambiguities']['dead'])
        dis.solve_hidden_deadlocks(session['ambiguities']['hidden'])
        pm.delete_queue(session['id'])
        graph = dis.get_graph()
        draw_graph(graph)
        return graph
    return make_response( 'File not found', "400")

def draw_graph(source):
    try:
        graph = pydot.graph_from_dot_data(source)[0]
    except:
        return
    if(len(graph.get_edges()) <= 300):
        jpg = graph.create_jpg()
        with open((session['output'])+'.jpg','wb') as output:
            output.write(jpg)

@app.route('/graph', methods=['POST'])
def get_graph():
    if check_session():
        return session['output']+'.jpg'
    else:
        make_response("No graph data available", 400)

@app.route('/img/<path:filename>')
def send_file(filename):
    print (filename)
    return send_from_directory('tmp', filename)
