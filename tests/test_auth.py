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

from nose.tools import eq_
from util import SimpleServer
from auth import *

def test_auth():
    simple_server = SimpleServer()
    auth = Authentificator(simple_server.send)
    auth.handle_request("RASX")
    result = simple_server.recieve().split("\t")
    eq_(result[1], "JHOFIG")

