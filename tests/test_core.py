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


# Adding parent dir to syspath
import sys
from os.path import join, realpath, pardir
sys.path.append(
    realpath(join(__file__, pardir, pardir)))


from threading import Thread

from nose.tools import eq_, assert_raises

from unittest import TestCase
from mockserver import MockServer
from core import *

class TestConnector(TestCase):
    def setUp(self):
        self.server = MockServer()

    def tearDown(self):
        self.server.shutdown()
        del self.server

    def test_iterlines(self):
        thread = Thread(target=self.server.random_send)
        thread.start()
        connector = Connector(('localhost', self.server.port))
        data = open('tests/s2c.log')
        for line in connector.iterlines():
            eq_(line, data.next()[:-1])
        assert_raises(StopIteration, data.next)
        connector.stop_and_wait()

        thread.join()

    def test_send(self):
        messages = ("the first test message\n",
                    "the second message is very l" + "o" * 10000 + "ng\n"
                   )
        message = "".join(messages)
        thread = Thread(target=self.server.recieve_all)
        thread.start()
        connector = Connector(('localhost', self.server.port))

        for m in messages:
            connector.send(m)

        connector.stop_and_wait()
        thread.join()

        eq_(message, self.server.recieved)

class TestClientCore(TestCase):
    def setUp(self):
        self.server = MockServer()
    
    def tearDown(self):
        self.server.shutdown()
        del self.server

    def test_set_handler(self):
        thread = Thread(target=self.server.random_send)
        thread.start()
        core = ClientCore(('localhost', self.server.port))

        def c_generator():
            for line in open('tests/s2c.log'):
                if line[0] == 'c':
                    yield line[:-1]
        c_generator = c_generator()

        def c_handler(c_message):
            eq_(c_generator.next(), c_message)

        def lab_generator():
            for line in open('tests/s2c.log'):
                if line[0] in 'lab':
                    yield line[:-1]
        lab_generator = lab_generator()

        def lab_handler(lab_message):
            eq_(lab_generator.next(), lab_message)

        def R_handler(R_message):
            raise Exception("Unreachable code")

        core.set_handler('c', c_handler)
        core.set_handler('lab', lab_handler)
        core.set_handler('R', R_handler)
        core.remove_handler('R')
        core.run()
        core.stop_and_wait()

        thread.join()

        assert_raises(StopIteration, c_generator.next)
        assert_raises(StopIteration, lab_generator.next)


    def test_send(self):
        messages = ("the first test message\n",
                    "the second message is very l" + "o" * 10000 + "ng\n"
                   )
        message = "".join(messages)
        thread = Thread(target=self.server.recieve_all)
        thread.start()
        core = ClientCore(('localhost', self.server.port))

        for m in messages:
            core.send(m)

        core.stop()
        thread.join()

        eq_(message, self.server.recieved)

