import os
import analyser
import subprocess
from flask import send_from_directory

from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'dot'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
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
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        result = subprocess.getoutput('python3 analyser.py '+ file_path)
        return result
    return 'File not found'

@app.route('/hdead_analysis', methods=['POST'])
def hdead_analyser():
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        result = subprocess.getoutput('python3 analyser.py --hdead '+ file_path)
        return result
    return 'File not found'

@app.route('/delete_model', methods=['POST'])
def delete_model():
    filename = secure_filename(request.form['name'])
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        os.remove(file_path)
    except OSError as e:  ## if failed, report it back to the user ##
        print ("Error: %s - %s." % (e.filename, e.strerror))
        return "An error occured while deleting the file model"
    else:
        return "Model file deleted"
