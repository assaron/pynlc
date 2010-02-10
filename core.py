# -*- coding: utf-8 -*-
# 
# Copyrigt 2010 Aleksey Sergushichev <alsergbox@gmail.com>
# 
# This file is part of pynlc.

# Pynlc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Pynlc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pynlc.  If not, see <http://www.gnu.org/licenses/>.

import socket
import Queue 
import threading

import config

class Connector (threading.Thread):
    """
        The class that handle connection with Netland server.
    """

    def __init__(self, server_address):
        """
            Connects to a given server.
        """
        threading.Thread.__init__(self)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(server_address)

        self.stopped = False
        self.out_queue = Queue.Queue(0)

        self.start()

    def send(self, msg):
        """
            Adds the message to queue for sending.
            Raise an exception if connector is stopped.
        """
        if not self.stopped:
            self.out_queue.put(msg)
        else:
            # FIXME: change exception type
            raise Exception("Can't send a message because connector is stopped")

    def stop(self):
        """
            Stops connector. Does NOT wait.
        """
        self.stopped = True
        self.out_queue.put(None)

    def stop_and_wait(self):
        """
            Stops connector and waits for processing all data.
        """
        self.stop()
        self.out_queue.join()

    def iterlines(self, line_splitter = '\n'):
        """
            Generator for incoming lines.
        """
        last = ""
        while True:
            try:
                s = self.client_socket.recv(config.BUF_SIZE)
            except socket.error:
                s = None

            if not s:
                raise StopIteration
            lines = s.split(line_splitter)
            lines[0] = last + lines[0]
            last = lines[-1]
            lines = lines[:-1]
            
            for line in lines:
                if line == "":
                    continue
                yield line

    def run(self):
        """
            Starts sending messages from the interanal queue.
        """
        while True:
            msg = self.out_queue.get()
            if not msg and self.stopped:
                break
            self.client_socket.sendall(msg)
            self.out_queue.task_done()

        self.client_socket.shutdown(socket.SHUT_RD)
        self.client_socket.close()
        self.out_queue.task_done()


class ClientCore(threading.Thread):
    """
        Dispatch data income and outcome data flaws.
    """

    def __init__(self, server_address):
        threading.Thread.__init__(self)
        self._connector = Connector(server_address)
        self._handlers = {}

    def set_handler(self, chars, handler):
        """
            Sets handler for messages starting with given chars.
        """
        for char in chars:
            self._handlers[char] = handler

    def remove_handler(self, chars):
        """
            For all char in chars remove handler if it exists.
        """
        for char in chars:
            if char in self._handlers:
                del self._handlers[char]

    def send(self, msg):
        """
            Sends message to server.
        """
        self._connector.send(msg)

    def stop(self):
        """
            Stops core. Does NOT wait.
        """
        self._connector.stop()

    def stop_and_wait(self):
        """
            Stops core and waits for end.
        """
        self._connector.stop_and_wait()

    def run(self):
        """
            Handles messages from server.
        """
        for line in self._connector.iterlines():
            if line[0] in self._handlers:
                self._handlers[line[0]](line)



