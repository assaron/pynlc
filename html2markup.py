#!/usr/bin/python
# -*- coding: utf-8 -*-
# 
# Copyright 2010 Александр Крупенькин <alexandr.krupenkin@gmail.com>
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

from HTMLParser import HTMLParser

class Html2Markup(HTMLParser):
    """
        Simple HTMLParser.
    """
    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.buffer += "\n"
        if tag == "b":
            self.buffer += "<b>"
        if tag == "i":
            self.buffer += "<i>"
        
    def handle_endtag(self, tag):
        if tag == "b":
            self.buffer += "</b>"
        if tag == "i":
            self.buffer += "</i>"

    def handle_data(self, data):
        self.buffer += data
    
    def convert(self, html):
        self.buffer = u""
        self.feed(html)
        return self.buffer
        
