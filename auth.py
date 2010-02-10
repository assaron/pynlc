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

from subprocess import Popen, PIPE
from platform import system
from socket import gethostname

import config

class Authentificator:
    """
        Class that holds authentification stuff.
    """
    def __init__(self, sender=None, auto_auth=True):
        self._sender = sender
        self._request_message = None
        self._auto_auth = auto_auth

    def set_sender(self, new_sender):
        """
            Sets sender for auth replies.
        """
        self._sender = new_sender

    def handle_request(self, request_message):
        """
            Remembers authentification request.
        """
        # removing the first 'R' char
        self._request_message = request_message[1:]
        if self._auto_auth:
            self.auth()

    def auth(self):
        """
            Sends authentification reply.
        """
        sys = system()
        if sys == 'Linux':
            executable = "./encode"
        else:
            raise Exception("Unsupported OS")
        args = [executable, config.NC_HASH, self._request_message]
        p = Popen(args, stdout=PIPE)
        reply = p.stdout.readline()[:-1] # without '\n'
        p.wait()

        self._sender("%s\t%s\t%s %s\t%s\n" % \
                (config.NC_VERSION,  reply, "CPU_INFO", "OS_INFO", gethostname()))

