# # # # # # # # # # # # # # # # # # # # #
#Configuration file containing fixtures #
# # # # # # # # # # # # # # # # # # # # #
import pytest
import os
from flask import Flask
from src import fts

UPLOAD_FOLDER = os.path.relpath("uploads")

"""@pytest.fixture
def test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    yield app"""

#Create test client
@pytest.fixture
def test_client():
    fts.app.config['TESTING'] = True
    fts.app.testing = True
    fts.app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    yield fts.app.test_client()

