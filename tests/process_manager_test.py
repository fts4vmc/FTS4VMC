import pytest
import time
from src.internals.process_manager import ProcessManager
from multiprocessing import Process, Queue

class TestProcessManager():

    def dummy():
        while True:
            time.sleep(30)

    def strong_dummy():
        import signal
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while True:
            time.sleep(30)

    @pytest.fixture
    def queue(self):
        return Queue()

    @pytest.fixture
    def process(self):
        return Process(target=self.dummy, daemon=True)

    @pytest.fixture
    def masked_proc(self):
        return Process(target=self.strong_dummy, daemon=True)

    def test_get_instance(self):
        pm1 = ProcessManager.get_instance()
        pm2 = ProcessManager.get_instance()
        assert pm1 == pm2

    def test_get_instance_error(self):
        pm1 = ProcessManager.get_instance()
        with pytest.raises(Exception, match=r"A ProcessManager instance already exists"):
            pm2 = ProcessManager()

    def test_add_process(self, process):
        pm = ProcessManager.get_instance()
        pm.add_process('add_process', process)
        assert pm.process_exists('add_process')
        
    def test_add_not_a_process(self):
        pm = ProcessManager.get_instance()
        with pytest.raises(Exception, match=r"process must be instance of"):
            pm.add_process('add_process', "NOT A PROCESS")
        
    def test_is_not_alive(self):
        pm = ProcessManager.get_instance()
        assert not pm.is_alive('add_process')

    def test_is_alive(self):
        pm = ProcessManager.get_instance()
        pm.start_process('add_process')
        assert pm.is_alive('add_process')

    def test_end_process(self):
        pm = ProcessManager.get_instance()
        pm.end_process('add_process')
        assert not (pm.is_alive('add_process') or pm.process_exists('add_process'))

    def test_kill_process(self, masked_proc):
        pm = ProcessManager.get_instance()
        pm.add_process('kill', masked_proc)
        pm.start_process('kill')
        pm.end_process('kill')
        assert not (pm.is_alive('kill') or pm.process_exists('kill'))

    def test_process_dont_exists(self):
        pm = ProcessManager.get_instance()
        assert not pm.process_exists('nothing')

    def test_end_non_existing_process(self):
        pm = ProcessManager.get_instance()
        nproc = len(pm.proc)
        pm.end_process('nothing')
        assert len(pm.proc) == nproc

    def test_add_non_existing_process(self):
        pm = ProcessManager.get_instance()
        assert not pm.process_exists('nothing')

    def test_start_non_existing_process(self):
        pm = ProcessManager.get_instance()
        with pytest.raises(KeyError, match=r'nothing'):
            pm.start_process('nothing')

    def test_add_queue(self, queue):
        pm = ProcessManager.get_instance()
        pm.add_queue('add_queue', queue)
        assert len(pm.queue) == 1

    def test_add_not_a_queue(self):
        pm = ProcessManager.get_instance()
        with pytest.raises(Exception, match=r'queue must be instance of'):
            pm.add_queue('add_queue', "NOT A QUEUE")

    def test_get_queue(self):
        pm = ProcessManager.get_instance()
        assert pm.get_queue('add_queue')

    def test_get_non_existing_queue(self):
        pm = ProcessManager.get_instance()
        assert pm.get_queue('nothing') == None

    def test_delete_queue(self):
        pm = ProcessManager.get_instance()
        pm.delete_queue('add_queue')
        assert pm.get_queue('add_queue') == None

    def test_delete_non_existing_queue(self):
        pm = ProcessManager.get_instance()
        nqueue = len(pm.queue)
        pm.delete_queue('nothing')
        assert nqueue == len(pm.queue)
