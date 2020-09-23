# # # # # # # # # # # # # #
#Test suite for src/fts.py#
# # # # # # # # # # # # # #
import pytest
import os
import shutil
import src
from flask import request

UPLOAD_FOLDER = os.path.relpath("uploads")
EXAMPLE_FILE_NAME = 'example.dot'
EXAMPLE_FILE_PATH = os.path.join('tests', EXAMPLE_FILE_NAME)
#test index
def test_index(test_client):
    ans = test_client.get('/')
    assert b'Load model' in ans.data
    assert b'Full ambiguities analysis' in ans.data
    assert b'Liveness analysis' in ans.data
    assert b'Delete model and close' in ans.data

#Upload model function
def upload_m(test_client):
    data = []
    with open(EXAMPLE_FILE_PATH,'rb') as ex_file: 
        return test_client.open('/upload',method='POST',data=dict(file=ex_file))
#Delete model function
def delete_m(test_client):
    return test_client.open('/delete_model', method='POST', data=dict(name='tests_'+ EXAMPLE_FILE_NAME))
#Analyser
def analyser(test_client,full):
    if full == True:
        return test_client.open('/full_analysis', method='POST', data=dict(name='tests_' + EXAMPLE_FILE_NAME))
    else:
        return test_client.open('/hdead_analysis', method='POST', data=dict(name='tests_' + EXAMPLE_FILE_NAME))


#Upload/Delete model test
def test_upload_delete_model(test_client):
    ans = upload_m(test_client)
    assert ans.status_code == 200
    assert os.path.exists(UPLOAD_FOLDER)
    ans = delete_m(test_client)
    assert ans.status_code == 200
    assert not os.path.exists(os.path.join(UPLOAD_FOLDER, EXAMPLE_FILE_NAME))

#full analyser
def test_full_analyser(test_client):
    ans = upload_m(test_client)
    assert ans.status_code == 200
    ans = analyser(test_client,full=True)
    assert ans.status_code == 200
    ans = delete_m(test_client)
    assert ans.status_code == 200
#hdead analyser
def test_hdead_analyser(test_client):
    ans = upload_m(test_client)
    assert ans.status_code == 200
    ans = analyser(test_client,full=False)
    assert ans.status_code == 200
    ans = delete_m(test_client)
    assert ans.status_code == 200 
