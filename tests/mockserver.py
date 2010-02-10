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
import random

class MockServer:
    def __init__(self):
        self.server_socket = socket.socket()
        self.server_socket.bind(('', 0))
        self.host, self.port = self.server_socket.getsockname()
        self.server_socket.listen(10)
        self.recieved = None

    def random_send(self, seed = 15):
        connection_socket, addr_indo = self.server_socket.accept()
        random_genearator = random.Random(seed)
        header = open("tests/s2c.log")
        while True:
            size = 1 << random_genearator.randint(2, 13)
            msg = header.read(size)
            if not msg:
                break
            connection_socket.sendall(msg)

        connection_socket.close()

    def recieve_all(self):
        connection_socket, addr_indo = self.server_socket.accept()
        message = ""
        while True:
            buf = connection_socket.recv(1024)
            if not buf:
                break
            message += buf

        self.recieved = message

        connection_socket.close()




    def shutdown(self):
        self.server_socket.close()


