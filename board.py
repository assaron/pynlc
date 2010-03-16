# -*- coding: utf-8 -*-
from __future__ import with_statement
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

from datetime import date, timedelta
from threading import Condition
from Queue import Queue

from util import nsplit, get_expiration_day
from node import *
import config

MESSAGE_PROPERTIES = (
    ("id", int_decoder), ("unknown1", int_decoder), ("parent_id", int_decoder),
    ("delete_", int_decoder), ("IP", str_decoder), ("hostname", unicode_decoder),
    ("nick", unicode_decoder), ("body", unicode_decoder),
    ("edit_time", time_decoder), ("channel_id", int_decoder),
    ("unknown2", int_decoder), ("mac", str_decoder), ("zero1", int_decoder),
    ("zero2", int_decoder), ("zero3", int_decoder), ("zero4", int_decoder),
    ("time_id", int_decoder), ("deleted", int_decoder), ("post_time", time_decoder)
    )

# Message base class
MessageBase = Node(MESSAGE_PROPERTIES)

class Message(MessageBase):
    """
        Message.

        zeroX     - fields that seems to be always zero
        thread_id - something like thread id
        time_id   - consecutive ID: almost all the time 
                    (post_time1 > post_time2) == (time_id1 > time_id2)
        delete_   - seems to be equal to one after deleting
        deleted   - deletes message from original client (oppose to delete_)
    """

    def __init__(self, messages_update):
        """
            Parses message_update.
        """
        MessageBase.__init__(self, messages_update)
        self._properties["body"] = self._properties["body"].replace("\x01", "\n")

CHANNEL_PROPERTIES = (("id", int_decoder),
                      ("name", unicode_decoder),
                      ("description", unicode_decoder))

# Channel base class
ChannelBase = Node(CHANNEL_PROPERTIES)

class Channel(ChannelBase):
    """
        Channel.
    """
    def __init__(self, channel_update):
        ChannelBase.__init__(self, channel_update)

class Board:
    """
        Simple board realization.
    """
    def __init__(self, sender=None, with_iternews=True):
        self._channels = None
        self._channels_sequence = None
        self._messages = {}
        self._sender = sender
        self._last_time_id = 0
        self._channels_processed = False
        self._channels_processed_condition = Condition()
        self._with_iternews = with_iternews
        if with_iternews:
            self._news = Queue()
        else:
            self._news = None

    def handle_update(self, message):
        """
            Handles update messages.
        """
        # remove the first 'd' char
        message = message[1:]
        type_, message = nsplit(message, 2)
        actions = { "channels" : self.handle_channels_update,
                    "new" : self.handle_new,
                    "admin" : None,
                    "skins" : None,
                    "skin" : None }

        if type_ in actions:
            action = actions[type_]
            if action:
                action(message)
        else:
            self.handle_messages_update(type_, message)

    def set_sender(self, new_sender):
        """
            Sets sender for replies.
        """
        self._sender = new_sender

    def reply(self, message_id, reply, nick):
        """
            Creates a reply on the message.
        """
        reply = reply.replace("\n","\r").encode("cp1251")
        nick = nick.encode("cp1251")
        self._sender("Dreply\t%d\t%s\t%s\t\t\n" % (message_id, nick, reply))

    def new(self, channel_id, message, nick, actuality_period=50):
        """
            Creates new message on the channel with the actuality period in days.
        """
        expiration_date = get_expiration_day(actuality_period)
        message = message.replace("\n","\r").encode("cp1251")
        nick = nick.encode("cp1251")
        self._sender("Dadd\t%d\t%d\t%s\t%s\n" %
                        (channel_id, expiration_date, nick, message))

    def edit_message(self, message_id, new_message,
                     new_nick, actuality_period=50):
        """
            Changes message.
        """
        message = self._messages[message_id]
        new_message = new_message.replace("\n","\r").encode("cp1251")
        new_nick = new_nick.encode("cp1251")
        expiration_date = get_expiration_day(actuality_period)
        self._sender("Dedit\t%d\t%d\t%d\t%d\t%s\t%s\t\t" %
                (message_id, message.channel_id(), expiration_date,
                 message.parent_id(), new_nick, new_message))

    def delete_message(self, message_id):
        """
            Deletes the message with comments.
        """
        # :TODO: change nick to something else and see what happens
        self._sender("Ddel\t%d\t%s\t\t\n" %
                (message_id, self._messages[message_id].nick().encode("cp1251")))

    def delete_comments(self, message_id):
        """
            Deletes comments of the message.
        """
        self._sender("Ddel\t%d\t%s\tReplyOnly\t\n" %
                (message_id, self._messages[message_id].nick().encode("cp1251")))


    def up_message(self, message_id):
        """
            Moves message to the top.
        """
        self._sender("Dup\t%d\n" % message_id)

    def update(self):
        """
            Sends request for update.
        """
        # "-8=-1," means that we're requesting from all (-8) channels
        # as many messages as server wants (-1)
        self._sender("Dlast\t%d\t-8=-1,\n" % self._last_time_id)

    def channels_list(self):
        """
            Returns a tuple of all channels.
        """
        return tuple(map(self.get_channel, self._channels_sequence))

    def get_channel(self, id):
        """
            Returns a channel by id.
            Returns None if id is absent.
        """
        if id in self._channels:
            return self._channels[id]
        return None

    def get_channel_name(self, channel, with_description=False):
        """
            Returns a channel name by channel.
            Returns a channel name with description by channel.
        """
        if with_description:
            return "/".join([node.name()[1:] for node in channel]) +\
            " :: "+"/".join([node.description() for node in channel])
        else:
            return "/".join([node.name()[1:] for node in channel])

    def get_message(self, id):
        """
            Returns a message by id. 
            Returns None if id is absent.
        """
        if id in self._messages:
            return self._messages[id]
        return None

    def last_time_id(self):
        """
            Returns the biggest time_id.
        """
        return self._last_time_id

    def wait_for_channels(self):
        """
            Waits for channels to be recieved.
        """
        with self._channels_processed_condition:
            while not self._channels_processed:
                self._channels_processed_condition.wait()

    def iternews(self):
        """
            Iterates on new messages.
            Should be called only once!
            Iteration should go in daemonic thread!
        """
        import sys
        if not self._with_iternews:
            raise Exception(
                    "Calling iternews() without setting with_iternews to True")
        def _news_iterator():
            while True:
                yield self._news.get()
        return _news_iterator()

    def handle_new(self, message):
        """
            Handles 'dnew' message calling update().
        """
        self.update()

    def handle_channels_update(self, message):
        """
            Handles dchannels message.
            Creates channels list.
            Clears previously recieved channels and messages.
        """
        self._channels = {}
        self._channels_sequence = []
        self._messages = {}
        for channel_update in message.split("\r")[:-1]:
            channel = Channel(channel_update)
            self._channels[channel.id()] = channel
            self._channels_sequence.append(channel.id())

        with self._channels_processed_condition:
            self._channels_processed = True
            self._channels_processed_condition.notifyAll()


    def handle_messages_update(self, header, messages_update):
        """
            Handle messages' update.
            Add messages to the tree.
        """
        messages_update = messages_update.split('\r')[:-1]
        for message_update in messages_update:
            message = Message(message_update)

            if message.time_id() > self._last_time_id:
                self._last_time_id = message.time_id()

            if message.parent_id() == -1:
                parent = self._channels[message.channel_id()]
            else:
                parent = self._messages[message.parent_id()]

            if message.id() in self._messages:
                # editing update (after Dedit or Ddel)
                old_message = self._messages[message.id()]
                parent.replace_reply(old_message, message)
            else:
                # new message
                parent.add_reply(message)

            self._messages[message.id()] = message
            if self._with_iternews:
                self._news.put(message)

