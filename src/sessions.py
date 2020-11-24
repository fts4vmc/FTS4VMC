import os
import time
import string
import random
import pathlib
from src.fts import app
from src.config import Config
from flask import session
from src.internals.process_manager import ProcessManager
import multiprocessing

config = Config()

def check_session():
    """Check if the current session is still valid by verifying if the
    timeout value is still bigger than the current time."""
    pm = ProcessManager.get_instance()
    if 'id' in session:
        lock =  pm.get_lock(session['id'])
        if lock:
            with lock:
                return ('timeout' in session and session['timeout'] is not None
                    and session['timeout'] > time.time())
    else:
        return ('timeout' in session and session['timeout'] is not None
            and session['timeout'] > time.time())

def update():
    tmp = ['output', 'graph', 'model', 'counter_graph']
    if ('timeout' in session and session['timeout'] is not None
            and session['timeout'] > time.time()):
        session['timeout'] = time.time()+900
        for target in tmp:
            if target in session and os.path.isfile(session[target]):
                try:
                    pathlib.Path(session[target]).touch()
                except FileNotFoundError:
                    continue
        return {'text':'ok'}, 200
    return {'text':'Session expired no update'}, 200

@app.route('/keep_alive', methods=['POST'])
def update_session_timeout():
    """Updates timeout for valid sessions and updates last modification
    time for existing files related to the session"""
    pm = ProcessManager.get_instance()
    if 'id' in session:
        lock =  pm.get_lock(session['id'])
        if lock:
            with lock:
                return update()
    return update()

def new_session():
    """Deletes file related to the previous session and sets value for the
    new one"""
    if 'output' in session and session['output']:
        delete_output_file(True)
    now = time.time()
    session['position'] = 0
    session['timeout'] = now+900
    session['output'] = ''.join(random.SystemRandom().choice(
                string.ascii_uppercase + string.digits) for _ in range(32))
    session['graph'] = os.path.join(config.TMP_FOLDER,
            session['output']+'.svg')
    session['counter_graph'] = os.path.join(config.TMP_FOLDER,
            session['output'] + 'counterexamplegraph.svg')
    session['model'] = os.path.join(config.UPLOAD_FOLDER,
            session['output']+'.dot')
    session['output'] = os.path.join(config.TMP_FOLDER,
            session['output']+'-output')
    session['ambiguities'] = {}

def close_session():
    """Closes a session by deleting all of its related files and by freeing
    the related session dictionary."""
    pm = ProcessManager.get_instance()
    session.pop('timeout', None)
    session.pop('position', None)
    if 'id' in session and session['id']:
        pm.end_process(session['id'])
        pm.delete_lock(session['id'])
    delete_output_file(True)
    session.pop('id', None)
    session.pop('output', None)
    session.pop('ambiguities', None)
    session.pop('graph', None)
    session.pop('counter_graph', None)
    session.pop('model', None)

def delete_output_file(complete = False):
    """Deletes output file for the current session"""
    if 'output' in session:
        files = [
                session['output'], 
                session['output']+'log.txt',
                session['output']+'summary.html', 
                session['output']+'graph.svg',
                session['output']+'model.dot',
                ]
        if complete:
            if 'graph' in session:
                files.append(session['graph'])
            if 'counter_graph' in session:
                files.append(session['counter_graph'])
            if 'model' in session:
                files.append(session['model'])
        for f in files:
            try:
                os.remove(f)
            except:
                continue
