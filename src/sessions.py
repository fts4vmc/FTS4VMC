import os
import time
import string
import random
import pathlib
from src.fts import app
from flask import session
from src.internals.process_manager import ProcessManager

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
    session['graph'] = os.path.join('src', 'static', session['output']+'.svg')
    session['model'] = os.path.join(app.config['UPLOAD_FOLDER'], session['output']+'.dot')
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

def delete_output_file():
    if 'output' in session:
        files = [session['output'], session['output']+'log.txt',
                session['output']+'summary.html', session['output']+'graph.svg',
                session['output']+'model.dot']
        for f in files:
            try:
                os.remove(f)
            except:
                pass
        try:
            os.remove(session['graph'])
        except:
            pass
