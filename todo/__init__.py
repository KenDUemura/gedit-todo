# Copyright (C) 2007 - Nando Vieira
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# 2007-10-25 - Alexandre da Silva <simpsomboy@gmail.com>
# Obtained original program from Nando Vieira, and changed need use only
# python and mozembed, removed not used code

import os
import re
import urllib

from gettext import gettext as _
from gi.repository import Gdk, GObject, Gedit, Gio, Gtk, WebKit
from todo import parse_directory


DEBUG_NAME = 'TODO_DEBUG'
DEBUG_TITLE = 'todo'

ui_str = """
<ui>
    <menubar name="MenuBar">
        <menu name="ViewMenu" action="View">
            <menuitem name="ToDo" action="ToDo"/>
        </menu>
    </menubar>
</ui>
"""


class BrowserPage(WebKit.WebView):
    def __init__(self):
        WebKit.WebView.__init__(self)


def debug(text, level=1):
    if os.environ.has_key(DEBUG_NAME):
        try:
            required_level = int(os.environ[DEBUG_NAME])

            if required_level >= level:
                print "[%s] %s" % (DEBUG_TITLE, text)
        except:
            print "[%s] debug error" % DEBUG_TITLE


# TODO: Create a Configuration dialog
class TodoPlugin(GObject.Object, Gedit.WindowActivatable):

    __gtype_name__ = "TodoPlugin"

    window = GObject.property(type=Gedit.Window)

    handlers = {}

    mt = re.compile(r'(?P<protocol>^gedit:\/\/\/)(?P<file>.*?)\?line=(?P<line>.*?)$')

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.todo_window = None
        self._browser = None
        self.add_menu()

    def do_deactivate(self):
        self._browser = None
        self.todo_window = None

    def do_update_state(self):
        pass

    def add_menu(self):
        actions = [
            ('ToDo', Gtk.STOCK_EDIT, _('TODO-List'), '<Shift><Alt>t',
             _("List all TODO marks from your current project"),
             self.show_todo_marks)
        ]

        action_group = Gtk.ActionGroup("ToDoActions")
        action_group.add_actions(actions, self.window)

        self.manager = self.window.get_ui_manager()
        self.manager.insert_action_group(action_group, -1)
        self.manager.add_ui_from_string(ui_str)

    def get_root_directory(self):
        # get filebrowser plugin root
        fb_root = self.get_filebrowser_root()
        if fb_root and fb_root != "" and fb_root is not None:
            title = "TODO List (Filebrowser integration)"
            root = fb_root
        else:
            title = "TODO List (current directory)"
            root = os.path.dirname(__file__)

        rt_path = urllib.unquote(root.replace("file://", ""))
        return (rt_path, title)

    def get_filebrowser_root(self):
        """ Get path to current filebrowser root. """
        settings = Gio.Settings.new('org.gnome.gedit.plugins.filebrowser')
        virtual_root = settings.get_string('virtual-root')#.split('file://')[1]
        return virtual_root

    def show_todo_marks(self, *args):
        # getting variables
        root, title = self.get_root_directory()
        html_str = parse_directory(root)

        if self.todo_window:
            self.todo_window.show()
            self.todo_window.grab_focus()
        else:
            self._browser = BrowserPage()
            self._browser.connect('navigation-requested',
                                  self.on_navigation_request)
            self.todo_window = Gtk.Window()
            self.todo_window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
            self.todo_window.resize(700,510)
            self.todo_window.connect('delete_event', self.on_todo_close)
            self.todo_window.connect("key-release-event", self.on_window_key)
            self.todo_window.set_destroy_with_parent(True)
            self.todo_window.add(self._browser)
            self.todo_window.show_all()

        self.todo_window.set_title(title)
        self._browser.load_string(html_str, "text/html", "utf-8", "file://")

    def on_todo_close(self, *args):
        self.todo_window.hide()
        return True

    def on_window_key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.todo_window.hide()

    def on_navigation_request(self, page, frame, request):
        file_uri = None
        uri = request.get_uri()
        gp = self.mt.search(uri)
        if gp:
            file_uri = 'file://%s' % gp.group('file')
            line_number = gp.group('line')
            if file_uri:
                # Test if document is already open
                for doc in self.window.get_documents():
                    doc_uri = 'file://%s' % doc.get_uri_for_display()
                    if doc_uri == file_uri:
                        tab = Gedit.Tab.get_from_document(doc)
                        view = tab.get_view()
                        self.window.set_active_tab(tab)
                        doc.goto_line(int(line_number))
                        view.scroll_to_cursor()
                        self.todo_window.hide()
                        return 1
                # Document isn't open, create a new tab from uri
                file_uri = Gio.file_new_for_uri(file_uri)
                self.window.create_tab_from_location(file_uri,
                                                     Gedit.encoding_get_current(),
                                                     int(line_number),
                                                     0, False, True)
                self.todo_window.hide()
                return 1
        else:
            #self.todo_window.hide()
            return 0

    def set_data(self, name, value):
        self.window.get_active_tab().get_view().set_data(name, value)

    def get_data(self, name):
        return self.window.get_active_tab().get_view().get_data(name)
