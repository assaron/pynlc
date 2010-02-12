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

from datetime import date, timedelta

from util import nsplit
import config

def get_get_property_from_dict_function(property_name, dict_name="_properties"):
    def _get_property_from_dict(self):
        return getattr(self, dict_name)[property_name]
    return _get_property_from_dict


def Node(properties_names, text_properties):
    """
        Generates a class with given properties.
    """
    class _Node:
        def __init__(self, input_string):
            properties = input_string.split('\t')[:-1]
            self._properties = dict(zip(properties_names, properties))
            for key, value in self._properties.iteritems():
                if key in text_properties:
                    self._properties[key] = value.decode("cp1251")
                else:
                    self._properties[key] = int(value)

            self._replies = []

        def add_reply(self, reply):
            """
                Appends the reply to the replies' list.
            """
            self._replies.append(reply)

        def replies(self):
            """
                Returns list of replies.
            """
            # :TODO: something like iterreplies will be good.
            return tuple(self._replies)


    # creating readonly properties like 
    # def id()
    #     return self._properties["id"]
    for name in properties_names:
        setattr(_Node, name, get_get_property_from_dict_function(name))

    return _Node

MESSAGE_PROPERTIES = ("id", "unknown1", "parent_id", "delete_",
        "IP", "hostname", "nick", "body", "edit_time", "channel_id",
        "unknown2", "mac", "zero1", "zero2", "zero3", "zero4",
        "time_id", "deleted", "post_time" )
MESSAGE_TEXT_PROPERTIES = set(["IP", "hostname", "nick", "body", "mac"])

# Message base class
MessageBase = Node(MESSAGE_PROPERTIES, MESSAGE_TEXT_PROPERTIES)

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

CHANNEL_PROPERTIES = ("id", "name", "description")
CHANNEL_TEXT_PROPERTIES = set(["name", "description"])

# Channel base class
ChannelBase = Node(CHANNEL_PROPERTIES, CHANNEL_TEXT_PROPERTIES)

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
    def __init__(self, sender=None):
        self._channels = None
        self._channels_sequence = None
        self._messages = {}
        self._sender = sender
        self._last_time_id = 0

    def handle_update(self, message):
        """
            Handles update messages.
        """
        # remove the first 'd' char
        message = message[1:]
        type_, message = nsplit(message, 2)
        actions = { "channels" : self.handle_channels_update,
                    "new" : None,
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
        expiration_date = (date.today() + timedelta(actuality_period) -
                           config.EPOCH_START_DAYS).days
        message = message.replace("\n","\r").encode("cp1251");
        nick = nick.encode("cp1251")
        self._sender("Dadd\t%d\t%d\t%s\t%s\n" %
                        (channel_id, expiration_date, nick, message))

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

    def handle_channels_update(self, message):
        """
            Handles dchannels message.
            Creates channels list.
        """
        self._channels = {}
        self._channels_sequence = []
        for channel_update in message.split("\r")[:-1]:
            channel = Channel(channel_update)
            self._channels[channel.id()] = channel
            self._channels_sequence.append(channel.id())

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

            self._messages[message.id()] = message

            if message.parent_id() == -1:
                parent = self._channels[message.channel_id()]
            else:
                parent = self._messages[message.parent_id()]
            parent.add_reply(message)

