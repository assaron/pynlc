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
from util import print_function, get_channel_name
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
            self.connect('destroy', lambda *w: gtk.main_quit())
        
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
          ( "Profile", gtk.STOCK_PROPERTIES,
            "_Профиль", "<control>P",
            "Profile",
            self.show_profile_window ),
          ( "About", gtk.STOCK_ABOUT,
            "_О программе", "<control>A",
            "About",
            self.show_about_window ),
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
      <menuitem action='Profile'/>
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
        for channel in board.channels_list():
            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            sw.set_shadow_type(gtk.SHADOW_NONE)
            
            channel.tree = gtk.Table()
            channel.tree.show()
            channel.vp = gtk.Viewport()
            channel.vp.set_shadow_type(gtk.SHADOW_IN)
            channel.vp.add(channel.tree)
            sw.add(channel.vp)
            
            name = gtk.Label(get_channel_name(channel))
            name.show()
            frame = gtk.Frame()
            frame.set_label(get_channel_name(channel, True))
            frame.add(sw)
            self.board.append_page(frame, name)
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
        i = 0
        for channel in board.channels_list():
            channel.tree.destroy()
            channel.tree = gtk.Table()
            channel.tree.show()
            channel.vp.add(channel.tree)
            for msg in channel.iterreplies():
                channel.tree.attach( self.create_msg_table(msg),
                    # X direction #          # Y direction
                    0, 1,                      i, i+1,
                    gtk.EXPAND | gtk.FILL,     0,
                    5,                         5)
                i = i + 1

    def get_internal_messages(self, widget, msg_table):
        """
            Get and draw internal messages.
        """
        msg_table.bar.show()
        int_table = gtk.Table()
        message = board.get_message(msg_table.id)
        i = 0
        for msg in message.iterreplies():
            int_table.attach( self.create_msg_table(msg),
                # X direction #          # Y direction
                0, 1,                      i, i+1,
                gtk.EXPAND | gtk.FILL,     0,
                5,                         5)
            i = i + 1
        msg_table.bar.destroy()
        msg_table.button.destroy()
        msg_table.attach( int_table,
            # X direction #          # Y direction
            0, 2,                      1, 2,
            gtk.EXPAND | gtk.FILL,     0,
            0,                         0)
        int_table.show()

    def create_msg_table(self, msg):
        """
            Create and return message table.
        """
        msg_table = gtk.Table(2, 2, False)
        msg_table.id = msg.id()

        msg_frame = gtk.Frame()
        msg_frame.set_label(
            '%s :: %s | %s' %
            (msg.nick(), msg.IP(),
            msg.post_time().ctime()))
        msg_body = gtk.TextView()
        msg_body.set_wrap_mode(gtk.WRAP_WORD)
        msg_body.set_editable(False)
        buf = msg_body.get_buffer()
        iter = buf.get_iter_at_offset(0)
        buf.insert(iter, msg.body());
        msg_body.show()
        msg_frame.add(msg_body)
        msg_frame.show()
        msg_table.attach( msg_frame,
            # X direction #          # Y direction
            0, 2,                      0, 1,
            gtk.EXPAND | gtk.FILL,     0,
            0,                         0)
        
        if True: 
            ''' 
                Вместо тру нужен метод проверки вложений 
            '''
            msg_table.button = gtk.Button("+")
            msg_table.button.connect("clicked", self.get_internal_messages, msg_table)
            msg_table.button.show()
            msg_table.bar = gtk.ProgressBar()
            msg_table.attach( msg_table.button,
                # X direction #          # Y direction
                0, 1,                      1, 2,
                0,                         0,
                0,                         0)
            msg_table.attach( msg_table.bar,
                # X direction #          # Y direction
                1, 2,                      1, 2,
                gtk.EXPAND | gtk.FILL,     0,
                20,                        0)
        msg_table.bar.show()
        msg_table.show()
        return msg_table
    
    def show_profile_window(self, action):
        """
            Show window with profile settings.
        """
        global nick
        dialog = gtk.Dialog("Настройки профиля", self, 0,
                        (gtk.STOCK_OK, gtk.RESPONSE_OK,))
        
        hbox = gtk.HBox(False, 8)
        hbox.set_border_width(8)
        dialog.vbox.pack_start(hbox, False, False, 0)
        
        table = gtk.Table(2, 1)
        table.set_row_spacings(4)
        table.set_col_spacings(4)
        hbox.pack_start(table, True, True, 0)
        label = gtk.Label("Ник:")
        label.set_use_underline(True)
        table.attach(label, 0, 1, 0, 1)
        
        nick_entry = gtk.Entry()
        nick_entry.set_text(nick)
        table.attach(nick_entry, 1, 2, 0, 1)
        
        label.set_mnemonic_widget(nick_entry)
        dialog.show_all()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            nick = nick_entry.get_text()
        dialog.destroy()

    def show_about_window(self, action):
        """
            Show window with about information.
        """
        dialog = gtk.AboutDialog()
        dialog.set_name("PyNLC GTK")
        dialog.set_copyright("\302\251 Copyright 201x the PyNLC Team")
        dialog.set_website("http://csm/git")
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
