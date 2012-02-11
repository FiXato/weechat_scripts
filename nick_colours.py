# -*- coding: utf-8 -*-
#
# Nick Colours, version 0.1 for WeeChat version 0.3
# Latest development version: https://github.com/FiXato/weechat_scripts
#
#   Tools to help set up the colours you want to use for
#   colouring the nicknames in your nicklist and/or with 
#   colorize_nicks/lines.
#
## History:
### 2012-02-10: FiXato:
# 
# * version 0.1: initial release.
#     * 
#
## Acknowledgements:
# * Sébastien "Flashcode" Helleu, for developing the kick-ass chat/IRC
#    client WeeChat
# * Nils "nils_2" Görs, for his quick_force_color.py script that partially
#    inspired me to work on this script.
#
## TODO: 
#   - Show all currently used nick colours in a custom buffer.
#
## Copyright (c) 2011 Filip H.F. "FiXato" Slagter,
#   <FiXato [at] Gmail [dot] com>
#   http://google.com/profiles/FiXato
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
SCRIPT_NAME    = "nick_colours"
SCRIPT_AUTHOR  = "Filip H.F. 'FiXato' Slagter <fixato [at] gmail [dot] com>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC    = "Manage weechat.color.chat_nick_colors in a more user-friendly way."
SCRIPT_COMMAND = "nick_colours"
SCRIPT_BUFFERNAME = "nick_colours"

import_ok = True

try:
  import weechat
except ImportError:
  print "This script must be run under WeeChat."
  import_ok = False

import re

config_settings = (
  ("autofocus", "on", "Focus the nick_colours buffer in the current window if it isn't already displayed by a window."),
)
script_buff = None
buff_items = []
curline = 0

def buffer_items():
  global buff_items
  return buff_items

def script_buffer():
  global script_buff
  return script_buff

# Create nick colours buffer.
def create_script_buffer():
  global curline, script_buff

  if not script_buffer():
    script_buff = weechat.buffer_new(SCRIPT_BUFFERNAME, "buffer_input_cb", \
                "", "buffer_close_cb", "")
    weechat.buffer_set(script_buffer(), "title", "Colours used for nicks")
    # Sets notify to 0 as this buffer does not need to be in hotlist.
    weechat.buffer_set(script_buffer(), "notify", "0")
    weechat.buffer_set(script_buffer(), "nicklist", "0")
    weechat.buffer_set(script_buffer(), "type", "free")
    weechat.buffer_set(script_buffer(), "key_bind_ctrl-L", "/%s **refresh" % SCRIPT_COMMAND)
    weechat.buffer_set(script_buffer(), "key_bind_meta2-A", "/%s **up" % SCRIPT_COMMAND)
    weechat.buffer_set(script_buffer(), "key_bind_meta2-B", "/%s **down" % SCRIPT_COMMAND)
    weechat.buffer_set(script_buffer(), "key_bind_meta2-1~", "/%s **scroll_top" % SCRIPT_COMMAND)
    weechat.buffer_set(script_buffer(), "key_bind_meta2-4~", "/%s **scroll_bottom" % SCRIPT_COMMAND)
    weechat.buffer_set(script_buffer(), "key_bind_meta-ctrl-J", "/%s **enter" % SCRIPT_COMMAND)
    weechat.buffer_set(script_buffer(), "key_bind_meta-ctrl-M", "/%s **enter" % SCRIPT_COMMAND)
    curline = 0
  if weechat.config_get_plugin("autofocus") == "on":
    if not weechat.window_search_with_buffer(script_buffer()):
      weechat.command("", "/buffer " + weechat.buffer_get_string(script_buffer(),"name"))

def script_initialise_list():
  global buff_items
  nick_colours = weechat.config_string(weechat.config_get('weechat.color.chat_nick_colors'))
  buff_items = [x.strip() for x in nick_colours.split(',')]
  return

def keyEvent (data, buffer, args):
  global buffer_options
  buffer_options[args]()
  
def buffer_input_cb(data, buffer, input_data):
  global buffer_options, curline
  buffer_options[input_data]()
  return weechat.WEECHAT_RC_OK

def buffer_refresh():
  weechat.buffer_clear(script_buffer())

  y = 0
  for list_data in buffer_items():
    buffer_refresh_line(y)
    y += 1
  return

def buffer_refresh_line(y):
  global curline
  if y >= 0 and y < len(buffer_items()):
    formatted_line = buffer_line_format(buffer_items()[y], y == curline)
    weechat.prnt_y(script_buffer(), y, formatted_line)

def buffer_refresh_curline():
  global curline
  buffer_refresh_line(curline-1)
  buffer_refresh_line(curline)
  buffer_refresh_line(curline+1)
  return

def buffer_line_format(buffer_item,curr=False):
  str = ""
  if (curr):
    str += weechat.color("white,darkgray")
  str += "%s%s" % (weechat.color(buffer_item), buffer_item)
  return str

def buffer_line_up():
  global curline
  if curline <= 0:
    return
  curline -= 1
  buffer_refresh_curline()
  buffer_check_outside_window()
  return

def buffer_line_down():
  global curline
  if curline+1 >= len(buffer_items()):
    return
  curline += 1
  buffer_refresh_curline()
  buffer_check_outside_window()
  return

def buffer_line_run():
  global curline
  selected_item = buffer_items()[curline]

  command = ""
  buffer = ""
  weechat.command(buffer, command)
  return

def buffer_line_select():
  return

def buffer_scroll_top():
  global curline
  old_y = curline
  curline = 0
  buffer_refresh_curline()  
  buffer_refresh_line(old_y)
  weechat.command(script_buffer(), "/window scroll_top")
  return

def buffer_scroll_bottom():
  global curline
  old_y = curline
  curline = len(buffer_items())-1
  buffer_refresh_curline()
  buffer_refresh_line(old_y)
  weechat.command(script_buffer(), "/window scroll_bottom")
  return

def buffer_check_outside_window():
  global curline
  if (script_buffer()):
    infolist = weechat.infolist_get("window", "", "current")
    if (weechat.infolist_next(infolist)):
      start_line_y = weechat.infolist_integer(infolist, "start_line_y")
      chat_height = weechat.infolist_integer(infolist, "chat_height")
      if(start_line_y > curline):
        weechat.command(script_buffer(), "/window scroll -%i" %(start_line_y - curline))
      elif(start_line_y <= curline - chat_height):
        weechat.command(script_buffer(), "/window scroll +%i"%(curline - start_line_y - chat_height + 1))
    weechat.infolist_free(infolist)

def buffer_close_cb(*kwargs):
  """ A callback for buffer closing. """
  global script_buff

  script_buff = None
  return weechat.WEECHAT_RC_OK

buffer_options = {
  'refresh'      : buffer_refresh,
  'up'           : buffer_line_up,
  'down'         : buffer_line_down,
  'enter'        : buffer_line_run,
  'space'        : buffer_line_select,
  'scroll_top'   : buffer_scroll_top,
  'scroll_bottom': buffer_scroll_bottom,
}

def buffer_command_main(data, buffer, args):
  if args[0:2] == "**":
    keyEvent(data, buffer, args[2:])
  elif args == "":
    script_initialise_list()
    create_script_buffer()
    buffer_refresh()
  return weechat.WEECHAT_RC_OK

def set_default_settings():
  global config_settings, script_buff
  # Set default settings
  for option, default_value, description in config_settings:
     if not weechat.config_is_set_plugin(option):
         weechat.config_set_plugin(option, default_value)
         version = weechat.info_get("version_number", "") or 0
         if int(version) >= 0x00030500:
             weechat.config_set_desc_plugin(option, description)

if __name__ == "__main__" and import_ok:
  if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION,
                      SCRIPT_LICENSE, SCRIPT_DESC, "buffer_close_cb", ""):
    set_default_settings()
    script_buff = weechat.buffer_search("python", SCRIPT_BUFFERNAME)
    weechat.hook_command(SCRIPT_COMMAND, 
                          "Nick Colours",
                          "", "", "", 
                          "buffer_command_main", "")
