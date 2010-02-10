#!/usr/bin/python
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

import sys
import threading
import time
import os
from tempfile import mkstemp
from datetime import timedelta
from subprocess import call
from getpass import getuser

from core import ClientCore
from board import *
from auth import Authentificator
from util import print_function
import config

def print_message(msg):
    print ""
    print "====================="
    print "From:", msg.nick()
    date = config.EPOCH_START_SECONDS + timedelta(0, msg.post_time())
    print "Date:", date.ctime()
    print "ID:", msg.id()
    print "---------------------"
    print msg.body().replace('\r\n','\n').replace('\r','\n')
    print "====================="
    print ""

if __name__ == "__main__":
    core = None
    nick = getuser()
    try:
        core = ClientCore(config.SERVER)
        board = Board(core.send)
        auth = Authentificator(core.send)
        core.set_handler('d', board.handle_update)
        core.set_handler('R', auth.handle_request)
        core.set_handler('bfsF', print_function)
        core.start()

        board.update()

        # wait for dchannels message to be processed
        time.sleep(0.1) 
        stack = [board.get_channel(0)]
        while True:
            prompt = "#%s$ " % ("/".join([`node.id()` for node in stack]))
            args = raw_input(prompt).split()
            if not args:
                continue
            cmd = args[0]
            try:
                if cmd == 'exit':
                    break
                elif cmd == 'ls':
                    for msg in stack[-1].replies():
                        print msg.id()
                elif cmd == 'cat':
                    for arg in args[1:]:
                        if arg == '*':
                            map(print_message, stack[-1].replies())
                        else:
                            message_id = int(arg)
                            message = board.get_message(message_id)
                            if message:
                                print_message(message)
                elif cmd == 'cd':
                    arg = args[1]
                    for node in arg.split('/'):
                        if node[0] == '#':
                            channel_id = int(node[1:])
                            channel = board.get_channel(channeld_id)
                            if channel:
                                stack = [channel]
                        elif node == "..":
                            if len(stack) > 0:
                                stack = stack[:-1]
                        elif node == "":
                            pass
                        else:
                            message_id = int(node)
                            message = board.get_message(message_id)
                            if message:
                                stack.append(message)
                elif cmd == 'post':
                    if isinstance(stack[-1], Channel):
                        poster = board.new
                    else:
                        poster = board.reply
                    temp_fd, temp_name = mkstemp()
                    editor = os.getenv("EDITOR")
                    call([editor, temp_name])
                    file = os.fdopen(temp_fd)
                    message = (''.join(file)).decode('utf-8')
                    message = message.replace('\n','<br>\n')
                    if not message:
                        print "canceled"
                    else:
                        poster(stack[-1].id(), message, nick)
                        print "posted"
                elif cmd == 'update':
                    board.update()
            except:
                print "Unexpected error:", sys.exc_info()[0]


    finally:
        core.stop_and_wait()
