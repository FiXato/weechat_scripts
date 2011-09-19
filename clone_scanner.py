# -*- coding: utf-8 -*-
#
# Clone Scanner, version 0.4 for WeeChat version 0.3
# Latest development version: https://github.com/FiXato/weechat_scripts
#
#   A Clone Scanner that can manually scan channels and 
#   automatically scans joins for users on the channel 
#   with multiple nicknames from the same host.
#
#   Upon join by a user, the user's host is compared to the infolist of 
#   already connected users to see if they are already online from
#   another nickname. If the user is a clone, it will report it.
#   With the '/clone_scanner scan' command you can manually scan a chan.
#
#   See /set plugins.var.python.clone_scanner.* for all possible options
#   Use the brilliant iset.pl plugin (/weeget install iset) to see what they do
#   Or check the sourcecode below.
#
# Example output for an on-join scan result:
#   21:32:46  ▬▬▶ FiXato_Odie (FiXato@FiXato.net) has joined #lounge
#   21:32:46      FiXato_Odie is already on the channel as FiXato!FiXato@FiXato.Net and FiX!FiXaphone@FiXato.net
#
# Example output for a manual scan:
#   21:34:44 fixato.net is online from 3 nicks:
#   21:34:44  - FiXato!FiXato@FiXato.Net
#   21:34:44  - FiX!FiXaphone@FiXato.net
#   21:34:44  - FiXato_Odie!FiXato@FiXato.net
#
## History:
### 2011-09-11: FiXato:
# 
# * version 0.1: initial release.
#     * Added an on-join clone scan. Any user that joins a channel will be
#       matched against users already on the channel.
#
# * version 0.2: manual clone scan
#     * Added a manual clone scan via /clone_scanner scan
#        you can specify a target channel with:
#         /clone_scanner scan #myChannelOnCurrentServer
#        or:
#         /clone_scanner scan Freenode.#myChanOnSpecifiedNetwork
#     * Added completion
#
### 2011-09-12: FiXato:
#
# * version 0.3: Refactor galore
#     * Refactored some code. Codebase should be DRYer and clearer now.
#     * Manual scan report lists by host instead of nick now.
#     * Case-insensitive host-matching
#     * Bugfixed the infolist memleak.
#     * on-join scanner works again
#     * Output examples added to the comments
#
### 2011-09-19
# * version 0.4: Option galore
#     * Case-insensitive buffer lookup fix.
#     * Added some bold formatting to the nicks in the responses.
#     * Made most messages optional through settings.
#     * Made on-join alert and clone report key a bit more configurable.
#     * Added formatting options for on-join alerts.
#     * Added format_message helper method that accepts multiple whitespace-separated weechat.color() options.
#     * Added formatting options for join messages
#
## Acknowledgements:
# * Sebastien "Flashcode" Helleu, for developing the kick-ass chat/IRC
#    client WeeChat
# * ArZa, whose kickban.pl script helped me get started with using the
#   infolist results. 
#
## TODO: 
#   - Add option to enable/disable public clone reporting aka msg channels
#   - Add option to enable/disable scanning on certain channels/networks
#   - Add more formatting configuration options for the clones report
#   - Add cross-channel clone scan
#   - Add cross-server clone scan
#   - Make clone_scanner buffer optional
#   - Add optional command redirection.
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
SCRIPT_VERSION  = "0.4"
SCRIPT_LICENSE  = "MIT"
SCRIPT_DESC     = "A Clone Scanner that can manually scan channels and automatically scans joins for users on the channel with multiple nicknames from the same host."
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
cs_settings = (
  ("display_join_messages",               "off", "Display all joins in the clone_scanner buffer"),
  ("display_onjoin_alert_clone_buffer",   "on", "Display an on-join clone alert in the clone_scanner buffer"),
  ("display_onjoin_alert_target_buffer",  "on", "Display an on-join clone alert in the buffer where the clone was detected"),
  ("display_onjoin_alert_current_buffer", "off", "Display an on-join clone alert in the current buffer"),
  ("display_scan_report_clone_buffer",    "on", "Display manual scan reports in the clone buffer"),
  ("display_scan_report_target_buffer",   "off", "Display manual scan reports in the buffer of the scanned channel"),
  ("display_scan_report_current_buffer",  "on", "Display manual scan reports in the current buffer"),
  ("clone_report_key",                    "mask", "Which 'key' to display in the clone report: 'mask' for full hostmasks, or 'nick' for nicks"),
  ("clone_onjoin_alert_key",              "mask", "Which 'key' to display in the on-join alerts: 'mask' for full hostmasks, or 'nick' for nicks"),
  ("onjoin_alert_message_color",          "red", "The on-join clone alert's message colour. Formats are space separated."),
  ("onjoin_alert_nick_color",             "bold red", "The on-join clone alert's nick colour. Formats are space separated. Note: if you have colorize_nicks, this option might not work as expected."),
  ("onjoin_alert_channel_color",          "red", "The on-join clone alert's channel colour. Formats are space separated."),
  ("onjoin_alert_matches_color",          "bold red", "The on-join clone alert's matches (masks or nicks) colour. Formats are space separated. Note: if you have colorize_nicks, this option might not work as expected."),
  ("join_messages_message_color",         "chat", "The base colour for the join messages."),
  ("join_messages_nick_color",            "bold", "The colour for the 'nick'-part of the join messages. Note: if you have colorize_nicks, this option might not always work as expected."),
  ("join_messages_identhost_color",       "chat", "The colour for the 'ident@host'-part of the join messages."),
  ("join_messages_channel_color",         "bold", "The colour for the 'ident@host'-part of the join messages."),
)

def get_validated_key_from_config(setting):
  key = weechat.config_get_plugin(setting)
  if key != 'mask' and key != 'nick':
    weechat.prnt("", "Key %s not found. Valid settings are 'nick' and 'mask'. Reverted the setting to 'mask'" % key)
    weechat.config_set_plugin("clone_report_key", "mask")
    key = "mask"
  return key

def format_message(msg, formats, reset_color='chat'):
  if type(formats) == str:
    formats = formats.split()
  formatted_message = msg
  needs_color_reset = False
  for format in formats:
    if format in ['bold', 'reverse', 'italic', 'underline']:
      end_format = '-%s' % format
    else:
      needs_color_reset = True
      end_format = ""
    formatted_message = "%s%s%s" % (weechat.color(format), formatted_message, weechat.color(end_format))
  if needs_color_reset:
    formatted_message += weechat.color(reset_color)
  return formatted_message

def on_join_scan_cb(data, signal, signal_data):
  global cs_buffer
  network = signal.split(',')[0]
  joined_nick = weechat.info_get("irc_nick_from_host", signal_data)
  join_match_data = re.match(':[^!]+!([^@]+@(\S+)) JOIN :?(#\S+)', signal_data)
  parsed_ident_host = join_match_data.group(1)
  parsed_host = join_match_data.group(2).lower()
  chan_name = join_match_data.group(3)
  network_chan_name = "%s.%s" % (network, chan_name)
  chan_buffer = weechat.info_get("irc_buffer", "%s,%s" % (network, chan_name))
  if not chan_buffer:
    print "No IRC channel buffer found for %s" % network_chan_name
    return weechat.WEECHAT_RC_OK

  if weechat.config_get_plugin("display_join_messages") == "on":
    cs_create_buffer()
    message = "%s%s%s%s%s" % (
      format_message(joined_nick, weechat.config_get_plugin("join_messages_nick_color")),
      format_message("!", weechat.config_get_plugin("join_messages_message_color")),
      format_message(parsed_ident_host, weechat.config_get_plugin("join_messages_identhost_color")),
      format_message(" JOINed ", weechat.config_get_plugin("join_messages_message_color"))
      format_message(network_chan_name, weechat.config_get_plugin("join_messages_channel_color")),
    )
    weechat.prnt(cs_buffer, message)

  clones = get_clones_for_buffer("%s,%s" % (network, chan_name), parsed_host)
  if clones:
    key = get_validated_key_from_config("clone_onjoin_alert_key")

    filtered_clones = filter(lambda clone: clone['nick'] != joined_nick, clones[parsed_host])
    match_strings = map(lambda m: format_message(m[key], weechat.config_get_plugin("onjoin_alert_matches_color")), filtered_clones)

    join_string = format_message(' and ',weechat.config_get_plugin("onjoin_alert_message_color"))
    masks = join_string.join(match_strings)
    message = "%s %s %s %s %s" % (
      format_message(joined_nick, weechat.config_get_plugin("onjoin_alert_nick_color")),
      format_message("is already on", weechat.config_get_plugin("onjoin_alert_message_color")),
      format_message(network_chan_name, weechat.config_get_plugin("onjoin_alert_channel_color")),
      format_message("as", weechat.config_get_plugin("onjoin_alert_message_color")),
      masks)

    if weechat.config_get_plugin("display_onjoin_alert_clone_buffer") == "on":
      cs_create_buffer()
      weechat.prnt(cs_buffer,message)
    if weechat.config_get_plugin("display_onjoin_alert_target_buffer") == "on":
      weechat.prnt(chan_buffer, message)
    if weechat.config_get_plugin("display_onjoin_alert_current_buffer") == "on":
      weechat.prnt(weechat.current_buffer(),message)
  return weechat.WEECHAT_RC_OK

# Create debug buffer.
def cs_create_buffer():
  global cs_buffer

  if not cs_buffer:
    # Sets notify to 0 as this buffer does not need to be in hotlist.
    cs_buffer = weechat.buffer_new("clone_scanner", "", \
                "", SCRIPT_CLOSE_CB, "")
    weechat.buffer_set(cs_buffer, "title", "Clone Scanner")
    weechat.buffer_set(cs_buffer, "notify", "0")
    weechat.buffer_set(cs_buffer, "nicklist", "0")

def cs_close_cb(*kwargs):
  """ A callback for buffer closing. """
  global cs_buffer

  cs_buffer = None
  return weechat.WEECHAT_RC_OK


def get_channel_from_buffer_args(buffer, args):
  server_name = weechat.buffer_get_string(buffer, "localvar_server")
  channel_name = args
  if not channel_name:
    channel_name = weechat.buffer_get_string(buffer, "localvar_channel")

  match_data = re.match('\A(irc.)?([^.]+)\.(#\S+)\Z', channel_name)
  if match_data:
    channel_name = match_data.group(3)
    server_name = match_data.group(2)
  
  return server_name, channel_name

def get_clones_for_buffer(infolist_buffer_name, hostname_to_match=None):
  global cs_buffer
  matches = {}
  infolist = weechat.infolist_get("irc_nick", "", infolist_buffer_name)
  while(weechat.infolist_next(infolist)):
    ident_hostname = weechat.infolist_string(infolist, "host")
    host_matchdata = re.match('([^@]+)@(\S+)', ident_hostname)
    if not host_matchdata:
      continue

    hostname = host_matchdata.group(2).lower()

    if hostname_to_match and hostname_to_match.lower() != hostname:
      continue

    if hostname not in matches:
      matches[hostname] = []

    nick = weechat.infolist_string(infolist, "name")
    matches[hostname].append({
      'nick': nick,
      'mask': "%s!%s" % (format_message(nick, 'bold'), ident_hostname),
      'ident': host_matchdata.group(1),
      'ident_hostname': ident_hostname,
      'hostname': hostname,
    })
  weechat.infolist_free(infolist)

  #Select only the results that have more than 1 match for a host
  return dict((k, v) for (k, v) in matches.iteritems() if len(v) > 1)

def report_clones(clones, scanned_buffer_name, target_buffer=None):
  # Default to clone_scanner buffer
  if not target_buffer:
    cs_create_buffer()
    global cs_buffer
    target_buffer = cs_buffer

  if clones:
    weechat.prnt(target_buffer, "%s hosts with clones were found on %s:" % (len(clones), scanned_buffer_name))
    for (host, clones) in clones.iteritems():
      weechat.prnt(target_buffer, "%s is online from %s nicks:" % (host, len(clones)))
      for user in clones:
        key = get_validated_key_from_config("clone_report_key")
        weechat.prnt(target_buffer, " - %s" % user[key])
  else:
    weechat.prnt(target_buffer, "No clones found on %s" % scanned_buffer_name)

def cs_command_main(data, buffer, args):
  if args[0:4] == 'scan':    
    server_name, channel_name = get_channel_from_buffer_args(buffer, args[5:])
    clones = get_clones_for_buffer('%s,%s' % (server_name, channel_name))
    if weechat.config_get_plugin("display_scan_report_target_buffer") == "on":
      target_buffer = weechat.info_get("irc_buffer", "%s,%s" % (server_name, channel_name))
      report_clones(clones, '%s.%s' % (server_name, channel_name), target_buffer)
    if weechat.config_get_plugin("display_scan_report_clone_buffer") == "on":
      report_clones(clones, '%s.%s' % (server_name, channel_name))
    if weechat.config_get_plugin("display_scan_report_current_buffer") == "on":
      report_clones(clones, '%s.%s' % (server_name, channel_name), weechat.current_buffer())
  return weechat.WEECHAT_RC_OK

def cs_set_default_settings():
  global cs_settings

  # Set default settings
  for option, default_value, description in cs_settings:
     if not weechat.config_is_set_plugin(option):
         weechat.config_set_plugin(option, default_value)
         version = weechat.info_get("version_number", "") or 0
         if int(version) >= 0x00030500:
             weechat.config_set_desc_plugin(option, description)

if __name__ == "__main__" and import_ok:
  if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION,
                      SCRIPT_LICENSE, SCRIPT_DESC, SCRIPT_CLOSE_CB, ""):
    cs_set_default_settings()

    cs_buffer = weechat.buffer_search("python", "clone_scanner")
    cs_create_buffer()

    weechat.hook_signal("*,irc_in2_join", "on_join_scan_cb", "")

    weechat.hook_command(SCRIPT_COMMAND, 
                          SCRIPT_DESC,
                          "[scan] [[plugin.][network.]channel] | [help]",
                          "the target_buffer can be: \n"
                          "- left out, so the current channel buffer will be scanned.\n"
                          "- a plain channel name, such as #weechat, in which case it will prefixed with the current network name\n"
                          "- a channel name prefixed with network name, such as Freenode.#weechat\n"
                          "- a channel name prefixed with plugin and network name, such as irc.freenode.#weechat\n"
                          "See /set plugins.var.python.clone_scanner.* for all possible configuration options",

                          " || scan %(buffers_names)"
                          " || help",

                          "cs_command_main", "")


