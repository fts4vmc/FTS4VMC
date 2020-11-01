import pytest
import src.fts as fts

class TestDisambiguator:
    @pytest.fixture
    def client(self):
        fts.app.config['TESTING'] = True
        return fts.app.test_client()

    def test_index(self, client):
        import os
        with open(os.path.join('tests', 'main.html')) as html:
            assert client.get('/').get_data(True)+'\n' == html.read()
    
    def test_yield_no_session(self, client):
        import json
        assert client.get('/yield').get_json()['text'] == "\nSession timed-out"
