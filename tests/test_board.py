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
from nose.tools import eq_, assert_raises
from board import *
from util import SimpleServer
from threading import Thread

def test_board():
    board = Board()
    channels = [ (0, "#Channel0", "This is the zeroth channel"),
                 (2, "#Channel2", "This is the zeroth channel"),
                 (3, "#Channel3", "This is the zeroth channel"),
                 (1, u"#1 канал", u"Первый канал представляет"),]

    update_message = "dchannels\t" + "\t\r".join(
            ["\t".join([unicode(field) for field in channel])
                for channel in channels] + [''])

    board.handle_update(update_message.encode("cp1251"))
    board_channels = [
            tuple([getattr(channel,field)()
                for field, __ in CHANNEL_PROPERTIES])
                    for channel in board.channels_list()]
    eq_(channels, board_channels)
    eq_(None, board.get_channel(10))

    eq_(0, board.last_time_id())

    messages = [[1, 0, -1, 0, "127.0.0.1", "host1", "nick1", "Hello world",
                 0, 1, 0, "ff-ff-ff-ff-ff-ff", 0, 0, 0, 0, 1, 0, 0],
                [2, 0, 1, 0, "127.0.0.2", "host2", "nick2", u"Привет и тебе",
                 0, 1, 0, "ff-ff-ff-ff-ff-fe", 0, 0, 0, 0, 2, 1, 0],
                [3, 0, 1, 0, "255.255.255.255", "255", u"ник255", u"бугога",
                 0, 1, 0, "00-00-00-00-00-00", 0, 0, 0, 0, 5, 0, 0],
                [4, 0, -1, 0, "127.0.0.2", "host2", "nick2", "Hello<br>\nchannel<br>\n#2",
                 0, 2, 0, "ff-ff-ff-ff-ff-fe", 0, 0, 0, 0, 3, 1, 0], ]

    update_message = "dmagic\r" + ("\t\r".join(
            ["\t".join([unicode(field) for field in message])
                for message in messages] + [''])).replace("\n","\x01")

    board.handle_update(update_message.encode("cp1251"))

    eq_(5, board.last_time_id())

    eq_([len(board.get_channel(i).replies()) for i in xrange(4)],
        [0, 1, 0, 0])

    eq_([len(board.get_message(i).replies()) for i in xrange(1, 5)],
        [1, 0, 0, 0])

    eq_([len(board.get_channel(i).replies(True)) for i in xrange(4)],
        [0, 1, 1, 0])

    eq_([len(board.get_message(i).replies(True)) for i in xrange(1, 5)],
        [2, 0, 0, 0])

    for message in messages:
        board_message = board.get_message(message[0])
        for i, (field, decoder) in enumerate(MESSAGE_PROPERTIES):
            if not decoder:
                def identity(x):
                    return x
                decoder = identity
            eq_(decoder(unicode(message[i]).encode("cp1251")), getattr(board_message, field)())

    eq_(None, board.get_message(10))

    simple_server = SimpleServer()
    board.set_sender(simple_server.send)
    message_id = 3
    board.delete_message(message_id)
    eq_("Ddel\t%d\t%s\t\t\n" % (message_id, messages[message_id - 1][6]),
        simple_server.recieve().decode('cp1251'))

    board.delete_comments(message_id)
    eq_("Ddel\t%d\t%s\tReplyOnly\t\n" % (message_id, messages[message_id - 1][6]),
        simple_server.recieve().decode('cp1251'))

    expiration_date = (date.today() + timedelta(50) - date(1899, 12, 30)).days
    new_message = u"измененное\nсообщение"
    new_nick = u"измененный ник"
    board.edit_message(message_id, new_message, new_nick)
    eq_("Dedit\t%d\t%d\t%d\t%d\t%s\t%s\t\t" %
            (message_id, messages[message_id - 1][9], expiration_date,
             messages[message_id - 1][2], new_nick,
             new_message.replace("\n","\r")),
        simple_server.recieve().decode('cp1251'))

    eq_(messages[2][17], 0)
    messages[2][17] = 1


    update_message = "dmagic\r" + (
            "\t\r".join(
                ["\t".join([unicode(field) for field in messages[2]])
                ] + ['']
                )
            ).replace("\n","\x01")

    board.handle_update(update_message.encode("cp1251"))

    eq_([len(board.get_channel(i).replies()) for i in xrange(4)],
        [0, 1, 0, 0])

    eq_([len(board.get_message(i).replies()) for i in xrange(1, 5)],
        [0, 0, 0, 0])

    eq_([len(board.get_channel(i).replies(True)) for i in xrange(4)],
        [0, 1, 1, 0])

    eq_([len(board.get_message(i).replies(True)) for i in xrange(1, 5)],
        [2, 0, 0, 0])


def test_board_reply():
    simple_server = SimpleServer()
    board = Board(simple_server.send)
    reply = u"чё смеешься?"
    nick = u"user_Вася"
    parent_id = 4
    board.reply(parent_id, reply, nick)

    eq_("Dreply\t%d\t%s\t%s\t\t\n" % (parent_id, nick, reply),
        simple_server.recieve().decode('cp1251'))

def test_board_new():
    simple_server = SimpleServer()
    board = Board(simple_server.send)
    channel_id = 0
    message = u"Внимание!"
    nick = u"user_Вася"
    board.new(channel_id, message, nick)
    expiration_date = (date.today() + timedelta(50) - date(1899, 12, 30)).days
    eq_("Dadd\t%d\t%d\t%s\t%s\n" % (channel_id, expiration_date, nick, message),
        simple_server.recieve().decode('cp1251'))

    channel_id = 1
    message = u"Срочный вопрос!"
    nick = u"user_Петя"
    actuality_period = 1
    board.new(channel_id, message, nick, actuality_period)
    expiration_date = (date.today() +
                       timedelta(actuality_period) - date(1899, 12, 30)).days
    eq_("Dadd\t%d\t%d\t%s\t%s\n" % (channel_id, expiration_date, nick, message),
        simple_server.recieve().decode('cp1251'))

def test_board_up_message():
    simple_server = SimpleServer()
    board = Board(simple_server.send)
    message_id = 4
    board.up_message(message_id)

    eq_("Dup\t%d\n" % message_id, simple_server.recieve().decode('cp1251'))

def test_wait_for_channels():
    board = Board()
    waiting_thread = Thread(target = board.wait_for_channels)
    waiting_thread.start()
    eq_(waiting_thread.isAlive(), True)
    channels = [ (0, "#Channel0", "This is the zeroth channel"),
                 (2, "#Channel2", "This is the zeroth channel"),
                 (3, "#Channel3", "This is the zeroth channel"),
                 (1, u"#1 канал", u"Первый канал представляет"),]
    eq_(waiting_thread.isAlive(), True)

    update_message = "dchannels\t" + "\t\r".join(
            ["\t".join([unicode(field) for field in channel])
                for channel in channels] + [''])

    eq_(waiting_thread.isAlive(), True)

    board.handle_update(update_message.encode("cp1251"))
    waiting_thread.join()

def test_iternews():
    board = Board(with_iternews=False)
    assert_raises(Exception, board.iternews)

    board = Board()

    news = board.iternews()

    channels = [ (0, "#Channel0", "This is the zeroth channel"), ]
    update_message = "dchannels\t" + "\t\r".join(
            ["\t".join([unicode(field) for field in channel])
                for channel in channels] + [''])
    board.handle_update(update_message)


    messages = [[1, 0, -1, 0, "127.0.0.1", "host1", "nick1", "Hello world",
                 0, 0, 0, "ff-ff-ff-ff-ff-ff", 0, 0, 0, 0, 1, 0, 0],
                [2, 0, 1, 0, "127.0.0.2", "host2", "nick2", u"Привет и тебе",
                 0, 0, 0, "ff-ff-ff-ff-ff-fe", 0, 0, 0, 0, 2, 1, 0],
                [3, 0, 1, 0, "255.255.255.255", "255", u"ник255", u"бугога",
                 0, 0, 0, "00-00-00-00-00-00", 0, 0, 0, 0, 5, 0, 0],
                [4, 0, -1, 0, "127.0.0.2", "host2", "nick2", "Hello<br>\nchannel<br>\n#2",
                 0, 0, 0, "ff-ff-ff-ff-ff-fe", 0, 0, 0, 0, 3, 1, 0], ]

    update_message = "dmagic\r" + ("\t\r".join(
            ["\t".join([unicode(field) for field in message])
                for message in messages[0:3]] + [''])).replace("\n","\x01")

    board.handle_update(update_message.encode("cp1251"))
    eq_(news.next().id(), 1)


    update_message = "dmagic\r" + ("\t\r".join(
            ["\t".join([unicode(field) for field in message])
                for message in messages[3:4]] + [''])).replace("\n","\x01")

    board.handle_update(update_message.encode("cp1251"))
    eq_(news.next().id(), 2)
    eq_(news.next().id(), 3)
    eq_(news.next().id(), 4)


def test_auto_update():
    simple_server = SimpleServer()
    board = Board(simple_server.send)
    board.handle_update("dnew\n")
    eq_("Dlast\t0", simple_server.recieve()[:7])


