#!/usr/bin/env python

# Uzbl tabbing wrapper using a fifo socket interface
# Copyright (c) 2009, Tom Adams <tom@holizz.com>
# Copyright (c) 2009, Chris van Dijk <cn.vandijk@hotmail.com>
# Copyright (c) 2009, Mason Larobina <mason.larobina@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Author(s):
#   Tom Adams <tom@holizz.com>
#       Wrote the original uzbl_tabbed.py as a proof of concept.
#
#   Chris van Dijk (quigybo) <cn.vandijk@hotmail.com>
#       Made signifigant headway on the old uzbl_tabbing.py script on the
#       uzbl wiki <http://www.uzbl.org/wiki/uzbl_tabbed>
#
#   Mason Larobina <mason.larobina@gmail.com>
#       Rewrite of the uzbl_tabbing.py script to use a fifo socket interface
#       and inherit configuration options from the user's uzbl config.
#
# Contributor(s):
#   mxey <mxey@ghosthacking.net>
#       uzbl_config path now honors XDG_CONFIG_HOME if it exists.
#
#   Romain Bignon <romain@peerfuse.org>
#       Fix for session restoration code.
#
#   Jake Probst <jake.probst@gmail.com>
#       Wrote a patch that overflows tabs in the tablist on to new lines when
#       running of room.
#
#   Devon Jones <devon.jones@gmail.com>
#       Fifo command bring_to_front which brings the gtk window to focus.
#
#   Simon Lipp (sloonz)
#       Various


# Dependencies:
#   pygtk - python bindings for gtk.
#   pango - python bindings needed for text rendering & layout in gtk widgets.
#   pygobject - GLib's GObject bindings for python.
#
# Note: I haven't included version numbers with this dependency list because
# I've only ever tested uzbl_tabbed.py on the latest stable versions of these
# packages in Gentoo's portage. Package names may vary on different systems.


# Configuration:
# Because this version of uzbl_tabbed is able to inherit options from your main
# uzbl configuration file you may wish to configure uzbl tabbed from there.
# Here is a list of configuration options that can be customised and some
# example values for each:
#
# General tabbing options:
#   show_tablist            = 1
#   show_gtk_tabs           = 0
#   tablist_top             = 1
#   gtk_tab_pos             = (top|left|bottom|right)
#   gtk_refresh             = 1000
#   switch_to_new_tabs      = 1
#   multiline_tabs          = 1
#
# Tab title options:
#   tab_titles              = 1
#   tab_indexes             = 1
#   new_tab_title           = Loading
#   max_title_len           = 50
#   show_ellipsis           = 1
#
# Session options:
#   save_session            = 1
#   json_session            = 0
#   session_file            = $HOME/.local/share/uzbl/session
#
# Inherited uzbl options:
#   icon_path               = $HOME/.local/share/uzbl/uzbl.png
#   status_background       = #303030
#
# Misc options:
#   window_size             = 800,800
#   verbose                 = 0
#
# And uzbl_tabbed.py takes care of the actual binding of the commands via each
# instances fifo socket.
#
# Custom tab styling:
#   tab_colours             = foreground = "#888" background = "#303030"
#   tab_text_colours        = foreground = "#bbb"
#   selected_tab            = foreground = "#fff"
#   selected_tab_text       = foreground = "green"
#   tab_indicate_https      = 1
#   https_colours           = foreground = "#888"
#   https_text_colours      = foreground = "#9c8e2d"
#   selected_https          = foreground = "#fff"
#   selected_https_text     = foreground = "gold"
#
# How these styling values are used are soley defined by the syling policy
# handler below (the function in the config section). So you can for example
# turn the tab text colour Firetruck-Red in the event "error" appears in the
# tab title or some other arbitrary event. You may wish to make a trusted
# hosts file and turn tab titles of tabs visiting trusted hosts purple.


# Issues:
#   - new windows are not caught and opened in a new tab.
#   - when uzbl_tabbed.py crashes it takes all the children with it.
#   - when a new tab is opened when using gtk tabs the tab button itself
#     grabs focus from its child for a few seconds.
#   - when switch_to_new_tabs is not selected the notebook page is
#     maintained but the new window grabs focus (try as I might to stop it).


# Todo:
#   - add command line options to use a different session file, not use a
#     session file and or open a uri on starup.
#   - ellipsize individual tab titles when the tab-list becomes over-crowded
#   - add "<" & ">" arrows to tablist to indicate that only a subset of the
#     currently open tabs are being displayed on the tablist.
#   - add the small tab-list display when both gtk tabs and text vim-like
#     tablist are hidden (I.e. [ 1 2 3 4 5 ])
#   - check spelling.
#   - pass a uzbl socketid to uzbl_tabbed.py and have it assimilated into
#     the collective. Resistance is futile!


import pygtk
import gtk
import subprocess
import os
import re
import time
import getopt
import pango
import select
import sys
import gobject
import socket
import random
import hashlib
import atexit
import types

from gobject import io_add_watch, source_remove, timeout_add, IO_IN, IO_HUP
from signal import signal, SIGTERM, SIGINT
from optparse import OptionParser, OptionGroup
from traceback import print_exc


pygtk.require('2.0')

_SCRIPTNAME = os.path.basename(sys.argv[0])
def error(msg):
    sys.stderr.write("%s: error: %s\n" % (_SCRIPTNAME, msg))

# ============================================================================
# ::: Default configuration section ::::::::::::::::::::::::::::::::::::::::::
# ============================================================================

def xdghome(key, default):
    '''Attempts to use the environ XDG_*_HOME paths if they exist otherwise
    use $HOME and the default path.'''

    xdgkey = "XDG_%s_HOME" % key
    if xdgkey in os.environ.keys() and os.environ[xdgkey]:
        return os.environ[xdgkey]

    return os.path.join(os.environ['HOME'], default)

# Setup xdg paths.
DATA_DIR = os.path.join(xdghome('DATA', '.local/share/'), 'uzbl/')

# Ensure uzbl xdg paths exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# All of these settings can be inherited from your uzbl config file.
config = {
  # Tab options
  'show_tablist':           True,   # Show text uzbl like statusbar tab-list
  'show_gtk_tabs':          False,  # Show gtk notebook tabs
  'tablist_top':            True,   # Display tab-list at top of window
  'gtk_tab_pos':            'top',  # Gtk tab position (top|left|bottom|right)
  'gtk_refresh':            1000,   # Tablist refresh millisecond interval
  'switch_to_new_tabs':     True,   # Upon opening a new tab switch to it
  'multiline_tabs':         True,   # Tabs overflow onto new tablist lines.

  # Tab title options
  'tab_titles':             True,   # Display tab titles (else only tab-nums)
  'tab_indexes':             True,   # Display tab nums (else only tab titles)
  'new_tab_title':          'Loading', # New tab title
  'max_title_len':          50,     # Truncate title at n characters
  'show_ellipsis':          True,   # Show ellipsis when truncating titles

  # Session options
  'save_session':           True,   # Save session in file when quit
  'saved_sessions_dir':     os.path.join(DATA_DIR, 'sessions/'),
  'session_file':           os.path.join(DATA_DIR, 'session'),

  # Inherited uzbl options
  'icon_path':              os.path.join(DATA_DIR, 'uzbl.png'),
  'status_background':      "#303030", # Default background for all panels.

  # Misc options
  'window_size':            "800,800", # width,height in pixels.
  'verbose':                False,  # Print verbose output.

  # Add custom tab style definitions to be used by the tab colour policy
  # handler here. Because these are added to the config dictionary like
  # any other uzbl_tabbed configuration option remember that they can
  # be superseeded from your main uzbl config file.
  'tab_colours':            'foreground = "#888" background = "#303030"',
  'tab_text_colours':       'foreground = "#bbb"',
  'selected_tab':           'foreground = "#fff"',
  'selected_tab_text':      'foreground = "green"',
  'tab_indicate_https':     True,
  'https_colours':          'foreground = "#888"',
  'https_text_colours':     'foreground = "#9c8e2d"',
  'selected_https':         'foreground = "#fff"',
  'selected_https_text':    'foreground = "gold"',

} # End of config dict.

UZBL_TABBED_VARS = config.keys()

# This is the tab style policy handler. Every time the tablist is updated
# this function is called to determine how to colourise that specific tab
# according the simple/complex rules as defined here. You may even wish to
# move this function into another python script and import it using:
#   from mycustomtabbingconfig import colour_selector
# Remember to rename, delete or comment out this function if you do that.

def colour_selector(tabindex, currentpage, uzbl):
    '''Tablist styling policy handler. This function must return a tuple of
    the form (tab style, text style).'''

    # Just as an example:
    # if 'error' in uzbl.title:
    #     if tabindex == currentpage:
    #         return ('foreground="#fff"', 'foreground="red"')
    #     return ('foreground="#888"', 'foreground="red"')

    # Style tabs to indicate connected via https.
    if config['tab_indicate_https'] and uzbl.uri.startswith("https://"):
        if tabindex == currentpage:
            return (config['selected_https'], config['selected_https_text'])
        return (config['https_colours'], config['https_text_colours'])

    # Style to indicate selected.
    if tabindex == currentpage:
        return (config['selected_tab'], config['selected_tab_text'])

    # Default tab style.
    return (config['tab_colours'], config['tab_text_colours'])

# ============================================================================
# ::: End of configuration section :::::::::::::::::::::::::::::::::::::::::::
# ============================================================================

def echo(msg):
    if config['verbose']:
        sys.stderr.write("%s: %s\n" % (_SCRIPTNAME, msg))


def counter():
    '''To infinity and beyond!'''

    i = 0
    while True:
        i += 1
        yield i


def escape(s):
    '''Replaces html markup in tab titles that screw around with pango.'''

    for (split, glue) in [('&','&amp;'), ('<', '&lt;'), ('>', '&gt;')]:
        s = s.replace(split, glue)
    return s

class SocketClient:
    '''Represents a connection to the uzbl-tabbed socket.'''

    # List of UzblInstance objects not already linked with a SocketClient
    instances_queue = {}

    def __init__(self, socket, uzbl_tabbed):
        self._buffer = ""
        self._socket = socket
        self._watchers = [io_add_watch(socket, IO_IN, self._socket_recv),\
          io_add_watch(socket, IO_HUP, self._socket_closed)]

        self.uzbl = None
        self.uzbl_tabbed = uzbl_tabbed
        self.dispatcher = GlobalEventDispatcher(uzbl_tabbed)


    def _socket_recv(self, fd, condition):
        '''Data available on socket, process it'''

        self._feed(self._socket.recv(1024)) #TODO: is io_add_watch edge or level-triggered ?
        return True


    def _socket_closed(self, fd, condition):
        '''Remote client exited'''
        self.uzbl.close()
        return False


    def _feed(self, data):
        '''An Uzbl instance sent some data, parse it'''

        self._buffer += data

        if "\n" in self._buffer:
            cmds = self._buffer.split("\n")

            if cmds[-1]: # Last command has been received incomplete, don't process it
                self._buffer, cmds = cmds[-1], cmds[:-1]
            else:
                self._buffer = ""

            for cmd in cmds:
                if cmd:
                    self.handle_event(cmd)

    def handle_event(self, cmd):
        cmd = parse_event(cmd)
        message, instance_name, message_type = cmd[0:3]
        args = cmd[3:]

        if not message == "EVENT":
            return

        # strip the surrounding []
        instance_name = instance_name[1:-1]

        if self.uzbl:
            if not self.dispatcher.dispatch(message_type, args):
                self.uzbl.dispatcher.dispatch(message_type, args)
        elif message_type == 'INSTANCE_START':
            uzbl = self.instances_queue.get(instance_name)
            if uzbl:
                # we've found the uzbl we were waiting for
                del self.instances_queue[instance_name]
            else:
                # an unsolicited uzbl has connected, how exciting!
                uzbl = UzblInstance(self.uzbl_tabbed, None, '', '', False)
            self.uzbl = uzbl
            self.uzbl.got_socket(self)
            self._feed("")

    def send(self, data):
        '''Child socket send function.'''

        self._socket.send(data + "\n")

    def close(self):
        '''Close the connection'''

        if self._socket:
            self._socket.close()
            self._socket = None
            map(source_remove, self._watchers)
            self._watchers = []


def unquote(s):
    '''Removes quotation marks around strings if any and interprets
    \\-escape sequences using `string_escape`'''
    if s and s[0] == s[-1] and s[0] in ['"', "'"]:
        s = s[1:-1]
    return s.encode('utf-8').decode('string_escape').decode('utf-8')

_splitquoted = re.compile("( |\"(?:\\\\.|[^\"])*?\"|'(?:\\\\.|[^'])*?')")
def parse_event(text):
    '''Splits string on whitespace while respecting quotations'''
    return [unquote(p) for p in _splitquoted.split(text) if p.strip()]

class EventDispatcher:
    def dispatch(self, message_type, args):
        '''Returns True if the message was handled, False otherwise.'''

        method = getattr(self, message_type.lower(), None)

        if method is None:
            return False

        method(*args)
        return True

class GlobalEventDispatcher(EventDispatcher):
    def __init__(self, uzbl_tabbed):
        self.uzbl_tabbed = uzbl_tabbed

    def new_tab(self, uri = ''):
        self.uzbl_tabbed.new_tab(uri)

    def new_tab_bg(self, uri = ''):
        self.uzbl_tabbed.new_tab(uri, switch = False)

    def new_tab_next(self, uri = ''):
        self.uzbl_tabbed.new_tab(uri, next=True)

    def new_bg_tab_next(self, uri = ''):
        self.uzbl_tabbed.new_tab(uri, switch = False, next = True)

    def next_tab(self, step = 1):
        self.uzbl_tabbed.next_tab(int(step))

    def prev_tab(self, step = 1):
        self.uzbl_tabbed.prev_tab(int(step))

    def goto_tab(self, index):
        self.uzbl_tabbed.goto_tab(int(index))

    def first_tab(self):
        self.uzbl_tabbed.goto_tab(0)

    def last_tab(self):
        self.uzbl_tabbed.goto_tab(-1)

    def preset_tabs(self, *args):
        self.uzbl_tabbed.run_preset_command(*args)

    def bring_to_front(self):
        self.uzbl_tabbed.window.present()

    def clean_tabs(self):
        self.uzbl_tabbed.clean_slate()

    def exit_all_tabs(self):
        self.uzbl_tabbed.quitrequest()

class InstanceEventDispatcher(EventDispatcher):
    def __init__(self, uzbl):
        self.uzbl   = uzbl
        self.parent = self.uzbl.parent

    def plug_created(self, plug_id):
        if not self.uzbl.tab:
            tab = self.parent.create_tab()
            tab.add_id(int(plug_id))
            self.uzbl.set_tab(tab)

    def title_changed(self, title):
        self.uzbl.title = title.strip()
        self.uzbl.title_changed(False)

    def variable_set(self, var, _type, val):
        try:
            val = int(val)
        except:
            pass

        if var in UZBL_TABBED_VARS:
            if config[var] != val:
                config[var] = val
                if var == "show_gtk_tabs":
                    self.parent.notebook.set_show_tabs(bool(val))
                elif var == "show_tablist" or var == "tablist_top":
                    self.parent.update_tablist_display()
                elif var == "gtk_tab_pos":
                    self.parent.update_gtk_tab_pos()
                elif var == "status_background":
                    if config['status_background'].strip():
                        try:
                          col = gtk.gdk.color_parse(config['status_background'])
                          self.parent.ebox.modify_bg(gtk.STATE_NORMAL, col)
                        except ValueError:
                          pass # got an invalid colour, just ignore it
                elif var == "tab_titles" or var == "tab_indexes":
                    for tab in self.parent.notebook:
                        self.parent.tabs[tab].title_changed(True)

                self.parent.update_tablist()
        else:
            config[var] = val

        if var == "uri":
            self.uzbl.uri = val.strip()
            self.parent.update_tablist()

    def load_commit(self, uri):
        self.uzbl.uri = uri

class UzblInstance:
    '''Uzbl instance meta-data/meta-action object.'''

    def __init__(self, parent, name, uri, title, switch):

        self.parent = parent
        self.tab    = None
        self.dispatcher = InstanceEventDispatcher(self)

        self.name = name
        self.title = title
        self.tabtitle = ""
        self.uri = uri

        self._client = None
        self._switch = switch # Switch to tab after loading ?

    def set_tab(self, tab):
        self.tab = tab
        self.title_changed()
        self.parent.tabs[self.tab] = self

    def got_socket(self, client):
        '''Uzbl instance is now connected'''

        self._client = client
        self.parent.config_uzbl(self)
        if self._switch:
            tabid = self.parent.notebook.page_num(self.tab)
            self.parent.goto_tab(tabid)


    def title_changed(self, gtk_only = True): # GTK-only is for indexes
        '''self.title has changed, update the tabs list'''

        if not self.tab:
            return

        tab_titles = config['tab_titles']
        tab_indexes = config['tab_indexes']
        show_ellipsis = config['show_ellipsis']
        max_title_len = config['max_title_len']

        # Unicode heavy strings do not like being truncated/sliced so by
        # re-encoding the string sliced of limbs are removed.
        self.tabtitle = self.title[:max_title_len + int(show_ellipsis)]
        if type(self.tabtitle) != types.UnicodeType:
            self.tabtitle = unicode(self.tabtitle, 'utf-8', 'ignore')

        self.tabtitle = self.tabtitle.encode('utf-8', 'ignore').strip()

        if show_ellipsis and len(self.tabtitle) != len(self.title):
            self.tabtitle += "\xe2\x80\xa6"

        gtk_tab_format = "%d %s"
        index = self.parent.notebook.page_num(self.tab)
        if tab_titles and tab_indexes:
            self.parent.notebook.set_tab_label_text(self.tab,
              gtk_tab_format % (index, self.tabtitle))
        elif tab_titles:
            self.parent.notebook.set_tab_label_text(self.tab, self.tabtitle)
        else:
            self.parent.notebook.set_tab_label_text(self.tab, str(index))

        # If instance is current tab, update window title
        if index == self.parent.notebook.get_current_page():
            title_format = "%s - Uzbl Browser"
            self.parent.window.set_title(title_format % self.title)

        # Non-GTK tabs
        if not gtk_only:
            self.parent.update_tablist()


    def set(self, key, val):
        ''' Send the SET command to Uzbl '''

        if self._client:
            line = 'set %s = %s' % (key, val) #TODO: escape chars ?
            self._client.send(line)


    def exit(self):
        ''' Ask the Uzbl instance to close '''

        if self._client:
            self._client.send('exit')

    def close(self):
        '''The remote instance exited'''

        if self._client:
            self._client.close()
            self._client = None


class UzblTabbed:
    '''A tabbed version of uzbl using gtk.Notebook'''

    def __init__(self):
        '''Create tablist, window and notebook.'''

        self._timers = {}
        self._buffer = ""
        self._killed = False

        # A list of the recently closed tabs
        self._closed = []

        # Holds metadata on the uzbl childen open.
        self.tabs = {}

        # Uzbl sockets (socket => SocketClient)
        self.clients = {}

        # Generates a unique id for uzbl socket filenames.
        self.next_pid = counter().next

        # Whether to reconfigure new uzbl instances
        self.force_socket_dir = False
        self.force_fifo_dir   = False

        self.fifo_dir   = '/tmp' # Path to look for uzbl fifo.
        self.socket_dir = '/tmp' # Path to look for uzbl socket.

        # Create main window
        self.window = gtk.Window()
        try:
            window_size = map(int, config['window_size'].split(','))
            self.window.set_default_size(*window_size)

        except:
            print_exc()
            error("Invalid value for default_size in config file.")

        self.window.set_title("Uzbl Browser")
        self.window.set_border_width(0)

        # this prevents the window from expanding if the contents of the
        # statusbar are wider than the window.
        # i suspect this is not the right way to do this.
        self.window.set_geometry_hints(min_width=1)

        # Set main window icon
        icon_path = config['icon_path']
        if os.path.exists(icon_path):
            self.window.set_icon(gtk.gdk.pixbuf_new_from_file(icon_path))

        else:
            icon_path = '/usr/share/uzbl/examples/data/uzbl.png'
            if os.path.exists(icon_path):
                self.window.set_icon(gtk.gdk.pixbuf_new_from_file(icon_path))

        # Attach main window event handlers
        self.window.connect("delete-event", self.quitrequest)

        # Create tab list
        vbox = gtk.VBox()
        self.vbox = vbox
        self.window.add(vbox)
        ebox = gtk.EventBox()
        self.ebox = ebox
        self.tablist = gtk.Label()

        self.tablist.set_use_markup(True)
        self.tablist.set_justify(gtk.JUSTIFY_LEFT)
        self.tablist.set_line_wrap(False)
        self.tablist.set_selectable(False)
        self.tablist.set_padding(2,2)
        self.tablist.set_alignment(0,0)
        self.tablist.set_ellipsize(pango.ELLIPSIZE_END)
        self.tablist.set_text(" ")
        self.tablist.show()
        ebox.add(self.tablist)
        ebox.show()
        bgcolor = gtk.gdk.color_parse(config['status_background'])
        ebox.modify_bg(gtk.STATE_NORMAL, bgcolor)

        # Create notebook
        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(config['show_gtk_tabs'])

        # Set tab position
        self.update_gtk_tab_pos()

        self.notebook.set_show_border(False)
        self.notebook.set_scrollable(True)
        self.notebook.set_border_width(0)

        self.notebook.connect("page-removed", self.tab_closed)
        self.notebook.connect("switch-page", self.tab_changed)
        self.notebook.connect("page-added", self.tab_opened)
        self.notebook.connect("page-reordered", self.tab_reordered)

        self.notebook.show()
        vbox.pack_start(self.notebook, True, True, 0)
        vbox.reorder_child(self.notebook, 1)
        self.update_tablist_display()

        self.vbox.show()
        self.window.show()
        self.wid = self.notebook.window.xid

        # Store information about the application's socket.
        socket_filename = 'uzbltabbed_%d.socket' % os.getpid()
        self._socket = None
        self.socket_path = os.path.join(self.socket_dir, socket_filename)

        # Now initialise the the socket
        self.init_socket()

        # If we are using sessions then load the last one if it exists.
        if config['save_session']:
            self.load_session()


    def run(self):
        '''UzblTabbed main function that calls the gtk loop.'''

        if not self.clients and not SocketClient.instances_queue and not self.tabs:
            self.new_tab()

        gtk_refresh = int(config['gtk_refresh'])
        if gtk_refresh < 100:
            gtk_refresh = 100

        # Make SIGTERM act orderly.
        #signal(SIGTERM, lambda signum, stack_frame: self.terminate(SIGTERM))

        # Catch keyboard interrupts
        #signal(SIGINT, lambda signum, stack_frame: self.terminate(SIGINT))

        try:
            gtk.main()

        except:
            print_exc()
            error("encounted error %r" % sys.exc_info()[1])

            # Unlink socket
            self.close_socket()

            # Attempt to close all uzbl instances nicely.
            self.quitrequest()

            # Allow time for all the uzbl instances to quit.
            time.sleep(1)

            raise

    def terminate(self, termsig=None):
        '''Handle termination signals and exit safely and cleanly.'''

        # Not required but at least it lets the user know what killed his
        # browsing session.
        if termsig == SIGTERM:
            error("caught SIGTERM signal")

        elif termsig == SIGINT:
            error("caught keyboard interrupt")

        else:
            error("caught unknown signal")

        error("commencing infanticide!")

        # Sends the exit signal to all uzbl instances.
        self.quitrequest()


    def init_socket(self):
        '''Create interprocess communication socket.'''

        def accept(sock, condition):
            '''A new uzbl instance was created'''

            client, _ = sock.accept()
            self.clients[client] = SocketClient(client, self)

            return True

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.socket_path)
        sock.listen(1)

        # Add event handler for IO_IN event.
        self._socket = (sock, io_add_watch(sock, IO_IN, accept))

        echo("[socket] listening at %r" % self.socket_path)

        # Add atexit register to destroy the socket on program termination.
        atexit.register(self.close_socket)


    def close_socket(self):
        '''Close the socket when closing the application'''

        if self._socket:
            (fd, watcher) = self._socket
            source_remove(watcher)
            fd.close()
            os.unlink(self.socket_path)
            self._socket = None


    def run_preset_command(self, cmd, *args):
        if len(args) < 1:
            error("parse_command: invalid preset command")

        elif cmd == "save":
            path = os.path.join(config['saved_sessions_dir'], args[0])
            self.save_session(path)

        elif cmd == "load":
            path = os.path.join(config['saved_sessions_dir'], args[0])
            self.load_session(path)

        elif cmd == "del":
            path = os.path.join(config['saved_sessions_dir'], args[0])
            if os.path.isfile(path):
                os.remove(path)
            else:
                error("parse_command: preset %r does not exist." % path)

        elif cmd == "list":
            # FIXME: what argument is this supposed to be passed,
            # and why?
            uzbl = self.get_tab_by_name(int(args[0]))
            if uzbl:
                if not os.path.isdir(config['saved_sessions_dir']):
                    js = "js alert('No saved presets.');"
                    uzbl._client.send(js)

                else:
                    listdir = os.listdir(config['saved_sessions_dir'])
                    listdir = "\\n".join(listdir)
                    js = "js alert('Session presets:\\n\\n%s');" % listdir
                    uzbl._client.send(js)

            else:
                error("parse_command: unknown tab name.")

        else:
            error("parse_command: unknown parse command %r" % cmd)


    def get_tab_by_name(self, name):
        '''Return uzbl instance by name.'''

        for (tab, uzbl) in self.tabs.items():
            if uzbl.name == name:
                return uzbl

        return False

    def create_tab(self, beside = False):
        tab = gtk.Socket()
        tab.show()

        if beside:
            pos = self.notebook.get_current_page() + 1
            self.notebook.insert_page(tab, position=pos)
        else:
            self.notebook.append_page(tab)

        self.notebook.set_tab_reorderable(tab, True)
        return tab

    def new_tab(self, uri='', title='', switch=None, next=False):
        '''Add a new tab to the notebook and start a new instance of uzbl.
        Use the switch option to negate config['switch_to_new_tabs'] option
        when you need to load multiple tabs at a time (I.e. like when
        restoring a session from a file).'''

        tab = self.create_tab(next)
        sid = tab.get_id()
        uri = uri.strip()
        name = "%d-%d" % (os.getpid(), self.next_pid())

        if switch is None:
            switch = config['switch_to_new_tabs']

        if not title:
            title = config['new_tab_title']

        cmd = ['uzbl-browser', '-n', name, '-s', str(sid),
               '--connect-socket', self.socket_path]

        if(uri):
          cmd = cmd + ['--uri', str(uri)]

        gobject.spawn_async(cmd, flags=gobject.SPAWN_SEARCH_PATH)

        uzbl = UzblInstance(self, name, uri, title, switch)
        uzbl.set_tab(tab)

        SocketClient.instances_queue[name] = uzbl


    def clean_slate(self):
        '''Close all open tabs and open a fresh brand new one.'''

        self.new_tab()
        tabs = self.tabs.keys()
        for tab in list(self.notebook)[:-1]:
            if tab not in tabs: continue
            uzbl = self.tabs[tab]
            uzbl.exit()

    def config_uzbl(self, uzbl):
        '''Send bind commands for tab new/close/next/prev to a uzbl
        instance.'''

        if self.force_socket_dir:
            uzbl.set("socket_dir", self.socket_dir)

        if self.force_fifo_dir:
            uzbl.set("fifo_dir",   self.fifo_dir)

    def goto_tab(self, index):
        '''Goto tab n (supports negative indexing).'''

        title_format = "%s - Uzbl Browser"

        tabs = list(self.notebook)
        if 0 <= index < len(tabs):
            self.notebook.set_current_page(index)
            uzbl = self.tabs[self.notebook.get_nth_page(index)]
            self.window.set_title(title_format % uzbl.title)
            self.update_tablist()
            return None

        try:
            tab = tabs[index]
            # Update index because index might have previously been a
            # negative index.
            index = tabs.index(tab)
            self.notebook.set_current_page(index)
            uzbl = self.tabs[self.notebook.get_nth_page(index)]
            self.window.set_title(title_format % uzbl.title)
            self.update_tablist()

        except IndexError:
            pass


    def next_tab(self, step=1):
        '''Switch to next tab or n tabs right.'''

        if step < 1:
            error("next_tab: invalid step %r" % step)
            return None

        ntabs = self.notebook.get_n_pages()
        tabn = (self.notebook.get_current_page() + step) % ntabs
        self.goto_tab(tabn)


    def prev_tab(self, step=1):
        '''Switch to prev tab or n tabs left.'''

        if step < 1:
            error("prev_tab: invalid step %r" % step)
            return None

        ntabs = self.notebook.get_n_pages()
        tabn = self.notebook.get_current_page() - step
        while tabn < 0: tabn += ntabs
        self.goto_tab(tabn)


    def close_tab(self, tabn=None):
        '''Closes current tab. Supports negative indexing.'''

        if tabn is None:
            tabn = self.notebook.get_current_page()

        else:
            try:
                tab = list(self.notebook)[tabn]

            except IndexError:
                error("close_tab: invalid index %r" % tabn)
                return None

        self.notebook.remove_page(tabn)


    def tab_opened(self, notebook, tab, index):
        '''Called upon tab creation. Called by page-added signal.'''

        if config['switch_to_new_tabs']:
            self.notebook.set_focus_child(tab)

        else:
            oldindex = self.notebook.get_current_page()
            oldtab = self.notebook.get_nth_page(oldindex)
            self.notebook.set_focus_child(oldtab)


    def tab_closed(self, notebook, tab, index):
        '''Close the window if no tabs are left. Called by page-removed
        signal.'''

        if tab in self.tabs.keys():
            uzbl = self.tabs[tab]
            uzbl.close()

            self._closed.append((uzbl.uri, uzbl.title))
            self._closed = self._closed[-10:]
            del self.tabs[tab]

        if self.notebook.get_n_pages() == 0:
            if not self._killed and config['save_session']:
                if os.path.exists(config['session_file']):
                    os.remove(config['session_file'])

            self.quit()

        for tab in self.notebook:
            self.tabs[tab].title_changed(True)
        self.update_tablist()

        return True


    def tab_changed(self, notebook, page, index):
        '''Refresh tab list. Called by switch-page signal.'''

        tab = self.notebook.get_nth_page(index)
        self.notebook.set_focus_child(tab)
        self.update_tablist(index)
        return True


    def tab_reordered(self, notebook, page, index):
        '''Refresh tab titles. Called by page-reordered signal.'''

        for tab in self.notebook:
            self.tabs[tab].title_changed(True)
        return True


    def update_tablist_display(self):
        '''Called when show_tablist or tablist_top has changed'''

        if self.ebox in self.vbox.get_children():
            self.vbox.remove(self.ebox)

        if config['show_tablist']:
            self.vbox.pack_start(self.ebox, False, False, 0)
            if config['tablist_top']:
                self.vbox.reorder_child(self.ebox, 0)
            else:
                self.vbox.reorder_child(self.ebox, 2)

    def update_gtk_tab_pos(self):
        ''' Called when gtk_tab_pos has changed '''

        allposes = {'left': gtk.POS_LEFT, 'right':gtk.POS_RIGHT,
          'top':gtk.POS_TOP, 'bottom':gtk.POS_BOTTOM}
        if config['gtk_tab_pos'] in allposes.keys():
            self.notebook.set_tab_pos(allposes[config['gtk_tab_pos']])


    def update_tablist(self, curpage=None):
        '''Upate tablist status bar.'''

        if not config['show_tablist']:
            return True

        tab_titles = config['tab_titles']
        tab_indexes = config['tab_indexes']
        multiline_tabs = config['multiline_tabs']

        if multiline_tabs:
            multiline = []

        tabs = self.tabs.keys()
        if curpage is None:
            curpage = self.notebook.get_current_page()

        pango = ""
        normal = (config['tab_colours'], config['tab_text_colours'])
        selected = (config['selected_tab'], config['selected_tab_text'])

        if tab_titles and tab_indexes:
            tab_format = "<span %(tabc)s> [ %(index)d <span %(textc)s> %(title)s</span> ] </span>"
        elif tab_titles:
            tab_format = "<span %(tabc)s> [ <span %(textc)s>%(title)s</span> ] </span>"
        else:
            tab_format = "<span %(tabc)s> [ <span %(textc)s>%(index)d</span> ] </span>"

        for index, tab in enumerate(self.notebook):
            if tab not in tabs: continue
            uzbl = self.tabs[tab]
            title = escape(uzbl.tabtitle)

            style = colour_selector(index, curpage, uzbl)
            (tabc, textc) = style

            if multiline_tabs:
                opango = pango

                pango += tab_format % locals()

                self.tablist.set_markup(pango)
                listwidth = self.tablist.get_layout().get_pixel_size()[0]
                winwidth = self.window.get_size()[0]

                if listwidth > (winwidth - 20):
                    multiline.append(opango)
                    pango = tab_format % locals()
            else:
                pango += tab_format % locals()

        if multiline_tabs:
            multiline.append(pango)
            self.tablist.set_markup('&#10;'.join(multiline))

        else:
            self.tablist.set_markup(pango)

        return True


    def save_session(self, session_file=None):
        '''Save the current session to file for restoration on next load.'''

        if session_file is None:
            session_file = config['session_file']

        tabs = self.tabs.keys()
        lines = "curtab = %d\n" % self.notebook.get_current_page()
        for tab in list(self.notebook):
            if tab not in tabs:
                continue

            uzbl = self.tabs[tab]
            if not uzbl.uri:
                continue

            lines += "%s %s\n" % (uzbl.uri, uzbl.title)

        if not os.path.isfile(session_file):
            dirname = os.path.dirname(session_file)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)

        fh = open(session_file, 'w')
        fh.write(lines)
        fh.close()


    def load_session(self, session_file=None):
        '''Load a saved session from file.'''

        default_path = False
        delete_loaded = False

        if session_file is None:
            default_path = True
            delete_loaded = True
            session_file = config['session_file']

        if not os.path.isfile(session_file):
            return False

        fh = open(session_file, 'r')
        raw = fh.read()
        fh.close()

        tabs = []
        curtab = 0

        lines = filter(None, map(str.strip, raw.split('\n')))
        if len(lines) < 2:
            error("Error: The session file %r looks invalid." % session_file)
            if delete_loaded and os.path.exists(session_file):
                os.remove(session_file)

            return None

        try:
            for line in lines:
                if line.startswith("curtab"):
                    curtab = int(line.split()[-1])

                else:
                    uri, title = map(str.strip, line.split(" ", 1))
                    tabs += [(uri, title),]

        except:
            print_exc()
            error("Warning: failed to load session file %r" % session_file)
            return None

        # Now populate notebook with the loaded session.
        for (index, (uri, title)) in enumerate(tabs):
            self.new_tab(uri=uri, title=title, switch=(curtab==index))

        # A saved session has been loaded now delete it.
        if delete_loaded and os.path.exists(session_file):
            os.remove(session_file)


    def quitrequest(self, *args):
        '''Attempt to close all uzbl instances nicely and exit.'''

        self._killed = True

        if config['save_session']:
            if len(list(self.notebook)) > 1:
                self.save_session()

            else:
                # Notebook has one page open so delete the session file.
                if os.path.isfile(config['session_file']):
                    os.remove(config['session_file'])

        for (tab, uzbl) in self.tabs.items():
            uzbl.exit()

        # Add a gobject timer to make sure the application force-quits after a
        # reasonable period. Calling quit when all the tabs haven't had time to
        # close should be a last resort.
        timer = "force-quit"
        timerid = timeout_add(5000, self.quit, timer)
        self._timers[timer] = timerid


    def quit(self, *args):
        '''Cleanup and quit. Called by delete-event signal.'''

        # Close the socket, remove any gobject io event handlers and
        # delete socket.
        self.close_socket()

        # Remove all gobject timers that are still ticking.
        for (timerid, gid) in self._timers.items():
            source_remove(gid)
            del self._timers[timerid]

        try:
            gtk.main_quit()

        except:
            pass


if __name__ == "__main__":

    # Build command line parser
    usage = "usage: %prog [OPTIONS] {URIS}..."
    parser = OptionParser(usage=usage)
    parser.add_option('-n', '--no-session', dest='nosession',
      action='store_true', help="ignore session saving a loading.")
    parser.add_option('-v', '--verbose', dest='verbose',
      action='store_true', help='print verbose output.')
    parser.add_option('-s', '--socketdir', dest='socketdir',
      help="directory to create socket")
    parser.add_option('-f', '--fifodir', dest='fifodir',
      help="directory to create fifo")

    # Parse command line options
    (options, uris) = parser.parse_args()

    if options.nosession:
        config['save_session'] = False

    if options.verbose:
        config['verbose'] = True

    if config['verbose']:
        import pprint
        sys.stderr.write("%s\n" % pprint.pformat(config))

    uzbl = UzblTabbed()

    if options.socketdir:
        uzbl.socket_dir = options.socketdir
        uzbl.force_socket_dir = True

    if options.fifodir:
        uzbl.fifo_dir = options.fifodir
        uzbl.force_fifo_dir = True

    # All extra arguments given to uzbl_tabbed.py are interpreted as
    # web-locations to opened in new tabs.
    lasturi = len(uris)-1
    for (index,uri) in enumerate(uris):
        uzbl.new_tab(uri, switch=(index==lasturi))

    uzbl.run()