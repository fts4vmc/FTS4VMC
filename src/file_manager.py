import os
import time
import puremagic
from flask import session, request
from src.config import Config
from src.fts import app
import src.sessions as sessions
import src.internals.graph as graphviz
from src.internals.process_manager import ProcessManager
from multiprocessing import Process
from src.internals.analyser import load_dot

ALLOWED_EXTENSIONS = {'.dot'}
config = Config()

def is_fts(file_path):
    """Check if the given file_path refers to an dot file containing an FTS.
    Return True on success, False otherwise"""
    with open(file_path, 'r') as source:
        try:
            load_dot(source)
            return True
        except:
            return False

@app.route('/upload', methods=['POST'])
def upload_file():
    """This function allows file uploading while checking if the provided
    file is valid and creating necessary folders if not present"""
    payload = {}
    dot = ""
    sessions.close_session()
    sessions.new_session()
    if not os.path.exists(config.UPLOAD_FOLDER):
        os.makedirs(config.UPLOAD_FOLDER)
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
        if file:
            file_path = session['model']
            file.save(file_path)
            if not puremagic.from_file(file_path) in ALLOWED_EXTENSIONS:
                os.remove(file_path)
                return {"text":"Incompatible file format"}, 400
            if not is_fts(file_path):
                os.remove(file_path)
                return {"text":"The given file is not a FTS or contains errors"}, 400
            with open(file_path, 'r') as source:
                dot = source.read()
            graph = graphviz.Graph(dot)
            payload['mts'] = graph.get_mts()
            graph.draw_graph(session['graph'])
            payload['graph'] = dot
            payload['edges'], payload['nodes'] = graph.get_graph_number()
            payload['text'] = "Model loaded"
            return payload, 200
        else:
            return {"text": "Incompatible file format"}, 400
    return {"text": "Invalid request"}, 400

def delete_old_file(fmt, timeout, path):
    """Deletes file in the specified format older than timeout inside path

    Arguments:
    fmt -- File format to be deleted.
    timeout -- Maximum time in seconds after which file are considered
        deletable.
    path -- Path containing files to be deleted
    """
    for f in os.listdir(path):
        f = os.path.join(path, f)
        if f.split('.')[-1] == fmt:
            try:
                if os.stat(f).st_mtime + timeout < time.time():
                    os.remove(f)
            except:
                continue

def deleter():
    """Wait for 900 seconds then delete all temporary files older then
    900 seconds, forever"""
    timeout = 900
    while True:
        time.sleep(timeout)
        delete_old_file('svg', timeout, config.TMP_FOLDER)
        delete_old_file('dot', timeout, config.UPLOAD_FOLDER)
        delete_old_file('txt', timeout, config.TMP_FOLDER)
        delete_old_file('html', timeout, config.TMP_FOLDER)
        delete_old_file('dot', timeout, config.TMP_FOLDER)

def start_deleter():
    """Launch the deleter process as a daemon this ensure that the deleter
    process will end on parent process termination"""
    pm = ProcessManager.get_instance()
    thread = Process(target=deleter, daemon=True)
    pm.add_process('deleter', thread)
    pm.start_process('deleter')

def final_delete():
    """Deletes all temporary files, used on server shutdown"""
    delete_old_file('svg', 0, config.TMP_FOLDER)
    delete_old_file('dot', 0, config.UPLOAD_FOLDER)
    delete_old_file('txt', 0, config.TMP_FOLDER)
    delete_old_file('html', 0, config.TMP_FOLDER)
    delete_old_file('dot', 0, config.TMP_FOLDER)

@app.route('/download', methods=['POST'])
def download():
    """The function returns the path to the requested file

    Arguments:
    request.form['target'] -- Part of the HTTP request is used to choose
        the right file.
    request.form['main'] -- Part of the HTTP request is used to populate
        the content of the temporary file used to serve the download."""
    if not sessions.check_session():
        return {'text':"Session timed-out"}, 400

    if not ('target' in request.form and 'main' in request.form):
        return {'text':"Invalid request"}, 400

    payload = 'empty'
    mimetype = ''
    format = ''
    if(request.form['target'] == 'source'):
        payload = request.form['main']
        mimetype = 'text/plain'
        format = "model.dot"
    elif(request.form['target'] == 'summary'):
        payload = request.form['main']
        mimetype = 'text/html'
        format = "summary.html"
    elif(request.form['target'] == 'graph'):
        mime = 'image/svg+xml'
        format = "graph.svg"
        path = os.path.join('static', 'tmp', os.path.basename(session['graph']))
        if os.path.isfile(os.path.join('src', path)):
            return {"source":path, 'name':format}, 200
        else:
            return {"text":"File not found"}, 404
    elif(request.form['target'] == 'console'):
        payload = request.form['main']
        mimetype = 'text/plain'
        format="log.txt"
    else:
        return {"text":"Invalid request"}, 400

    with open(session['output']+format, 'w') as tmp:
        tmp.write(payload)
        path = os.path.join('static', 'tmp', os.path.basename(session['output']+format))
        if os.path.isfile(os.path.join('src', path)):
            return {"source":path, "name":format}, 200
        else:
            return {"text":"File not found"}, 404
