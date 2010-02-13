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

from itertools import izip, ifilter

def get_get_property_from_dict_function(property_name, dict_name="_properties"):
    def _get_property_from_dict(self):
        return getattr(self, dict_name)[property_name]
    return _get_property_from_dict

int_decoder = int
str_decoder = None
def unicode_decoder(string):
    return string.decode("cp1251")

def Node(properties):
    """
        Generates a class with given properties.
    """
    class _Node:
        def __init__(self, input_string):
            values = input_string.split('\t')[:-1]
            self._properties = {}
            for (name, decoder), value in izip(properties, values):
                if decoder:
                    value = decoder(value)
                self._properties[name] = value

            self._replies = []

        def add_reply(self, reply):
            """
                Appends the reply to the replies' list.
            """
            self._replies.append(reply)

        def replies(self, with_deleted=False):
            """
                Returns a tuple of replies.
            """
            return tuple(self.iterreplies(with_deleted))

        def iterreplies(self, with_deleted=False):
            """
                Returns an iterator for replies.
            """
            def not_deleted(message):
                return not message.deleted()
            if with_deleted:
                return iter(self._replies)
            return ifilter(not_deleted, self._replies)

        def replace_reply(self, old_message, new_message):
            """
                Replaces old_message to new_message in replies.
            """
            self._replies[self._replies.index(old_message)] = new_message


    # creating readonly properties like 
    # def id()
    #     return self._properties["id"]
    for name, __ in properties:
        setattr(_Node, name, get_get_property_from_dict_function(name))

    return _Node


