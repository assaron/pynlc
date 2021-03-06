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

from functools import partial, wraps
from datetime import date, timedelta
import logging

import config

def ping(server):
    """
        Spectial ping for netland server.
    """
    chost = ""
    cport = 1538
    ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ss.bind((chost, cport))
    sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sc.sendto('Ping Netland Servers', server)
    ss.settimeout(10)
    try:
        res = ss.recv(BUF_SIZE)
    except (socket.timeout):
        return None

    return res

def print_function(string):
    string = string.replace("\r", "\n")
    string = string.decode("cp1251")
    print string

def nsplit(s, num, sep=None):
    """
        Splits s to num pieces.
        Fills up left space with empty strings.
        >>> nsplit("1 2 3", 2)
        ['1', '2 3']
        >>> nsplit("1 2 3", 4)
        ['1', '2', '3', '']
    """
    return (s.split(sep, num-1) + ['']*num)[:num]

class SimpleServer:
    def __init__(self):
        self.message = None
    def send(self, message):
        self.message = message
    def recieve(self):
        return self.message

def get_expiration_day(actuality_period):
    return (date.today() + timedelta(actuality_period) -
            config.EPOCH_START_DAYS).days

def get_channel_name(channel, with_description=False):
    """
        Returns a channel name by channel.
        Returns a channel name with description by channel.
    """
    if with_description:
        return channel.name()[1:] + " :: " + channel.description()
    else:
        return channel.name()[1:]


def logobject(func):
    """
    Decorator adding logging.Logger instance to object as log attribute.
    """
    
    @wraps(func)
    def wrapper(obj, *args, **kw):
        obj.log = logging.getLogger(obj.__class__.__name__)
        return func(obj, *args, **kw)
    return wrapper
