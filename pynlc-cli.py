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
import os
import traceback
import argparse
import logging

from tempfile import mkstemp
from datetime import timedelta
from subprocess import call
from getpass import getuser
from guppy import hpy

from core import ClientCore
from board import *
from auth import Authentificator
from util import print_function

import config

def print_message(msg):
    print ""
    print "====================="
    print "From:", msg.nick()
    print "Date:", msg.post_time().ctime()
    print "ID:", msg.id()
    print "---------------------"
    print msg.body()
    print "====================="
    print ""

if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description="interface to pynlc")
    argParser.add_argument("-g", help="GUI interface")
    argParser.add_argument("-d", help="debug", action="store_const",
                           dest="debug", const=True, default=False)
    args = argParser.parse_args()
    if args.debug:
        logging.basicConfig(filename="log", 
                            level=logging.DEBUG,
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.debug("pynlc-cli started")


    core = None
    nick = getuser()
    profiler = hpy()
    try:
        core = ClientCore(config.SERVER)
        board = Board(core.send)
        auth = Authentificator(core.send)
        core.set_handler('d', board.handle_update)
        core.set_handler('R', auth.handle_request)
        core.set_handler('bfs', print_function)
        core.start()

        board.update()

        board.wait_for_channels()

        stack = [board.get_channel(0)]
        while True:
            prompt = "#%s$ " % ("/".join([`node.id()` for node in stack]))
            args = raw_input(prompt).split()
            if not args:
                continue
            cmd = args[0]
            try:
                if cmd == 'help':
                    print """
    This is a simple NetLand client.
    Possible commands are:

        cat <id1> <id2> ... - print messages with id1, id2, ...,
            idN are integers or '*'
            if idN = '*' print all current message's comments

        cd <path> - tries to change the current node to path
            examples of path:
                ../1234
                1234/1233
                #2/3123/../352

        help - prints this message

        exit - exits

        ls - lists current message's comments' ids

        memusage - some info about memory usage

        post - opens $EDITOR to compose a comment to the current node,
            leave empty to cancel

        rm [-c] <id1> <id2> - removes messages and their comments
            with -c option removes only comments

        up - up message to the top

        update - updates the messages tree

"""
                elif cmd == 'exit':
                    break
                elif cmd == 'ls':
                    for msg in stack[-1].iterreplies():
                        print msg.id()
                elif cmd == 'cat':
                    for arg in args[1:]:
                        if arg == '*':
                            map(print_message, stack[-1].iterreplies())
                        elif arg.isdigit():
                            message_id = int(arg)
                            message = board.get_message(message_id)
                            if message:
                                print_message(message)
                elif cmd == 'cd':
                    arg = args[1]
                    for node in arg.split('/'):
                        if node[0] == '#':
                            channel_id = int(node[1:])
                            channel = board.get_channel(channel_id)
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
                elif cmd == 'rm':
                    if '-c' in args:
                        deleter = board.delete_comments
                    else:
                        deleter = board.delete_message
                    for arg in args[1:]:
                        if arg.isdigit():
                            deleter(int(arg))
                elif cmd == 'up':
                    for arg in args[1:]:
                        if arg.isdigit():
                            board.up_message(int(arg))
                elif cmd == 'memusage':
                    print profiler.heap()


            except:
                print "Unhandled exception:"
                traceback.print_exc()

    except:
        print "Unhandled exception:"
        traceback.print_exc()
        print "Exiting..."

    finally:
        core.stop_and_wait()
