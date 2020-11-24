import pytest
import os
import time
from flask import session
from src.fts import app
import src.sessions as sessions

class TestSessions():

    def test_check_session(self):
        with app.test_request_context():
            session['timeout'] = time.time()+600
            assert sessions.check_session()
        
    def test_check_expired_session(self):
        with app.test_request_context():
            session['timeout'] = time.time() -1
            assert not sessions.check_session()
            
    def test_check_session_undefined_timeout(self):
        with app.test_request_context():
            session['timeout'] = None
            assert not sessions.check_session()
            
    def test_check_session_undefined(self):
        with app.test_request_context():
            assert not sessions.check_session()

    def test_update_expired_session(self, tmp_path):
        with app.test_request_context():
            sessions.config.UPLOAD_FOLDER = tmp_path
            sessions.config.TMP_FOLDER= tmp_path
            sessions.new_session()
            session['timeout'] = time.time() -1
            print (os.listdir(tmp_path))
            assert len(os.listdir(tmp_path)) == 0

    def test_update_session_no_file(self, tmp_path):
        with app.test_request_context():
            sessions.config.UPLOAD_FOLDER = tmp_path
            sessions.config.TMP_FOLDER= tmp_path
            sessions.new_session()
            print (os.listdir(tmp_path))
            assert len(os.listdir(tmp_path)) == 0

    def test_update_session(self, tmp_path):
        from pathlib import Path
        tmp = ['output', 'graph', 'model', 'counter_graph']
        with app.test_request_context():
            sessions.config.UPLOAD_FOLDER = tmp_path
            sessions.config.TMP_FOLDER= tmp_path
            sessions.new_session()
            for target in tmp:
                Path(session[target]).touch()
            print (os.listdir(tmp_path))
            assert len(os.listdir(tmp_path)) == 4

    def test_close_session(self, tmp_path):
        from pathlib import Path
        tmp = ['output', 'graph', 'model', 'counter_graph']
        with app.test_request_context():
            sessions.config.UPLOAD_FOLDER = tmp_path
            sessions.config.TMP_FOLDER= tmp_path
            sessions.new_session()
            session['model'] = os.path.join(tmp_path, 'test.dot')
            session['graph'] = os.path.join(tmp_path, 'test.svg')
            session['counter_graph'] = os.path.join(tmp_path, 'counter_test.svg')
            for target in tmp:
                Path(session[target]).touch()
            sessions.close_session()
            print (session)
            print (os.listdir(tmp_path))
            assert len(os.listdir(tmp_path)) == 0 and len(session) == 0
