import os
import sys
import time
import analyser
import multiprocessing
from flask import make_response, session

from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'dot'}

process = {}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'\xb1\xa8\xc0W\x0c\xb3M\xd6\xa0\xf4\xabSmz=\x83'

def full_analysis_worker(fts_file, out_file):
    fts_source = open(fts_file, 'r')
    sys.stdout = open(out_file, 'w')
    fts = analyser.load_dot(fts_source)
    analyser.z3_analyse_full(fts)
    fts.report()
    sys.stdout.close()

def hdead_analysis_worker(fts_file, out_file):
    fts_source = open(fts_file, 'r')
    sys.stdout = open(out_file, 'w')
    fts = analyser.load_dot(fts_source)
    analyser.z3_analyse_hdead(fts)
    fts.report()
    sys.stdout.close()

def check_session():
    global process
    if 'timeout' in session and session['timeout'] is not None and session['id'] in process:
        if session['timeout'] > time.time():
            return True
    return False

def new_session():
    now = time.time()
    session['position'] = 0
    session['timeout'] = now+60*60
    session['output'] = '/tmp/' + str(now) + '-output'

def close_session():
    global process
    session.pop('timeout', None)
    session.pop('position', None)
    if 'id' in session and session['id'] and session['id'] in process:
        process[session['id']].terminate()
        process[session['id']].join(1)
        # Subprocess won't end or exited on error
        if(process[session['id']].is_alive() or 
                process[session['id']].exitcode != 0):
            process[session['id']].kill()
        process[session['id']].close()
        process.pop(session['id'], None)
    if 'output' in session:
        try:
            os.remove(session['output'])
        except FileNotFoundError:
            pass
    session.pop('id', None)
    session.pop('output', None)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/yield')
def get_output():
    if not check_session():
        return make_response(('\nSession timed-out', "200"))
    global process
    if process[session['id']] is None:
        return make_response(('', "200"))
    else:
        with open(session['output']) as out:
            if process[session['id']].is_alive():
                out.seek(session['position'])
                result = out.read(4096)
                session['position'] = out.tell()
                return make_response((result, "206"))
            else:
                out.seek(session['position'])
                result = out.read()
                close_session()
                return make_response((result, "200"))

@app.route('/upload', methods=['POST'])
def upload_file():
    new_session()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER);
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return "Model loaded"
    return "Invalid request"

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("main.html")

@app.route('/full_analysis', methods=['POST'])
def full_analyser():
    global process
    close_session()
    new_session()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        thread = multiprocessing.Process(target=full_analysis_worker,
                args=[file_path, session['output']])
        session['id'] = thread.name
        process[session['id']] = thread
        thread.start()
        return "Processing data..."
    return 'File not found'

@app.route('/hdead_analysis', methods=['POST'])
def hdead_analyser():
    global process
    close_session()
    new_session()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        thread = multiprocessing.Process(target=hdead_analysis_worker,
                args=[file_path, session['output']])
        session['id'] = thread.name
        process[session['id']] = thread
        thread.start()
        return "Processing data..."
    return 'File not found'

@app.route('/delete_model', methods=['POST'])
def delete_model():
    close_session()
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        os.remove(file_path)
    except OSError as e:  ## if failed, report it back to the user ##
        print ("Error: %s - %s." % (e.filename, e.strerror))
        return "An error occured while deleting the file model"
    else:
        return "Model file deleted"

@app.route('/stop', methods=['POST'])
def stop_process():
    close_session()
    return 'Stopped process'
