import os
import socket
import threading
import selectors
import types


class mctcpserver (threading.Thread):
    def __init__(self, address, port):
        self.bContinue = True
        self.address = address
        self.port = port
        self.sel = selectors.DefaultSelector()

    def run2(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.address, self.port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    print('Received', repr(data))
                    if not data:
                        break
                    conn.sendall(data)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as lsock:
            #lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            lsock.bind((self.address, self.port))
            lsock.listen()
            print('listening on', (self.address, self.port))
            lsock.setblocking(False)
            self.sel.register(lsock, selectors.EVENT_READ, data=None)
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)

    def accept_wrapper(self,sock):
        conn, addr = sock.accept()  # Should be ready to read
        print('accepted connection from', addr)
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                print('closing connection to', data.addr)
                self.sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print('echoing', repr(data.outb), 'to', data.addr)
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]