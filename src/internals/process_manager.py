import multiprocessing

class ProcessManager:
    """
    The ProcessManager class provides methods to manage subprocesses and queues
    used to communicate with them, it is a Singleton class.
    It is used to retrieve previously defined processes without the need of
    serialize them.
    """
    __instance = None

    @staticmethod
    def get_instance():
        """Static method used to get a ProcessManager object,
        if no ProcessManager object exists it creates a new one,
        returns always a ProcessManager object.
        """
        if ProcessManager.__instance == None:
            return ProcessManager()
        else:
            return ProcessManager.__instance

    def __init__(self):
        if ProcessManager.__instance != None:
            raise Exception("A ProcessManager instance already exists")
        else:
            ProcessManager.__instance = self
            self.proc = {}
            self.queue = {}

    def add_process(self, key, process):
        """Given a string key, and a multiprocessing.Process process,
        it adds the process inside the proc dictionary"""
        if isinstance(process, multiprocessing.Process):
            self.proc[key] = process
        else:
            raise Exception("process must be instance of multiprocessing.Process")

    def process_exists(self, key):
        """Returns True if the given key is present inside the proc dictionary,
        False otherwise"""
        return key in self.proc

    def is_alive(self, key):
        """Returns True if the process associated with key is still running,
        False otherwise"""
        if key in self.proc:
            return self.proc[key].is_alive()
        else:
            return False

    def start_process(self, key):
        """Start the process associated with key"""
        self.proc[key].start()

    def end_process(self, key):
        """Terminate the process associated with the given key value"""
        if key in self.proc:
            self.proc[key].terminate()
            self.proc[key].join(1)
            # Subprocess won't end or exited on error
            if(self.proc[key].is_alive() or self.proc[key].exitcode != 0):
                self.proc[key].kill()
                self.proc[key].join()
            self.proc[key].close()
            self.proc.pop(key, None)

    def add_queue(self, key, queue):
        """Given a string key, and a multiprocessing.Queue queue,
        it adds the queue inside the queue dictionary"""
        if isinstance(queue, multiprocessing.queues.Queue):
            self.queue[key] = queue
        else:
            raise Exception("queue must be instance of multiprocessing.Queue")

    def get_queue(self, key):
        """Given a string key returns the associated queue if exists"""
        if key in self.queue:
            return self.queue[key]
        else:
            return None

    def delete_queue(self, key):
        """Given a string key removes the associated queue"""
        if key in self.queue:
            self.queue.pop(key, None)
