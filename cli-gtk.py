#!/usr/bin/python
# -*- coding: utf-8 -*-
# 
# Copyright 2010 Aleksey Sergushichev <alsergbox@gmail.com>
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

import sys
import threading
import os
import traceback
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

import pygtk
pygtk.require('2.0')
import gtk
import gobject

ui_info = \
'''<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menuitem action='Update'/>
      <separator/>
      <menuitem action='Quit'/>
    </menu>
    <menu action='PreferencesMenu'>
    </menu>
    <menu action='HelpMenu'>
      <menuitem action='About'/>
    </menu>
  </menubar>
</ui>'''


class NetLandGTK(gtk.Window):
    def __init__(self, parent=None):
        self._channels_trees = {}

        gtk.gdk.threads_init()
        gtk.Window.__init__(self)
        try:
            self.set_screen(parent.get_screen())
        except AttributeError:
            self.connect('destroy', lambda *w: gtk.main_quit() )
        self.set_title("NetLand Client GTK")
        self.set_default_size(640, 480)

        merge = gtk.UIManager()
        self.set_data("ui-manager", merge)
        merge.insert_action_group(self.create_action_group(), 0)
        self.add_accel_group(merge.get_accel_group())

        try:
            mergeid = merge.add_ui_from_string(ui_info)
        except gobject.GError, msg:
            print "building menus failed: %s" % msg
        bar = merge.get_widget("/MenuBar")
        bar.show()
               
        table = gtk.Table(1, 4, False)
        self.add(table)

        table.attach(bar,
            # X direction #          # Y direction
            0, 1,                      0, 1,
            gtk.EXPAND | gtk.FILL,     0,
            0,                         0)
        
        self.board = gtk.Notebook()
        self.board.set_tab_pos(gtk.POS_BOTTOM)
        for channel_id in board._channels:
            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_IN)
            
            self._channels_trees[channel_id] = gtk.TreeStore(str)
            channel = [board.get_channel(channel_id)]
            sw.add(self.draw_channel(channel, self._channels_trees[channel_id]))
            
            label = gtk.Label("/".join([node.name()[1:] for node in channel]))
            label.show()
            self.board.append_page(sw, label)
        self.board.show()

        table.attach(self.board,
            # X direction           Y direction
            0, 1,                   2, 3,
            gtk.EXPAND | gtk.FILL,  gtk.EXPAND | gtk.FILL,
            0,                      0)
        
        statusbar = gtk.Statusbar()
        statusbar.show()
        context_id = statusbar.get_context_id("Statusbar")
        statusbar.push(context_id, "Statusbar")

        table.attach(statusbar,
            # X direction           Y direction
            0, 1,                   3, 4,
            gtk.EXPAND | gtk.FILL,  0,
            0,                      0)
        
        self.show_all()

    def create_action_group(self):
        entries = (
          ( "FileMenu", None, "_Файл" ),
          ( "PreferencesMenu", None, "_Настройки" ),
          ( "HelpMenu", None, "_Справка" ),
          ( "Update", gtk.STOCK_REFRESH,
            "_Обновить", "<control>U",
            "Update",
            self.update_channels_trees ),
          ( "Quit", gtk.STOCK_QUIT,
            "_Выход", "<control>Q",
            "Quit",
            lambda *w: gtk.main_quit() ),
          ( "About", gtk.STOCK_ABOUT,
            "_О программе", "<control>A",
            "About",
            self.activate_about ),
        );
        action_group = gtk.ActionGroup("AppWindowActions")
        action_group.add_actions(entries)
        return action_group

    def draw_channel(self, channel, channel_tree):
        treeview = gtk.TreeView(channel_tree)
        channel_name = "/".join([node.name()[1:] for node in channel])
        channel_name += " :: "+"/".join([node.description() for node in channel])
        tvcolumn = gtk.TreeViewColumn(channel_name)
        treeview.append_column(tvcolumn)
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'text', 0)
        treeview.set_search_column(0)
        return treeview
    
    def update_channels_trees(self, action):
        for channel_id in board._channels:
            channel = [board.get_channel(channel_id)]
            for msg in channel[-1].iterreplies():
                self._channels_trees[channel_id].append(None, ['<b>%s :: <i>%s</i></b>\n%s' % (msg.nick(), msg.post_time().ctime(), msg.body())])

    def activate_about(self, action):
        dialog = gtk.AboutDialog()
        dialog.set_name("PyNLC GTK")
        dialog.set_copyright("\302\251 Copyright 201x the PyNLC Team")
        dialog.set_website("http://")
        dialog.connect ("response", lambda d, r: d.destroy())
        dialog.show()


if __name__ == "__main__":
    core = None
    nick = getuser()
    profiler = hpy()

    core = ClientCore(config.SERVER)
    board = Board(core.send)
    auth = Authentificator(core.send)

    core.set_handler('d', board.handle_update)
    core.set_handler('R', auth.handle_request)
    core.set_handler('bfs', print_function)
    core.start()

    board.update()
    board.wait_for_channels()

    NetLandGTK()
    gtk.main()

    core.stop_and_wait()
