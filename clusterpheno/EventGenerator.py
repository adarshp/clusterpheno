class EventGenerator(object):
    def __init__(self, processes, mg5_path):
        self.processes = processes
        self.mg5_path = mg5_path
    def create_directories(self):
        for process in self.processes:
            process.create_directory(self.mg5_path)
