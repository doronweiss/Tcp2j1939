import threading
import queue

class MessageDecoder  (threading.Thread):
    def __init__(self):
        self.dataQueue = queue.Queue()
        self.mre = threading.Event()
        self.bcontinue = True

    def enqueue (self, data):
        self.dataQueue.put(data)
        self.mre.set()

    def dequeue (self):
        data = self.dataQueue.get(False)  # doesn't block
        if not data  is None:
            return data
        else:
            return None

    def run(self):
        while self.bcontinue:
            self.mre.wait(0.1)
            self.mre.clear()
            while True: # queue emptying loop
                try:
                    pass
                except:
                    break
