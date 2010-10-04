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

from node import *

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

