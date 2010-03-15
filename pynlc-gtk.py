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

class NetLandGTK(gtk.Window):
    """
        GTK interface.
    """
    def __init__(self, parent=None):
        """
            Create GTK interface.
        """
        gtk.gdk.threads_init()
        gtk.Window.__init__(self)
        try:
            self.set_screen(parent.get_screen())
        except AttributeError:
            self.connect('destroy', lambda *w: gtk.main_quit() )
        
        self.set_title("NetLand Client GTK")
        self.set_default_size(640, 480)

        table = gtk.Table(1, 4, False)
        table.attach( self.create_bar(),
            # X direction #          # Y direction
            0, 1,                      0, 1,
            gtk.EXPAND | gtk.FILL,     0,
            0,                         0)
        table.attach( self.create_board(),
            # X direction           Y direction
            0, 1,                   2, 3,
            gtk.EXPAND | gtk.FILL,  gtk.EXPAND | gtk.FILL,
            0,                      0)
        table.attach( self.create_statusbar(),
            # X direction           Y direction
            0, 1,                   3, 4,
            gtk.EXPAND | gtk.FILL,  0,
            0,                      0)        
        self.add(table)
        self.show_all()

    def create_action_group(self):
        """
            Create action group for menubar.
        """
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

    def create_bar(self):
        """
            Create menubar.
        """
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
        return bar

    def create_board(self):
        """
            Create gtk.Notebook with board.
        """
        self.board = gtk.Notebook()
        self.board.set_tab_pos(gtk.POS_BOTTOM)
        for channel_id in board._channels:
            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_IN)
            
            board._channels[channel_id].tree = gtk.TreeStore(str)
            channel_tree = gtk.TreeView(board._channels[channel_id].tree)
            channel = [board._channels[channel_id]]
            channel_name = "/".join([node.name()[1:] for node in channel]) + " :: "+"/".join([node.description() for node in channel])
            column = gtk.TreeViewColumn(channel_name)
            channel_tree.append_column(column)
            channel_tree.set_enable_tree_lines(True)
            cell = gtk.CellRendererText()
            '''
            cell.set_property('editable', True)
            '''
            column.pack_start(cell, True)
            column.add_attribute(cell, 'text', 0)
            channel_tree.set_search_column(0)
            channel_tree.connect("row-activated", self.get_internal_messages, channel_id)
            sw.add(channel_tree)
            
            label = gtk.Label("/".join([node.name()[1:] for node in channel]))
            label.show()
            self.board.append_page(sw, label)
        self.board.show()
        return self.board

    def create_statusbar(self):
        """
            Create simple statusbar.
        """
        statusbar = gtk.Statusbar()
        statusbar.show()
        context_id = statusbar.get_context_id("Statusbar")
        statusbar.push(context_id, "Statusbar")
        return statusbar

    def update_channels_trees(self, action):
        """
            Update information on board.
        """
        board.update()
        for channel_id in board._channels:
            board._channels[channel_id].tree.clear()
            channel = [board.get_channel(channel_id)]
            for msg in channel[-1].iterreplies():
                board._messages[msg.id()].tree_id = board._channels[channel_id].tree.append(None, ['%s :: %s | %s\n%s' % (msg.nick(), msg.IP(), msg.post_time().ctime(), msg.body())])

    def get_internal_messages(self, treeview, patch, column, channel_id):
        """
            Get and draw internal messages.
        """
        head_message = [board.get_channel(channel_id)][-1]
        for pos in patch:
            head_message = head_message.replies()[pos]
        for msg in head_message.iterreplies():
            try:
                board._messages[msg.id()].tree_id
            except:
                board._messages[msg.id()].tree_id = board._channels[channel_id].tree.append(board._messages[msg.parent_id()].tree_id, ['%s :: %s | %s\n%s' % (msg.nick(), msg.IP(), msg.post_time().ctime(), msg.body())])

    def activate_about(self, action):
        """
            Show window with about information.
        """
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
