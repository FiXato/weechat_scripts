# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2013 by Filip H.F. "FiXato" Slagter <fixato@gmail.com>
#
# BattleArena autobattler
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# 2013-05-07: FiXato (freenode.#weechat)
#       0.1 : initial release
SCRIPT_NAME     = "battlearena"
SCRIPT_AUTHOR   = "FiXato <FiXato+weechat@gmail.com>"
SCRIPT_VERSION  = "0.1"
SCRIPT_LICENSE  = "GPL"
SCRIPT_DESC     = "BattleArena Autobattlers"

DEFAULT_OPTIONS         = {
  'channel': ('EsperNET.#battlearena', 'The network.#channel where the Battle Arena is located.'),
  'botnick': ('BattleArena', 'The nickname of the Battle Arena bot that runs the game.'),
  'password': ('Y0r p455w0rd', 'Your BattleArena password'),
  'orbtrain_drivers': ('Raiden Tiranadel', 'High level players that you can hop on an orbtrain with.')
}


try:
  import weechat, re
  from random import choice
except Exception:
  print("This script must be run under WeeChat. Get WeeChat now at: http://www.weechat.org/")
  quit()

tp_delay = 0
available_techs = []
known_techs = []
all_known_techs_by_tech = {}
all_known_techs_by_weapon = {}
battlers = {}
enemies = {}
dead_characters = {}
npcs = {}
players = {}
unknown = {}
current_weapon = None
portal_hooks = []
attack_tech_hook = None
attack_tech_hook2 = None
attack_out_of_tp_hook = None
battle_has_ended_hook = None
in_battle = False

def arena_buffer():
  channel_name = OPTIONS['channel']
  bp = weechat.buffer_search("irc", channel_name)
  return bp

def botnick_tag():
  tag = 'nick_%s' % OPTIONS['botnick']
  return tag

def current_nickname():
  return weechat.buffer_string_replace_local_var(arena_buffer(), "$nick")

def current_channelname():
  return weechat.buffer_string_replace_local_var(arena_buffer(), "$channel")

def current_networkname():
  return weechat.buffer_string_replace_local_var(arena_buffer(), "$server")

def nicks_in_arena():
  nicks = []
  infolist = weechat.infolist_get("irc_nick", "", weechat.buffer_string_replace_local_var(arena_buffer(), "$server,$channel"))
  while weechat.infolist_next(infolist):
    nick = weechat.infolist_string(infolist,'name')
    nicks.append(nick)
  weechat.infolist_free(infolist)
  return nicks

def botnick():
  for nick in nicks_in_arena():
    if OPTIONS['botnick'] in nick:
      return nick
  weechat.prnt(weechat.current_buffer,"Can't find " + OPTIONS['botnick'] + " in channel list.")
  return weechat.WEECHAT_RC_ERROR

def nickmodes(nickname):
  nick_pointer = weechat.nicklist_search_nick(arena_buffer(),"",nickname)
  return weechat.nicklist_nick_get_string(arena_buffer(),nick_pointer,"prefix")

def is_voiced(nickname=None):
  if nickname == None:
    nickname = current_nickname()
  nick_cmodes = nickmodes(nickname)
  # weechat.prnt("", nick_cmodes)
  return ('+' in nick_cmodes)




#=======================Commands==========



def start_autobattle_hooks():
  global attack_tech_hook, attack_tech_hook2, attack_out_of_tp_hook, battle_has_ended_hook
  attack_tech_hook = weechat.hook_print(arena_buffer(), botnick_tag(), 'It is %s\'s turn' % current_nickname(), 1, 'cb_attack_tech_hook', '')
  attack_tech_hook2 = weechat.hook_print(arena_buffer(), botnick_tag(), '%s steps up first in the battle!' % current_nickname(), 1, 'cb_attack_tech_hook', '')
  attack_out_of_tp_hook = weechat.hook_print(arena_buffer(), botnick_tag(), '%s does not have enough TP to perform this technique!' % current_nickname(), 1, 'cb_attack_out_of_tp_hook', '')
  battle_has_ended_hook = weechat.hook_print(arena_buffer(), botnick_tag(), 'The Battle is Over!', 1, 'cb_battle_has_ended_hook', '')

def start_autobattle():
  stop_autobattle()
  global portal_hooks
  portal_hooks = [weechat.hook_print(arena_buffer(), botnick_tag(), 'type !enter if you wish to join the battle!', 1, 'cb_enter_portal', '')]
  start_autobattle_hooks()
  weechat.prnt(weechat.current_buffer(),"AutoBattle started")

def start_autobattle_orbtrain():
  global portal_hooks
  portal_hooks = []
  for nick in OPTIONS['orbtrain_drivers'].split():
    portal_hooks.append(weechat.hook_print(arena_buffer(), botnick_tag(), '%s has entered the battle!' % nick, 1, 'cb_enter_portal', ''))
  start_autobattle_hooks()
  weechat.prnt(weechat.current_buffer(),"AutoBattle (OrbTrain style) started")

def stop_autobattle():
  global portal_hooks, attack_tech_hook, attack_tech_hook2, attack_out_of_tp_hook, battle_has_ended_hook
  for hook in portal_hooks:
    weechat.unhook(hook)
  for hook in (attack_tech_hook, attack_tech_hook2, attack_out_of_tp_hook, battle_has_ended_hook):
    if hook:
      weechat.unhook(hook)
  weechat.prnt(weechat.current_buffer(),"AutoBattle stopped")
  return weechat.WEECHAT_RC_OK

def buy_from_shop(shop_type, item, amount=1):
  weechat.command(arena_buffer(),'/msg %s !shop buy %s %s %s' % (botnick(), shop_type, item, amount))

def change_style(style):
  weechat.command(arena_buffer(),'/msg %s !style change %s' % (botnick(), style))




#=================Retrieve Data========


def get_battlers():
  target_string = '[Battle Order: '
  battle_order_hook = weechat.hook_print("", botnick_tag(), target_string, 1, 'cb_store_battle_order', '')

  target_string = ' has been defeated by '
  battle_order_defeated_hook = weechat.hook_print("", botnick_tag(), target_string, 1, 'cb_battler_defeated_by', '')
   

def cb_store_battle_order(data, buffer, date, tags, displayed, highlight, prefix, message):
  global battlers
  battle_order_regexp = re.compile("\[Battle Order: (?P<battlers>.+)\]")
  m = battle_order_regexp.search(message)
  if m:
    battlers = {battler_name.lower(): battler_name for battler_name in m.groupdict()['battlers'].split(', ')}
  else:
    battlers = {}
  return weechat.WEECHAT_RC_OK

def cb_store_battle_order_colors(data, signal, signal_data): #(data, buffer, date, tags, displayed, highlight, prefix, message):
  global enemies, npcs, players, dead_characters, unknown
  # weechat.prnt("", "cb_store_battle_order_colors(%s,%s,%s)" % (data, signal, signal_data))
  message = signal_data.partition(' :')[2]
  battle_order_regexp = re.compile("\[Battle Order: (?P<battlers>.+)\]")
  m = battle_order_regexp.search(message)
  if m:
    battlers_string = m.groupdict()['battlers']
  else:
    return weechat.WEECHAT_RC_OK

  enemies = {}
  dead_characters = {}
  npcs = {}
  players = {}
  unknown = {}
  color_regex = re.compile("\x03(?P<color>\d{1,2}(?:,\d{1,2})?)(?P<name>\w+)")
  for battler in battlers_string.split(', '):
    m = color_regex.search(battler)
    if m:
      color = int(m.groupdict()['color'])
      battler_name = m.groupdict()['name']
      if color == 3:
        players[battler_name.lower()] = battler_name
      elif color == 5:
        enemies[battler_name.lower()] = battler_name
      elif color == 4:
        dead_characters[battler_name.lower()] = battler_name
      elif color == 12:
        npcs[battler_name.lower()] = battler_name
      else:
        weechat.prnt("", "Unknown colour %s for %s" % (color,battler_name))
        unknown[battler_name.lower()] = battler_name
    else:
      weechat.prnt("", 'No match for ' + battler)
  
  return weechat.WEECHAT_RC_OK

def sanitise_battler_name(name):
  alphanum_name = re.sub(r'[^a-zA-Z0-9]', '', name)
  if 'anothermedusahead' in alphanum_name:
    return 'goldmedusaheadclone'
  elif 'vampirecount' == alphanum_name:
    return 'count'
  elif 'redorbfountain' == alphanum_name:
    return 'orbfountain'
  elif 'vampirecountess' == alphanum_name:
    return 'countess'
  elif 'cloneof' in alphanum_name:
    return alphanum_name.replace('cloneof','') + 'clone'
  return alphanum_name

def get_battler_for_name(name):
  global battlers
  dname = name.lower()
  # names = [dname, dname.replace(' ','_'), dname.replace(' ',''), dname.replace('.','_'), dname.replace('.','_').replace(' ','_'), dname.replace('.','_').replace(' ','')]
  for battler, battler_name in battlers.items():
    # if battler in names:
    if sanitise_battler_name(dname) == sanitise_battler_name(battler):
      return battler
  return None
  

def cb_battler_defeated_by(data, buffer, date, tags, displayed, highlight, prefix, message):
  global battlers, dead_characters, players, enemies, npcs, unknown

  regexp = r"(?P<battler>.+) has been defeated by (?P<enemy>.+)!"
  m = re.match(regexp, message)
  battler_name = m.groupdict()['battler']
  battler = get_battler_for_name(battler_name)
  if not battler:
    weechat.prnt("", "Couldn't find %s in %s" % (battler_name, format_dict(battlers)))
    return weechat.WEECHAT_RC_OK

  dead_characters[battler] = battlers[battler]
  if battler in enemies:
    del enemies[battler]
  elif battler in players:
    del players[battler]
  elif battler in npcs:
    del npcs[battler]
  else:
    unknown[battler] = battlers[battler]
    weechat.prnt("", "Couldn't find %s in enemies %s, players %s or npcs %s" % (battler, format_dict(enemies), format_dict(players), format_dict(npcs)))
  return weechat.WEECHAT_RC_OK




def get_known_techs():
  global known_techs_hook
  #TODO: also handle '$nick does not know any techniques for his $weapon.'
  target_string = current_nickname() + ' knows the following techniques for '
  known_techs_hook = weechat.hook_print("", botnick_tag(), target_string, 1, 'cb_store_known_techs', '')
  weechat.command(arena_buffer(),'/msg %s !techs' % botnick())

def cb_store_known_techs(data, buffer, date, tags, displayed, highlight, prefix, message):
  global known_techs, current_weapon, all_known_techs_by_tech, all_known_techs_by_weapon
  regexp = r"(?P<nickname>\w+) knows the following techniques for (?P<pronoun>\w+) (?P<weapon>\w+): (?P<techs>.+)"
  m = re.match(regexp, message)
  nickname = m.groupdict()['nickname']
  pronoun = m.groupdict()['pronoun']
  current_weapon = m.groupdict()['weapon']
  techs = m.groupdict()['techs']
  known_techs = []

  for tech in techs.split(', '):
    regexp = r"(?P<name>\w+)\((?P<level>\d+)\)"
    tm = re.match(regexp, tech)
    tech_name = tm.groupdict()['name']
    tech_level = tm.groupdict()['level']
    known_techs.append(tech_name)

    if tech_name not in all_known_techs_by_tech:
      all_known_techs_by_tech[tech_name] = {}
    if current_weapon not in all_known_techs_by_tech[tech_name]:
      all_known_techs_by_tech[tech_name][current_weapon] = {}

    if current_weapon not in all_known_techs_by_weapon:
      all_known_techs_by_weapon[current_weapon] = {}
    if tech_name not in all_known_techs_by_weapon[current_weapon]:
      all_known_techs_by_weapon[current_weapon][tech_name] = {}

    all_known_techs_by_tech[tech_name][current_weapon] = tech_level
    all_known_techs_by_weapon[current_weapon][tech_name] = tech_level
  return weechat.WEECHAT_RC_OK



def get_available_techs():
  global available_techs_hook
  available_techs_hook = weechat.hook_print("", botnick_tag(), 'Tech Prices in Red Orbs: ', 1, 'cb_store_available_techs', '')
  weechat.command(arena_buffer(),'/msg %s !shop list techs' % (botnick()))

def cb_store_available_techs(data, buffer, date, tags, displayed, highlight, prefix, message):
  global available_techs, all_techs
  regexp = r"Tech Prices in Red Orbs: (?P<techs>.+)"
  m = re.match(regexp, message)
  techs = m.groupdict()['techs']
  available_techs = []
  for tech in techs.split(', '):
    tm = re.match(r"(?P<name>\w+)\+1 \((?P<upgradecost>\d+)\)", tech)
    tech_name = tm.groupdict()['name']
    tech_upgrade_cost = tm.groupdict()['upgradecost']
    available_techs.append(tech_name)
  return weechat.WEECHAT_RC_OK




#================== CALLBACKS ===================




#==========================Completion
def cb_completion_battle_order(data, completion_item, buffer, completion):
  global battlers
  for battler, battler_name in battlers.items():
    #TODO: exclude other players
    weechat.hook_completion_list_add(completion, battler_name, 0, weechat.WEECHAT_LIST_POS_SORT)
  return weechat.WEECHAT_RC_OK

def cb_completion_battle_players(data, completion_item, buffer, completion):
  global players
  for battler, battler_name in players.items():
    weechat.hook_completion_list_add(completion, battler_name, 0, weechat.WEECHAT_LIST_POS_SORT)
  return weechat.WEECHAT_RC_OK

def cb_completion_battle_enemies(data, completion_item, buffer, completion):
  global enemies
  for battler, battler_name in enemies.items():
    weechat.hook_completion_list_add(completion, battler_name, 0, weechat.WEECHAT_LIST_POS_SORT)
  return weechat.WEECHAT_RC_OK

def cb_completion_known_techs(data, completion_item, buffer, completion):
  global known_techs
  for tech in known_techs:
    weechat.hook_completion_list_add(completion, tech, 0, weechat.WEECHAT_LIST_POS_SORT)
  return weechat.WEECHAT_RC_OK

def cb_completion_available_techs(data, completion_item, buffer, completion):
  global available_techs
  for tech in available_techs:
    weechat.hook_completion_list_add(completion, tech, 0, weechat.WEECHAT_LIST_POS_SORT)
  return weechat.WEECHAT_RC_OK


#==========================Other callbacks
def cb_enter_portal(data, buffer, date, tags, displayed, highlight, prefix, message):
  global in_battle
  if not in_battle:
    in_battle = True
    weechat.hook_timer((choice([2,3,4])) * 1000, 0, 1, "cb_battlecommand", "!enter")
  return weechat.WEECHAT_RC_OK

def cb_attack_tech_hook(data, buffer, date, tags, displayed, highlight, prefix, message):
  global tp_delay
  if tp_delay and tp_delay > 0:
    tp_delay -= 1
    weechat.hook_timer(3 * 1000, 0, 1, "cb_attack", "")
  else:
    tp_delay = 0
    weechat.hook_timer(3 * 1000, 0, 1, "cb_use_tech", "")
  return weechat.WEECHAT_RC_OK

def cb_attack_out_of_tp_hook(data, buffer, date, tags, displayed, highlight, prefix, message):
  global tp_delay
  tp_delay = 5
  weechat.command(buffer, "!tp")
  weechat.command(buffer, "!bat info")
  weechat.hook_timer(2 * 1000, 0, 1, "cb_attack", "")
  return weechat.WEECHAT_RC_OK

def cb_battle_has_ended_hook(data, buffer, date, tags, displayed, highlight, prefix, message):
  global tp_delay, in_battle
  tp_delay = 0
  in_battle = False
  return weechat.WEECHAT_RC_OK

def select_enemy():
  global enemies
  if 'demon_portal' in enemies.keys():
    return 'Demon_Portal'
  else:
    return enemies.values()[0]

def debug_select_tech(criteria=[]):
  global current_weapon
  weapon, tech = select_tech(criteria)
  if weapon != current_weapon:
    weechat.prnt("", equip_weapon_cmd(weapon))
    # weechat.command(arena_buffer(), equip_weapon_cmd(weapon))
    weechat.hook_timer(3 * 1000, 0, 1, "cb_battlecommand", tech_cmd(tech, 'SomeEnemy'))
  else:
    weechat.prnt("", tech_cmd(tech, 'SomeEnemy'))

def select_tech(criteria=[]):
  global all_known_techs_by_weapon, current_weapon
  if 'current_weapon' in criteria:
    weapon = current_weapon
  else:
    weapon = choice(all_known_techs_by_weapon.keys())

  if 'max_level' in criteria:
    tech = max(all_known_techs_by_weapon[weapon].iterkeys(), key=(lambda key: int(all_known_techs_by_weapon[weapon][key])))
  elif 'weakest_level' in criteria:
    tech = min(all_known_techs_by_weapon[weapon].iterkeys(), key=(lambda key: int(all_known_techs_by_weapon[weapon][key])))
  else:
    tech = choice(all_known_techs_by_weapon[weapon].keys())
  
  return weapon, tech

def cb_use_tech(data, remaining_calls):
  use_tech()
  return weechat.WEECHAT_RC_OK

def use_tech(tech=None, enemy=None):
  global current_weapon
  if not enemy:
    enemy = select_enemy()
  if not tech:
    if enemy.lower() == 'evil_fixato':
      weapon, tech = select_tech(['weakest_level', 'current_weapon'])
    else:
      weapon, tech = select_tech()
    
  weechat.prnt("", "Will attack %s with tech %s using %s" % (enemy, tech, weapon))
  if weapon != current_weapon:
    weechat.command(arena_buffer(), equip_weapon_cmd(weapon))
    weechat.hook_timer(3 * 1000, 0, 1, "cb_battlecommand", tech_cmd(tech, enemy))
  else:
    weechat.command(arena_buffer(), tech_cmd(tech, enemy))

def cb_attack(data, remaining_calls):
  attack()
  return weechat.WEECHAT_RC_OK

def cb_battlecommand(data, remaining_calls):
  weechat.prnt("", "Battle command! Remaining: %s" % remaining_calls)
  weechat.command(arena_buffer(), data)
  return weechat.WEECHAT_RC_OK

def equip_weapon_cmd(weapon):
  return "!equip %s" % weapon
  
def tech_cmd(tech, enemy):
  return "/me uses his %s on %s" % (tech, enemy)
  
def attack_cmd(enemy):
  return "/me attacks %s" % enemy

def attack(enemy=None):
  if not enemy:
    enemy = select_enemy()
  weechat.command(arena_buffer(), attack_cmd(enemy))

def format_dict(d):
  return ' | '.join(['%s: %s' % (k, v) for k, v in d.items()])

def cb_command(data, buffer, args):
  global known_techs, current_weapon, available_techs, battlers, enemies, dead_characters, players, npcs, unknown
  if args[0] == '+': #+100str
    m = re.match(r"\+(?P<amount>\d+)(?P<stat>\w+)", args)
    amount = m.groupdict()['amount']
    stat = m.groupdict()['stat']
    buy_from_shop('stats', stat, amount)
  else:
    args = args.split()
    if args[0] == 'report':
      weechat.prnt(weechat.current_buffer(), 'Current Battlers: ' + format_dict(battlers))
      weechat.prnt(weechat.current_buffer(), 'Current Enemies: ' + format_dict(enemies))
      weechat.prnt(weechat.current_buffer(), 'Current Dead Characters: ' + format_dict(dead_characters))
      weechat.prnt(weechat.current_buffer(), 'Current Players: ' + format_dict(players))
      weechat.prnt(weechat.current_buffer(), 'Current NPCs: ' + format_dict(npcs))
      weechat.prnt(weechat.current_buffer(), 'Current Unknowns: ' + format_dict(unknown))
      weechat.prnt(weechat.current_buffer(), 'Current Weapon: ' + current_weapon)
      weechat.prnt(weechat.current_buffer(), 'Known Techs: ' + ', '.join(known_techs))
      weechat.prnt(weechat.current_buffer(), 'Available Techs: ' + ', '.join(available_techs))
      weechat.prnt(weechat.current_buffer(), 'All known Techs by Tech: ')
      for tech, weapon_level in list(all_known_techs_by_tech.iteritems()):
        weechat.prnt(weechat.current_buffer(), ' - %s:' % tech)
        for weapon, level in list(weapon_level.iteritems()):
          weechat.prnt(weechat.current_buffer(), '    - %s: %s' % (weapon, level))

      weechat.prnt(weechat.current_buffer(), 'All known Techs by Weapon: ')
      for weapon, tech_level in list(all_known_techs_by_weapon.iteritems()):
        weechat.prnt(weechat.current_buffer(), ' - %s:' % weapon)
        for tech, level in list(tech_level.iteritems()):
          weechat.prnt(weechat.current_buffer(), '    - %s: %s' % (tech, level))

    if args[0] == 'autobattle':
      if args[1] == 'start':
        start_autobattle()
      if args[1] == 'orbtrain':
        start_autobattle_orbtrain()
      elif args[1] == 'stop':
        stop_autobattle()

    elif args[0] == 'debug':
      if args[1] == 'techs':
        weechat.prnt("", "Weakest current weapon:")
        debug_select_tech(['weakest_level', 'current_weapon'])
        weechat.prnt("", "Best current weapon:")
        debug_select_tech(['max_level', 'current_weapon'])
        weechat.prnt("", "Defaults:")
        debug_select_tech()

    elif args[0] == 'use' and len(args) > 2:
      weechat.command(arena_buffer(),'/me uses his %s on %s' % (args[1], args[2]))

    elif (args[0] in ('stats','items','techs','skills','stats','weapons','styles','orbs','ignitions','portal','misc','gems','alchemy') and (len(args) == 1 or args[1] == 'list')):
      weechat.command(arena_buffer(),'/msg %s !shop list %s' % (botnick(), args[0]))
      weechat.command(arena_buffer(),'/msg %s !%s' % (botnick(), args[0]))

    elif (args[0] in ('stats','items','techs','skills','stats','weapons','styles','orbs','ignitions','portal','misc','gems','alchemy') and args[1] == 'buy'):
      buy_from_shop(args[0],' '.join(args[2:]).replace('_',' '))

    elif (args[0] == 'styles' and args[1] == 'change'):
      change_style(' '.join(args[2:]).replace('_',' '))

    elif args[0] == 'setup' and args[1] == 'bot':
      if len(args) < 3:
        weechat.prnt(weechat.current_buffer(), "You need to specify the bot name after 'setup bot '")
      else:
        buffer = weechat.current_buffer()
        weechat.config_set_plugin('botnick',args[2])
        weechat.config_set_plugin('channel',weechat.buffer_get_string(buffer,'name'))
  return weechat.WEECHAT_RC_OK





# ================================[ weechat options and description ]===============================
def cb_refresh_options(pointer, name, value):
  global OPTIONS
  option = name[len('plugins.var.python.' + SCRIPT_NAME + '.'):]        # get optionname
  OPTIONS[option] = value                                               # save new value
  weechat.prnt("", "Updating OPTIONS[%s] with %s from %s" % (option, value, name))
  return weechat.WEECHAT_RC_OK

def init_options():
  global OPTIONS, DEFAULT_OPTIONS
  OPTIONS = {}
  for option,value in list(DEFAULT_OPTIONS.items()):
    if not weechat.config_get_plugin(option):
      # weechat.prnt("", "Initialising from DEFAULT_OPTIONS[%s] with %s" % (option, value[0]))
      weechat.config_set_plugin(option, value[0])
      #No need to set the OPTION here as cb_refresh_options should take care of that
    else:
      stored_value = weechat.config_get_plugin(option)
      # weechat.prnt("", "Initialising to OPTIONS[%s] from stored variable with %s" % (option, stored_value))
      OPTIONS[option] = stored_value
    #TODO: fix so it doesn't break older weechats that don't support descriptions
    weechat.config_set_desc_plugin(option, '%s (default: "%s")' % (value[1], value[0]))






# ================================[ main ]===============================
if __name__ == "__main__":
  if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, '', ''):
    version = weechat.info_get("version_number", "") or 0
    weechat.hook_config( 'plugins.var.python.' + SCRIPT_NAME + '.*', 'cb_refresh_options', '' )
    init_options()
    weechat.hook_completion("plugin_known_techs", "Known techs completion", "cb_completion_known_techs", "")
    weechat.hook_completion("plugin_available_techs", "Available techs completion", "cb_completion_available_techs", "")
    weechat.hook_completion("plugin_battlers", "Battlers completion", "cb_completion_battle_order", "")
    weechat.hook_completion("plugin_players", "Battlers completion", "cb_completion_battle_players", "")
    weechat.hook_completion("plugin_enemies", "Battlers completion", "cb_completion_battle_enemies", "")
    weechat.hook_signal("EsperNET,irc_in2_privmsg", "cb_store_battle_order_colors", "")
    # weechat.hook_signal("EsperNET,irc_out_privmsg", "cb_store_battle_order_colors", "")
    if arena_buffer():
      if not is_voiced():
        weechat.prnt("", "Not voiced.")
        # weechat.command(arena_buffer(),'/msg %s !id %s' % (botnick(), OPTIONS['password']))
      get_known_techs()
      get_available_techs()
      get_battlers()
    weechat.hook_command("battlearena", "BattleArena client script with autobattle functions.",
        "[shop [list [items|techs|skills|stats|weapons|styles|orbs|ignitions|portal|misc|gems|alchemy]|buy [items|techs|skills|stats [hp|tp|ig|str|def|int|spd]|weapons|styles|orbs|ignitions|portal|misc|gems|alchemy]]] | autobattle [start|end]",
        "description of arguments...",
        "items|skills|weapons|styles|orbs|ignitions|portal|misc|gems|alchemy list|buy"
        " || stats buy|list hp|tp|ig|str|def|int|spd"
        " || styles buy|list|change TRICKSTER|WEAPONMASTER|GUARDIAN|SPELLMASTER|DOPPELGANGER|HITENMITSURUGI-RYU|QUICKSILVER"
        " || techs list|buy %(plugin_available_techs)"
        " || use %(plugin_known_techs) %(plugin_enemies)|%(plugin_players)"
        " || setup bot "
        " || autobattle orbtrain|start|stop",
        "cb_command", "")
