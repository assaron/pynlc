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

from datetime import date, timedelta
from nose.tools import eq_

from boardmanager import *
from util import SimpleServer

def test_board_reply():
    simple_server = SimpleServer()
    brdMngr = BoardManager(simple_server.send, id)
    reply = u"чё смеешься?"
    nick = u"user_Вася"
    parent_id = 4
    brdMngr.reply(parent_id, reply, nick)

    eq_("Dreply\t%d\t%s\t%s\t\t\n" % (parent_id, nick, reply),
        simple_server.recieve().decode('cp1251'))

def test_board_new():
    simple_server = SimpleServer()
    brdMngr = BoardManager(simple_server.send, id)
    channel_id = 0
    message = u"Внимание!"
    nick = u"user_Вася"
    brdMngr.new(channel_id, message, nick)
    expiration_date = (date.today() + timedelta(50) - date(1899, 12, 30)).days
    eq_("Dadd\t%d\t%d\t%s\t%s\n" % (channel_id, expiration_date, nick, message),
        simple_server.recieve().decode('cp1251'))

    channel_id = 1
    message = u"Срочный вопрос!"
    nick = u"user_Петя"
    actuality_period = 1
    brdMngr.new(channel_id, message, nick, actuality_period)
    expiration_date = (date.today() +
                       timedelta(actuality_period) - date(1899, 12, 30)).days
    eq_("Dadd\t%d\t%d\t%s\t%s\n" % (channel_id, expiration_date, nick, message),
        simple_server.recieve().decode('cp1251'))

def test_auto_update():
    simple_server = SimpleServer()
    brdMngr = BoardManager(simple_server.send, id)
    brdMngr.handle_update("dnew\n")
    eq_("Dlast\t0", simple_server.recieve()[:7])


