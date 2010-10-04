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


from nodes import *
from util import nsplit, get_expiration_day, logobject

class BoardManager:
    """
        Manages incoming and outcoming board messages.
    """
    @logobject
    def __init__(self, sender, updates_handler):
        """
            @param sender function, get string argument and sends it to server
            @param updates_handler function, get nodes updates,
                                   should be thread-safe
        """
        # :TODO:
        self._sender = sender
        self._last_time_id = 0
        self._external_updates_handler = updates_handler

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

    def edit_message(self, message_id, channel_id, parent_id, new_message,
                     new_nick, actuality_period=50):
        """
            Changes message.
        """
        # :TODO: what'll happen when change channel and parent id?
        new_message = new_message.replace("\n","\r").encode("cp1251")
        new_nick = new_nick.encode("cp1251")
        expiration_date = get_expiration_day(actuality_period)
        self._sender("Dedit\t%d\t%d\t%d\t%d\t%s\t%s\t\t" %
                (message_id, channel_id, expiration_date,
                 parent_id, new_nick, new_message))

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

    def last_time_id(self):
        """
            Returns the biggest time_id.
        """
        return self._last_time_id

    def handle_new(self, message):
        """
            Handles 'dnew' message calling update().
        """
        self.update()

    def handle_channels_update(self, message):
        """
            Handles dchannels message.
        """
        for channel_update in message.split("\r")[:-1]:
            channel = Channel(channel_update)

            self.log.debug("update: got channel %s" % channel)

            self._external_updates_handler(channel)

    def handle_messages_update(self, header, messages_update):
        """
            Handle messages' update.
            Add messages to the tree.
        """
        messages_update = messages_update.split('\r')[:-1]
        for message_update in messages_update:
            message = Message(message_update)

            self.log.debug("update: got message %s" % message)

            if message.time_id() > self._last_time_id:
                self._last_time_id = message.time_id()

            self._external_updates_handler(message)

