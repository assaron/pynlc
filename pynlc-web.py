#!/usr/bin/python
# -*- coding: utf-8 -*-
# 
# Copyrigt 2011 Aleksey Sergushichev <alsergbox@gmail.com>
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

import sys
import threading
import os
import traceback
import argparse
import logging
import re

import cgi
import urlparse
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

import posixpath
import urllib
import cgi
import sys
import shutil
import mimetypes
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from tempfile import mkstemp
from datetime import timedelta
from subprocess import call
from getpass import getuser
from guppy import hpy

from core import ClientCore
from board import *
from auth import Authentificator
from util import print_function

import config

smb_link_re = re.compile("\\\\\\\\([^ \\\\/?:]+\\\\)+")
netland_imgs_re = re.compile(u"\\\\\\\\" + config.SERVER[0] + u"\\\\~Поисковик~\\\\Imgs\\\\$")

def replace_smb_link(match_obj):
    s = match_obj.group(0)
    if not netland_imgs_re.match(s):
        return "smb:" + s.replace("\\","/")
    return "http://" + config.SERVER[0] + "/board/imgs?name="

def get_html_message(msg):
    res = u"""\
<table class=messN>
<tr>
 <td>%(id)d 
</table>

<table class=messT><tr>
	<td class=my3dC>
		<nobr>
		<font class=nik title="Ник">&nbsp;%(nick)s</font>
	<td class=my3dR>
		<table><tr><td><hr></table>
	<td width=100%%>
		<hr>
	<td class=my3dL>
		<table><tr><td><hr></table>
	<td class=my3dC>
		<nobr>
		%(hostname)s <small><small>(%(IP)s)</small></small>
		<font class=date>&nbsp;%(post_time)s</font>
</table>

<table width=100%%>
<tr><td class=mess>
%(body)s
</table>
<table width=100%%>
<tr>
	<td>
""" % msg._properties
    x = len(msg.replies())
    if x != 0:
        res += u"""\
        <span onclick="op(this,%d)" class=plusL>+[%d]</span>
""" % (msg.id(), x)

    res += u"""\
        <span onclick="reply(this,%(id)d)" class=replyL>Ответить</span>
    </td>
<tr>
    <td class=reply id="r%(id)d"></td>
</td>
<tr>
    <td class=replies id="rs%(id)d"></td>
</tr>
</table>""" % {"id" : msg.id()}
    return smb_link_re.sub(replace_smb_link, res)


def get_html_replies(parent_id):
    parent_id = int(parent_id)
    if (parent_id < 0):
        parent = board.get_channel(-parent_id - 1)
    else:
        parent = board.get_message(parent_id)
    if not parent:
        return None

    return "".join([get_html_message(m) for m in parent.replies()]).encode("utf-8")

def get_html_channel(channel_id):
    channel = board.get_channel(int(channel_id))
    if not channel:
        return None
    return (u"""\
<html>

<head>
  <title>NetlandSL, Доска объявлений Vadikus'a, #Новости</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <link rel="stylesheet" href="/styles.css" type="text/css">
  <script LANGUAGE="JavaScript" src="/scripts.js" type="text/javascript"></script>
</head>

<body
  bgColor=#101010
  text=#c0c0c0
  link=#80ffff
  alink=#ff0000
  topmargin=0
  leftmargin=0
  marginheight=0
  marginwidth=0
>
  <table width=100%%>

  <tr>
  <td width=1 style="padding: 10 15 5 15">
    <nobr>%s
  <td style="padding-top: 6">
    <small>%s</small>
  </table>

  <div id="rs-1">
    Java Script not enabled
  </div>

  <script>
    var channelID=%d
    op(null, -1);
  </script>
</body>

</html>""" % (channel.name(), channel.description(), channel.id())).encode("utf-8")

class MyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "MyHTTP/0.1"
    just_file = True

    replies_re = re.compile("/replies/(-?\d+)$")
    channel_re = re.compile("/channels/(\d+)$")

    def log_request(self, code):
        pass

    def get_field_storage(self, method):
        qs = urlparse.urlparse(self.path).query
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':method,
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     'QUERY_STRING': qs
                     })
        return form

    def do_POST(self):
        # Parse the form data posted

        form = self.get_field_storage("POST")
        # Begin the response
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Client: %s\n' % str(self.client_address))
        self.wfile.write('Path: %s\n' % self.path)
        self.wfile.write('Form data:\n')

        # Echo back information about what was posted in the form
        for field in form.keys():
            field_item = form[field]
            if field_item.filename:
                # The field contains an uploaded file
                file_data = field_item.file.read()
                file_len = len(file_data)
                del file_data
                self.wfile.write('\tUploaded %s (%d bytes)\n' % (field, 
                                                                 file_len))
            else:
                # Regular form value
                self.wfile.write('\t%s=%s\n' % (field, form[field].value))
        return

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()

        if f:
            if self.just_file:
                self.copyfile(f, self.wfile)
                f.close()
            else:
                self.wfile.write(f)

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f and self.just_file:
            f.close()

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """

        if self.replies_re.match(self.path):
            self.just_file = False
            response = get_html_replies(self.replies_re.match(self.path).group(1))

        if self.channel_re.match(self.path):
            self.just_file = False
            board.update()
            response = get_html_channel(self.channel_re.match(self.path).group(1))

        if not self.just_file:
            if not response:
                self.send_error(404, "File not found")
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            return response



        if self.path == "/":
            self.path = "/index.html"
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            self.send_error(404, "File not found")
            return None
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f


    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd() + "/html/"
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.

        The SOURCE argument is a file object open for reading
        (or anything with a read() method) and the DESTINATION
        argument is a file object open for writing (or
        anything with a write() method).

        The only reason for overriding this would be to change
        the block size or perhaps to replace newlines by CRLF
        -- note however that this the default server uses this
        to copy binary data as well.

        """
        shutil.copyfileobj(source, outputfile)

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })


if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description="interface to pynlc")
    argParser.add_argument("-g", help="GUI interface")
    argParser.add_argument("-d", help="debug", action="store_const",
                           dest="debug", const=True, default=False)
    args = argParser.parse_args()
    if args.debug:
        logging.basicConfig(filename="log", 
                            level=logging.DEBUG,
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logging.debug("pynlc-web started")


    core = None
    nick = getuser()
    profiler = hpy()
    try:
        core = ClientCore(config.SERVER)
        board = Board(core.send)
        auth = Authentificator(core.send)
        core.set_handler('d', board.handle_update)
        core.set_handler('R', auth.handle_request)
        core.set_handler('bfs', print_function)
        core.start()

        board.update()

        board.wait_for_channels()

        HandlerClass = MyRequestHandler
        ServerClass  = BaseHTTPServer.HTTPServer
        Protocol     = "HTTP/1.0"

        server_address = ('127.0.0.1', 8001)

        HandlerClass.protocol_version = Protocol
        httpd = ServerClass(server_address, HandlerClass)

        sa = httpd.socket.getsockname()
        print "Serving HTTP on", sa[0], "port", sa[1], "..."
        httpd.serve_forever()


    except:
        print "Unhandled exception:"
        traceback.print_exc()
        print "Exiting..."

    finally:
        core.stop_and_wait()
