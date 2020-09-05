import multiprocessing

class ProcessManager:
    __instance = None

    @staticmethod
    def get_instance():
        if ProcessManager.__instance == None:
            return ProcessManager()
        else:
            return ProcessManager.__instance

    def __init__(self):
        if ProcessManager.__instance != None:
            raise Exception("Error")
        else:
            ProcessManager.__instance = self
            self.proc = {}

    def add_process(self, key, process):
        self.proc[key] = process

    def process_exists(self, key):
        return key in self.proc

    def is_alive(self, key):
        return self.proc[key].is_alive()

    def start_process(self, key):
        self.proc[key].start()

    def end_process(self, key):
        if key in self.proc:
            self.proc[key].terminate()
            self.proc[key].join(1)
            # Subprocess won't end or exited on error
            if(self.proc[key].is_alive() or self.proc[key].exitcode != 0):
                self.proc[key].kill()
            self.proc[key].close()
            self.proc.pop(key, None)
