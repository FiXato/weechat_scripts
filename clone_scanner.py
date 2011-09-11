# -*- coding: utf-8 -*-
#
# Clone Scanner, version 0.2 for WeeChat version 0.3
# Latest development version: https://github.com/FiXato/weechat_scripts
#
#   Detect if a joining user is a clone or not.
#
#   Upon join by a user, the user's host is compared to the infolist of 
#   already connected users to see if they are already online from
#   another nickname. If the user is a clone, it will report it.
#
## History:
### 2011-09-11: FiXato:
# 
# * version 0.1:  initial release.
#     * Added an on-join clone scan. Any user that joins a channel will be
#       matched against users already on the channel.
# * version 0.2:  manual clone scan
#     * Added a manual clone scan via /clone_scanner scan
#        you can specify a target channel with:
#         /clone_scanner scan #myChannelOnCurrentServer
#        or:
#         /clone_scanner scan Freenode.#myChanOnSpecifiedNetwork
#
## Acknowledgements:
# * Sebastien "Flashcode" Helleu, for developing the kick-ass chat/IRC
#    client WeeChat
# * ArZa, whose kickban.pl script helped me get started with using the
#   infolist results. 
#
## TODO: 
#   - Add option to enable/disable clone reporting (local and public)
#   - Add option to enable/disable scanning on certain channels/networks
#   - Make clones report format configurable
#   - Make JOIN reporting optional
#   - Add command completion and help
#   - Add cross-channel clone scan
#   - Add cross-server clone scan
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
SCRIPT_NAME     = "clone_scanner"
SCRIPT_AUTHOR   = "Filip H.F. 'FiXato' Slagter <fixato [at] gmail [dot] com>"
SCRIPT_VERSION  = "0.1"
SCRIPT_LICENSE  = "MIT"
SCRIPT_DESC     = "A Clone Scanner that detects if joining users are already on the channel with a different nickname from the same host."
SCRIPT_COMMAND  = "clone_scanner"
SCRIPT_CLOSE_CB = "cs_close_cb"

import_ok = True

try:
  import weechat
except ImportError:
  print "This script must be run under WeeChat."
  import_ok = False

import re
cs_buffer = None

def on_join_scan_cb(data, signal, signal_data):
  global cs_buffer
  network = signal.split(',')[0]
  joined_nick = weechat.info_get("irc_nick_from_host", signal_data)
  join_match_data = re.match(':([^!]+)!([^@]+)@(\S+) JOIN :?(#\S+)', signal_data)
  parsed_nick = join_match_data.group(1)
  parsed_ident = join_match_data.group(2)
  parsed_host = join_match_data.group(3)
  chan_name = join_match_data.group(4)
  chan_buffer = weechat.buffer_search("irc", "%s.%s" % (network, chan_name))
  weechat.prnt(cs_buffer, "%s!%s JOINed %s.%s" % (joined_nick, parsed_host, network, chan_name))

  infolist = weechat.infolist_get("irc_nick", "", "%s,%s" % (network, chan_name))
  matches = []
  while(weechat.infolist_next(infolist)):
    ident_hostname = weechat.infolist_string(infolist, "host")
    host_matchdata = re.match('([^@]+)@(\S+)', ident_hostname)
    if host_matchdata:
      nick = weechat.infolist_string(infolist, "name")
      ident = host_matchdata.group(1)
      hostname = host_matchdata.group(2)
      if(hostname == parsed_host):
        matches.append({
          'nick': nick, 
          'ident': ident, 
          'hostname': hostname,
          'ident_hostname': ident_hostname, 
          'mask': "%s!%s" % (nick, ident_hostname)
        })
  if len(matches) > 0:
    #TODO: make match string configurable (nick, ident, hostname, ident_hostname, mask)
    match_strings = map(lambda m: m['mask'], matches)
    weechat.prnt(cs_buffer,"%s%s is already on %s.%s as %s" % (weechat.color("red"), joined_nick, network, chan_name, ' and '.join(match_strings)))
    weechat.prnt(chan_buffer,"%s%s is already on channel as %s" % (weechat.color("red"), joined_nick, ' and '.join(match_strings)))
  return weechat.WEECHAT_RC_OK
  
# Create debug buffer.
def cs_create_buffer():
  global cs_buffer

  if not cs_buffer:
    # Sets notify to 0 as this buffer does not need to be in hotlist.
    cs_buffer = weechat.buffer_new("clone_scanner", "", \
                "", "SCRIPT_CLOSE_CB", "")
    weechat.buffer_set(cs_buffer, "title", "Clone Scanner")
    weechat.buffer_set(cs_buffer, "notify", "0")
    weechat.buffer_set(cs_buffer, "nicklist", "0")

def cs_close_cb(*kwargs):
  """ A callback for buffer closing. """
  global cs_buffer

  cs_buffer = None
  return weechat.WEECHAT_RC_OK


def cs_command_main(data, buffer, args):
  global cs_buffer

  if args[0:4] == 'scan':
    server_name = weechat.buffer_get_string(buffer, "localvar_server")
    channel_name = args[5:]
    if not channel_name:
      channel_name = weechat.buffer_get_string(buffer, "localvar_channel")

    match_data = re.match('\A([^.]+)\.(#\S+)\Z', channel_name)
    if match_data:
      channel_name = match_data.group(2)
      server_name = match_data.group(1)

    infolist_buffer_name = '%s,%s' % (server_name, channel_name)
    target_buffer_name = '%s.%s' % (server_name, channel_name)

    infolist = weechat.infolist_get("irc_nick", "", infolist_buffer_name)
    matches = {}
    clone_found = False
    while(weechat.infolist_next(infolist)):
      ident_hostname = weechat.infolist_string(infolist, "host")
      host_matchdata = re.match('([^@]+)@(\S+)', ident_hostname)
      if host_matchdata:
        nick = weechat.infolist_string(infolist, "name")
        ident = host_matchdata.group(1)
        hostname = host_matchdata.group(2)
        user = {
          'nick': nick,
          'ident': ident,
          'hostname': hostname,
          'ident_hostname': ident_hostname,
          'mask': "%s!%s" % (nick, ident_hostname)
        }
        if hostname not in matches:
          matches[hostname] = []
        else:
          clone_found = True
        matches[hostname].append(user)
    if clone_found:
      weechat.prnt(cs_buffer, "The following clones were found:")
      hosts_with_multiple_matches = filter(lambda i: len(matches[i]) > 1, matches)
      for host in hosts_with_multiple_matches:
        weechat.prnt(cs_buffer, "%s is online from %s connections:" % (matches[host][0]['nick'], len(matches[host])))
        for user in matches[host]:
          weechat.prnt(cs_buffer, " - %s" % user['mask'])
    else:
      weechat.prnt(cs_buffer, "No clones found on %s" % target_buffer_name)
  return weechat.WEECHAT_RC_OK

if __name__ == "__main__" and import_ok:
  if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION,
                      SCRIPT_LICENSE, SCRIPT_DESC, SCRIPT_CLOSE_CB, ""):
    #        # Set default settings
    #        for option, default_value in cs_settings.iteritems():
    #            if not weechat.config_is_set_plugin(option):
    #                weechat.config_set_plugin(option, default_value)

    cs_buffer = weechat.buffer_search("python", "clone_scanner")
    cs_create_buffer()

    weechat.hook_signal("*,irc_in_join", "on_join_scan_cb", "")

    weechat.hook_command(SCRIPT_COMMAND, 
                          "Clone Scanner",
                          "", "", "", 
                          "cs_command_main", "")

