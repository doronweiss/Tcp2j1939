import os
import threading

from mctcpserver import MCTcpServer
import queue
import time


def enqueue(self, data):
    dataQueue.put(data)
    mre.set()


mre = threading.Event()
dataQueue = queue.Queue()
mts = MCTcpServer('127.0.0.1', 65432, enqueue)
mts.decoder.start()
mts.start()
print ("After run")
while True:
    mre.wait(0.1)
    mre.clear()
    try:
        data = dataQueue.get(False)
        print ("Resieved: {}".format(repr(data)))
        time.sleep(0.1)
    except:
        break
