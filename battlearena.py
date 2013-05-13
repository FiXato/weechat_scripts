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
# 2013-05-07: FiXato (freenode.#weechat / espernet.#battlearena)
#       0.1 : initial release
# 2013-05-11: FiXato (freenode.#weechat / espernet.#battlearena)
#       0.2 : Whole bunch of changes I still need to list here.
# 2013-05-12: FiXato (freenode.#weechat / espernet.#battlearena)
#       0.3 : Added Taunting and stealing support amongst others:
#             - Added support for 'gets another turn'.
#             - Also fixed new battle enemy mapping.
#             - Added 'steal_first' setting.
#             - Added 'taunt_first' setting.
#             - Removed cb_attack in favour of cb_battlecommand.
#             - Added a couple more TODOs
#
SCRIPT_NAME     = "battlearena"
SCRIPT_AUTHOR   = "FiXato <FiXato+weechat@gmail.com>"
SCRIPT_VERSION  = "0.3"
SCRIPT_LICENSE  = "GPL"
SCRIPT_DESC     = "BattleArena autobattler and tabcompletion support."

DEBUG = True
DEFAULT_OPTIONS         = {
  'channel': ('EsperNET.#battlearena', 'The network.#channel where the Battle Arena is located.'),
  'botnick': ('BattleArena', 'The nickname of the Battle Arena bot that runs the game.'),
  'password': ('Y0r p455w0rd', 'Your BattleArena password'),
  'orbtrain_drivers': ('Raiden Tiranadel', 'High level players that you can hop on an orbtrain with.'),
  'known_battlers_map_file': ('known_battlers_mapped.txt', 'Where the mapped battlers will be stored.'),
  'preferred_tech_criteria': ('max_level current_weapon', 'Space separated list of preferred tech criteria. Leave empty to use the default, which is random.'),
  'override_tech': ('', 'Set this to a tech name if you want to override the tech that will be used during autobattle.'),
  'taunt_first': ('no', 'Set this to "yes" if you want to taunt an enemy first in the battle.  Use "random_once" if you want to leave it to choice once per battler, or "random_always" if you want it to always randomly try to taunt.'),
  'steal_first': ('no', 'Set this to "yes" if you want to steal from an enemy first in the battle.'),
  'orbs.red.current': ('0', 'Current amount of red orbs.'),
  'orbs.black.current': ('0', 'Current amount of black orbs.'),
  'orbs.red.spent': ('0', 'Total amount of red orbs spent.'),
  'orbs.black.spent': ('0', 'Total amount of black orbs spent.')
}
COLORRESET = 'resetcolor' #TODO: set this to 'reset' if version < 0.3.6 

try:
  import weechat, re, os
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
orbcount_hooks = []
attack_tech_hook, attack_tech_hook2, attack_tech_hook3, attack_out_of_tp_hook = (None, None, None, None)
battle_has_ended_hook, battle_melee_only_hook, battle_new_battler_has_entered_hook = (None, None, None)
in_battle, melee_only, has_taunted, has_stolen = (False, False, False, False)
retry_counter = 0
battle_mode = 'Normal'
player_turn = None
health_status = ''
status_effects = []
active_skills = []

known_battlers = ["AbsoluteVirtue", "Acrobat", "Ahtu", "Air_Elemental", "Alucard", "Anders", "AndroidX", "Aris", "Arucard", "Ashi", "Ashmaker_Gotblut", "Baelfyr", "BahamutFury", "Balrog", "Bark_Spider", "Bayonetta", "BearShark", "Bee", "BeeBear", "Bigmouth_Billy", "BloodGoyle", "Bloody_Bones", "BlueSlime", "Blue_MedusaHead", "Bone_Soldier", "Brauner", "Byrgen", "Cactuar", "Cave_Tiger", "Cell", "Cell_clone", "Cerberus", "Chimyriad", "Chuckie", "ChunLi", "Citadel_Bats", "Cloud", "Combat", "Count", "Count_Bifrons", "Countess", "Crazy_Jester", "Creeper", "Crimson_Slime", "CureSlime", "Cursed_Bishop", "Cursed_King", "Cursed_Pawn", "Cursed_Queen", "Cursed_Rook", "CyberLord", "Cyberman", "Dalek", "DalekEmperor", "Dante", "Daos", "Dark_Ixion", "Dark_Knight", "Dark_Octopus", "Death", "Decapiclops", "Dekar", "Demon_Knight", "Demon_Portal", "Demon_Samurai", "Demon_Warrior", "Demon_Wizard", "Devil_Manta", "Ding_Bats", "Dirt_Eater", "Don_Kanonji", "Drachenlizard", "Dracula", "Dragoon_Ghost", "Dredd", "Dresden", "Dullahan", "Dune_Widow", "Earth_Elemental", "Enchanted_Bones", "Ermit_Imp", "Fafnir", "Female_Vampire", "Final_Guard", "FootballZombie", "Forest_Giant", "Gades", "Garland", "GearRay", "GearRex", "Gekko", "GekkoDwarf", "Geyfyrst", "Ghost_Bomb", "Ghost_Samurai", "Goblin_Berserker", "Goblin_Enchanter", "Goblin_Shaman", "Goblin_Smithy", "Gold_MedusaHead", "Gold_MedusaHead_clone", "Gothmog", "Greater_Pugil", "GuardDaos", "Guardian_Treant", "HealSlime", "Healing_Slime", "Heraldic_Imp", "Ichigo", "Iori", "Ironshell", "Jailor_of_Love", "Jeffery", "Jester", "Juliet", "JumboCactuar", "Kain", "Ken", "Killer_Rabbit", "Kindred_Knight", "Kindred_Samurai", "Kindred_Warrior", "Kindred_Wizard", "KingSlime", "KnightsNi", "Kosmos", "Large_Warmachine", "Latrilth", "Leaping_Lizzie", "Lenneth", "M_Bison", "Magnes_Quadav", "Male_Vampire", "Mammoth", "Maneating_Hornet", "Maria", "Marquis_Caim", "Maxim", "Medium_Warmachine", "Megaman", "MegamanX", "Menos_Grande", "MetalSlime", "Midnight_Slime", "Minotaur", "Moblin", "Moonfang", "Nauthima", "Nauthima_Tiranadel", "Nightmare_Hornet", "Nightmare_Vanguard", "Ninja_Assassin", "Ninja_Assassin_clone", "Orcish_Grunt", "Orcish_Gunshooter", "Orcish_Impaler", "Orcish_Predator", "Orcish_Wyrmbrander", "Orphen", "Oxocutioner", "Pallid_Percy", "PoisonSlime", "Poisonhand", "Poring", "Pride_Demon", "Prishe", "Pugil", "Puppet_Master", "Rainemard", "Randith", "Reaver", "RedSlime", "Retro_Hippie", "Revenant", "River_Crab", "Rock_Lizard", "Rose", "Ruby_Quadav", "Ryu", "Ryudo", "Ryukotsuki", "Sabertooth_Tiger", "Samurai_Ghost", "Samus", "SandyClaws", "Sapphire_Quadav", "Scorpion", "Sea_Horror", "Seiryu", "Selan", "Shanoa", "Shrapnel", "Sierra_Tiger", "Simon_Belmont", "Small_Warmachine", "Snow_Giant", "Snow_Lizard", "Snow_Wight", "Soma", "Squall", "Starman_Ghost", "Starman_Junior", "Stefenth", "Stone_Eater", "Strolling_Sapling", "Sub_Zero", "Succubus", "Suzaku", "Terry", "Thunder_Elemental", "Tia", "Tiamat", "Treant", "TrueErim", "Undead_BlackMage", "Undead_Corsair", "Undead_Dragoon", "Undead_Knight", "Undead_Monk", "Undead_Ranger", "Undead_RedMage", "Undead_Samurai", "Ungeweder", "Unicorn", "Urahara", "Vampire_Bat", "Vergil", "Volcano_Wasp", "Vyse", "Water_Elemental", "Wild_Rabbit", "Wonenth", "Wooden_Puppet", "Wyvern", "Yagudo_Oracle", "Yagudo_Prior", "Yagudo_Prioress", "Yagudo_Scribe", "Yagudo_Zealot", "Yanthu", "Yoko", "Yoruichi", "Yoruichi_Shihouin", "Zark", "Zarklet", "Zero", "ZombieChef", "ZombieRockStar", "Zu", "chaos", "evil_FiXato", "evil_Tiranadel", "orb_fountain", "zombie"]

known_battlers_mapped = {
  'Demon Portal': 'Demon_Portal', 
  'New Age Retro Hippie': 'Retro_Hippie',
  'Medium Warmachine': 'Medium_Warmachine'
}

def arena_buffer():
  channel_name = OPTIONS['channel']
  bp = weechat.buffer_search("irc", channel_name)
  return bp

def bot_buffer():
  bp = weechat.buffer_search("irc", '%s.%s' % (current_networkname(), botnick()))
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
  global attack_tech_hook, attack_tech_hook2, attack_tech_hook3, attack_out_of_tp_hook, battle_has_ended_hook, battle_new_battler_has_entered_hook, battle_melee_only_hook
  # attack_tech_hook  = weechat.hook_print(arena_buffer(), botnick_tag(), 'It is %s\'s turn' % current_nickname(), 1, 'cb_turn_hook', '')
  attack_tech_hook  = weechat.hook_print(arena_buffer(), botnick_tag(), "'s turn [Health Status:", 1, 'cb_turn_hook', '')
  attack_tech_hook2 = weechat.hook_print(arena_buffer(), botnick_tag(), '%s steps up first in the battle!' % current_nickname(), 1, 'cb_turn_hook', '')
  attack_tech_hook3  = weechat.hook_print(arena_buffer(), botnick_tag(), '%s gets another turn.' % current_nickname(), 1, 'cb_turn_hook', '')
  attack_out_of_tp_hook = weechat.hook_print(arena_buffer(), botnick_tag(), '%s does not have enough TP to perform this technique!' % current_nickname(), 1, 'cb_attack_out_of_tp_hook', '')
  battle_has_ended_hook = weechat.hook_print(arena_buffer(), botnick_tag(), 'The Battle is Over!', 1, 'cb_battle_has_ended_hook', '')
  battle_new_battler_has_entered_hook = weechat.hook_print(arena_buffer(), botnick_tag(), ' has entered the battle!', 1, 'cb_battle_new_battler_has_entered', '')
  battle_melee_only_hook = weechat.hook_print(arena_buffer(), botnick_tag(), 'An ancient Melee-Only symbol glows on the ground of the battlefield.', 1, 'cb_battle_melee_only', '')
  

def start_autobattle(mode='autoattack'):
  stop_autobattle()

  global portal_hooks
  if mode.lower() == 'autoattack':
    portal_hooks = [weechat.hook_print(arena_buffer(), botnick_tag(), 'type !enter if you wish to join the battle!', 1, 'cb_enter_portal', '')]
    set_battle_mode('AutoAttack')
  elif mode.lower() == 'orbtrain':
    portal_hooks = []
    for nick in OPTIONS['orbtrain_drivers'].split():
      portal_hooks.append(weechat.hook_print(arena_buffer(), botnick_tag(), '%s has entered the battle!' % nick, 1, 'cb_enter_portal', ''))
    set_battle_mode('OrbTrain')
  elif mode.lower() == 'tracking':
    set_battle_mode('Tracking')
  else:
    set_battle_mode('Unknown')

  start_autobattle_hooks()
  weechat.prnt(weechat.current_buffer(),"AutoBattle started in %s mode" % mode)

def set_battle_mode(mode):
  global battle_mode
  battle_mode = mode
  weechat.bar_item_update("battlearena_battle_mode")
  return battle_mode
  
def cb_battle_mode_item(data, item, window):
  global battle_mode
  if battle_mode == 'OrbTrain':
    color = 'yellow'
  elif battle_mode == 'Normal':
    color = 'green'
  elif battle_mode == 'AutoAttack':
    color = 'lightred'
  else:
    color = '*default'
  return '' + weechat.color(color) + battle_mode + weechat.color(COLORRESET) + ''

def stop_autobattle():
  global portal_hooks, attack_tech_hook, attack_tech_hook2, attack_tech_hook3, attack_out_of_tp_hook, battle_has_ended_hook, battle_new_battler_has_entered_hook, battle_melee_only_hook
  for hook in portal_hooks:
    weechat.unhook(hook)
  for hook in (attack_tech_hook, attack_tech_hook2, attack_tech_hook3, attack_out_of_tp_hook, battle_has_ended_hook, battle_new_battler_has_entered_hook, battle_melee_only_hook):
    if hook:
      weechat.unhook(hook)
  weechat.prnt(weechat.current_buffer(),"AutoBattle stopped")
  set_battle_mode('Normal')
  return weechat.WEECHAT_RC_OK

def buy_from_shop(shop_type, item, amount=1):
  weechat.command(arena_buffer(),'/msg %s !shop buy %s %s %s' % (botnick(), shop_type, item, amount))

def change_style(style):
  weechat.command(arena_buffer(),'/msg %s !style change %s' % (botnick(), style))




#=================Retrieve Data========

def add_orbcount_hooks():
  global orbcount_hooks
  orbcount_hooks.append(weechat.hook_print("", botnick_tag(), 'Black Orb(s) and has spent', 1, 'cb_orbcount', ''))
  orbcount_hooks.append(weechat.hook_print("", botnick_tag(), 'For their victory, these players have been rewarded with Red Orbs', 1, 'cb_orb_reward', ''))
  orbcount_hooks.append(weechat.hook_print("", botnick_tag(), 'The following players have absorbed a black orb from the boss: ', 1, 'cb_black_orb_reward', ''))
  orbcount_hooks.append(weechat.hook_print("", botnick_tag(), 'unlocks the treasure chest and obtains ', 1, 'cb_unlock_chest', ''))
  #TODO: FiXato unlocks the treasure chest and obtains 902 Red Orbs! The chest then disappears.

def cb_unlock_chest(data, buffer, date, tags, displayed, highlight, prefix, message):
  #TODO: FiXato unlocks the treasure chest and obtains 902 Red Orbs! The chest then disappears.
  regexp = re.compile("(?P<player>\S+) unlocks the treasure chest and obtains (?P<amount>\S+) (?P<item>.+?)! The chest then disappears.")
  m = regexp.search(message)
  if m and m.groupdict()['player'] == current_nickname():
    if m.groupdict()['item'] == 'Red Orbs':
      new_red_orbs_count = orbs_string_to_int(OPTIONS['orbs.red.current']) + orbs_string_to_int(m.groupdict()['amount'])
      weechat.config_set_plugin('orbs.red.current', comma_string(string_to_int(new_red_orbs_count)))
    elif m.groupdict()['item'] == 'Black Orbs' or m.groupdict()['item'] == 'Black Orb':
      new_black_orbs_count = orbs_string_to_int(OPTIONS['orbs.black.current']) + orbs_string_to_int(m.groupdict()['amount'])
      weechat.config_set_plugin('orbs.black.current', comma_string(string_to_int(new_black_orbs_count)))
    else:
      # TODO: Parse other items
      weechat.prnt("", "cb_unlock_chest(): Found: %sx %s" % (orbs_string_to_int(m.groupdict()['amount']), m.groupdict()['item']))
  else:
    weechat.prnt("", "cb_unlock_chest(): Can't find %s in %s" % (current_nickname(), message))
  return weechat.WEECHAT_RC_OK

def cb_orbcount(data, buffer, date, tags, displayed, highlight, prefix, message):
  regexp = re.compile("(?P<player>\S+) has (?P<orbs_red_current>\S+) Red Orbs and (?P<orbs_black_current>\S+) Black Orb\(s\) and has spent (?P<orbs_red_spent>\S+) Red Orbs and (?P<orbs_black_spent>\S+) Black Orb\(s\) total!")
  m = regexp.search(message)
  if m and m.groupdict()['player'] == current_nickname():
    for key in ('orbs.red.current', 'orbs.black.current', 'orbs.red.spent', 'orbs.black.spent'):
      weechat.config_set_plugin(key, m.groupdict()[key.replace('.','_')])
  else:
    weechat.prnt("", "cb_orbcount(): Can't find %s in %s" % (current_nickname(), message))
  return weechat.WEECHAT_RC_OK

def cb_black_orb_reward(data, buffer, date, tags, displayed, highlight, prefix, message):
  weechat.prnt("", "cb_black_orb_reward(): %s" % message)
  regexp = re.compile("The following players have absorbed a black orb from the boss: ([^,\s]+?, )*%s([^,\s]+?, )*" % current_nickname())
  m = regexp.search(message)
  if m:
    weechat.prnt("", "cb_black_orb_reward(): Found a match for %s in %s" % (current_nickname(), message))
    new_black_orbs_count = orbs_string_to_int(OPTIONS['orbs.black.current']) + 1
    weechat.prnt("", "cb_black_orb_reward(): Increased black orbs count with 1 to %s" % new_black_orbs_count)
    weechat.config_set_plugin('orbs.black.current', orbs_comma_string(new_black_orbs_count))
  else:
    weechat.prnt("", "cb_black_orb_reward(): Can't find %s in %s" % (current_nickname(), message))
      
  return weechat.WEECHAT_RC_OK

def cb_orb_reward(data, buffer, date, tags, displayed, highlight, prefix, message):
  weechat.prnt("", "cb_orb_reward(): %s" % message)
  regexp = re.compile("For their victory, these players have been rewarded with Red Orbs: .*%s\[\+(?P<red_orbs>(\d{1,3},?)+)\] ?" % current_nickname())
  m = regexp.search(message)
  if m and m.groupdict()['red_orbs']:
    new_red_orbs_count = orbs_string_to_int(OPTIONS['orbs.red.current']) + orbs_string_to_int(m.groupdict()['red_orbs'])
    weechat.config_set_plugin('orbs.red.current', orbs_comma_string(new_red_orbs_count))
      
  return weechat.WEECHAT_RC_OK

def get_orbcount():
  botcommand("!orbs")
  return weechat.WEECHAT_RC_OK

#TODO: Make these different
def orbs_string_to_int(orbs):
  return int(orbs.replace(',',''))
def string_to_int(item):
  return orbs_string_to_int(item)

#TODO: Make these different
def orbs_comma_string(orbs):
  return "{:,}".format(int(str(orbs).replace(',','')))
def comma_string(item):
  return orbs_comma_string(item)

def cb_orbs_item(data, item, window):
  red_current = weechat.color('red') + orbs_comma_string(OPTIONS['orbs.red.current']) + weechat.color(COLORRESET)
  red_spent = weechat.color('red') + orbs_comma_string(OPTIONS['orbs.red.spent']) + weechat.color(COLORRESET)
  black_current = weechat.color('darkgray') + orbs_comma_string(OPTIONS['orbs.black.current']) + weechat.color(COLORRESET)
  black_spent = weechat.color('darkgray') + orbs_comma_string(OPTIONS['orbs.black.spent']) + weechat.color(COLORRESET)
  return 'Orbs: %s/%s %s/%s' % (red_current, red_spent, black_current, black_spent)

def cb_current_weapon_item(data, item, window):
  global current_weapon
  return "Weapon: %s" % current_weapon

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
  alphanum_name = alphanum_name.replace('evildoppelgangerof','evil')
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

def find_plausible_battler_for_name(name):
  global known_battlers
  dname = name.lower()
  sanitised_name = sanitise_battler_name(dname)
  sanitised_known_battlers = [sanitise_battler_name(battler_name.lower()) for battler_name in known_battlers]
  if sanitised_name in sanitised_known_battlers:
    return known_battlers[sanitised_known_battlers.index(sanitised_name)]
  return None

def get_battler_for_name(name):
  global battlers
  dname = name.lower()
  # names = [dname, dname.replace(' ','_'), dname.replace(' ',''), dname.replace('.','_'), dname.replace('.','_').replace(' ','_'), dname.replace('.','_').replace(' ','')]
  for battler, battler_name in battlers.items():
    # if battler in names:
    if sanitise_battler_name(dname) == sanitise_battler_name(battler):
      return battler
  return None
  
def cb_battle_melee_only(data, buffer, date, tags, displayed, highlight, prefix, message):
  global melee_only
  melee_only = True
  return weechat.WEECHAT_RC_OK

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
    if battler.lower() == current_nickname().lower():
      update_health_status('Dead')
    del players[battler]
  elif battler in npcs:
    del npcs[battler]
  else:
    unknown[battler] = battlers[battler]
    weechat.prnt("", "Couldn't find %s in enemies %s, players %s or npcs %s" % (battler, format_dict(enemies), format_dict(players), format_dict(npcs)))
  return weechat.WEECHAT_RC_OK


def save_known_battlers():
  global known_battlers_mapped
  with open(OPTIONS['known_battlers_map_file'], 'w') as f:
    weechat.prnt("", os.path.abspath(OPTIONS['known_battlers_map_file']))
    for battler_name, battler in known_battlers_mapped.iteritems():
      if battler and battler_name and len(battler) > 0 and len(battler_name) > 0:
        f.write("%s: %s\n" % (battler, battler_name))

def load_known_battlers():
  global known_battlers_mapped
  try:
    weechat.prnt("", os.path.abspath(OPTIONS['known_battlers_map_file']))
    with open(OPTIONS['known_battlers_map_file'], 'r') as f:
      for line in f:
        battler, sep, battler_name = line.partition(': ')
        if battler_name not in known_battlers_mapped:
          known_battlers_mapped[battler_name] = battler
  except IOError:
    with open(OPTIONS['known_battlers_map_file'], 'w') as f:
      f.write('')
    
def cb_battle_new_battler_has_entered(data, buffer, date, tags, displayed, highlight, prefix, message):
  global enemies, known_battlers_mapped

  regexp = r"(?P<battler>.+) has entered the battle!"
  m = re.match(regexp, message)
  battler_name = m.groupdict()['battler']
  if battler_name in known_battlers_mapped:
    weechat.prnt("", "Already know %s as %s" % (battler_name, known_battlers_mapped[battler_name]))
    enemies[known_battlers_mapped[battler_name].lower()] = known_battlers_mapped[battler_name]
    battlers[known_battlers_mapped[battler_name].lower()] = known_battlers_mapped[battler_name]
    return weechat.WEECHAT_RC_OK

  plausible_battler_name = find_plausible_battler_for_name(battler_name)
  if plausible_battler_name:
    weechat.prnt("", "%s is probably %s" % (battler_name, plausible_battler_name))
    enemies[plausible_battler_name.lower()] = plausible_battler_name
    battlers[plausible_battler_name.lower()] = plausible_battler_name
    known_battlers_mapped[battler_name] = plausible_battler_name
    save_known_battlers()
  return weechat.WEECHAT_RC_OK



def get_known_techs():
  global known_techs_hook
  #TODO: also handle '$nick does not know any techniques for his $weapon.'
  target_string = current_nickname() + ' knows the following techniques for '
  known_techs_hook = weechat.hook_print("", botnick_tag(), target_string, 1, 'cb_store_known_techs', '')
  weechat.command(arena_buffer(),'/msg %s !techs' % botnick())

def update_current_weapon(weapon):
  global current_weapon
  if current_weapon != weapon:
    current_weapon = weapon
    weechat.bar_item_update("battlearena_current_weapon")
  return current_weapon

def cb_store_known_techs(data, buffer, date, tags, displayed, highlight, prefix, message):
  global known_techs, current_weapon, all_known_techs_by_tech, all_known_techs_by_weapon
  regexp = r"(?P<nickname>\w+) knows the following techniques for (?P<pronoun>\w+) (?P<weapon>\w+): (?P<techs>.+)"
  m = re.match(regexp, message)
  nickname = m.groupdict()['nickname']
  pronoun = m.groupdict()['pronoun']
  current_weapon = update_current_weapon(m.groupdict()['weapon'])
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
    update_health_status('Perfect')
    update_status_effects('None')
    update_active_skills('None')
  return weechat.WEECHAT_RC_OK

def cb_turn_hook(data, buffer, date, tags, displayed, highlight, prefix, message):
  global tp_delay, melee_only, battle_mode

  regexp = re.compile("((?P<player_a>.+?) gets another turn.|(?P<player_b>.+?) steps up first in the battle!|It is (?P<player_c>.+?)'s turn \[Health Status: (?P<health_status>[^\]]+)\] \[Status Effects: (?P<status_effects>[^]]+)\] \[Active Skills: (?P<active_skills>[^\]]+)\])")
  m = regexp.search(message)
  if m:
    player_list = [m.groupdict()['player_a'], m.groupdict()['player_b'], m.groupdict()['player_c']]
    player = player_list[map(bool, player_list).index(True)]
    update_player_turn(player)
    if player == current_nickname():
      if m.groupdict()['health_status']:
        update_health_status(m.groupdict()['health_status'])
        update_status_effects(m.groupdict()['status_effects'])
        update_active_skills(m.groupdict()['active_skills'])
    else:

      return weechat.WEECHAT_RC_OK
  else:
    weechat.prnt("", "Could not parse turn message: %s" % message)
    return weechat.WEECHAT_RC_OK

  if battle_mode.lower() in ('normal', 'tracking'):
    return weechat.WEECHAT_RC_OK

  if not can_attack():
    return weechat.WEECHAT_RC_OK
  if check_steal():
    weechat.hook_timer(4 * 1000, 0, 1, "cb_battlecommand", steal_cmd(select_enemy()))
    return weechat.WEECHAT_RC_OK
  if check_taunt():
    weechat.hook_timer(4 * 1000, 0, 1, "cb_battlecommand", taunt_cmd(select_enemy()))
    return weechat.WEECHAT_RC_OK
  if melee_only or check_cursed():
    weechat.hook_timer(3 * 1000, 0, 1, "cb_battlecommand", attack_cmd(select_enemy()))
    return weechat.WEECHAT_RC_OK
  if tp_delay and tp_delay > 0:
    tp_delay -= 1
    weechat.prnt("", "Setting cb_battlecommand timer for attack_cmd")
    weechat.hook_timer(4 * 1000, 0, 1, "cb_battlecommand", attack_cmd(select_enemy()))
  else:
    tp_delay = 0
    weechat.prnt("", "Setting cb_use_tech timer")
    weechat.hook_timer(4 * 1000, 0, 1, "cb_use_tech", "")
  return weechat.WEECHAT_RC_OK

def log(obj):
  if DEBUG:
    weechat.prnt("", obj)

def can_attack():
  global status_effects
  if 'intimidated' in status_effects:
    return False
  elif 'paralyzed' in status_effects:
    return False
  elif 'frozen in time' in status_effects:
    return False
  elif 'bored' in status_effects:
    return False
  elif 'stunned' in status_effects:
    return False
  return True

def check_cursed():
  global status_effects
  if 'cursed' in status_effects:
    return True
  return False

def check_steal():
  global has_stolen
  if has_stolen:
    log("Has already stolen from this party.")
    return False

  #TODO: Support stealing once *per enemy*
  if OPTIONS['steal_first'] in ('yes', 'on'):
    log("Will steal first because steal_first is %s" % OPTIONS['steal_first'])
    has_stolen = True
    return True
  else:
    return False

def check_taunt():
  global has_taunted
  if has_taunted:
    log("Have already taunted.")
    return False

  if OPTIONS['taunt_first'] in ('yes', 'on'):
    log("Will taunt first")
    will_taunt = True
  elif OPTIONS['taunt_first'] in ('random_once', 'random_always'):
    will_taunt = choice([True, False])
    log("Random pick for taunt_first(%s): %s" % (OPTIONS['taunt_first'], will_taunt))
  else:
    log("Won't taunt because taunt_first is %s" % (OPTIONS['taunt_first']))
    return False
  
  if not will_taunt:
    log("Won't taunt because will_taunt is %s" % (will_taunt))
    return False

  if OPTIONS['taunt_first'] == 'random_always':
    has_taunted = False
  else:
    has_taunted = True
  log("has_taunted has been set to %s" % has_taunted)
  return True

def cb_attack_out_of_tp_hook(data, buffer, date, tags, displayed, highlight, prefix, message):
  global tp_delay, battle_mode
  if battle_mode.lower() not in ('autoattack', 'orbtrain'):
    return weechat.WEECHAT_RC_OK
  tp_delay = 5
  weechat.command(buffer, "!tp")
  weechat.command(buffer, "!bat info")
  weechat.hook_timer(3 * 1000, 0, 1, "cb_battlecommand", attack_cmd(select_enemy()))
  return weechat.WEECHAT_RC_OK

def cb_battle_has_ended_hook(data, buffer, date, tags, displayed, highlight, prefix, message):
  global tp_delay, in_battle, melee_only, has_taunted, has_stolen
  tp_delay = 0
  in_battle = False
  melee_only = False
  has_taunted = False
  has_stolen = False
  update_player_turn('')
  update_health_status('')
  update_status_effects('')
  update_active_skills('')

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
  elif 'random' in criteria:
    tech = choice(all_known_techs_by_weapon[weapon].keys())
  else:
    tech = choice(all_known_techs_by_weapon[weapon].keys())
  
  return weapon, tech

def cb_use_tech(data, remaining_calls):
  tech = None
  if OPTIONS['override_tech'] and len(OPTIONS['override_tech']) > 0:
    tech = OPTIONS['override_tech']
    weechat.prnt("", "Set tech to %s" % tech)
  use_tech(tech)
  return weechat.WEECHAT_RC_OK

def use_tech(tech=None, enemy=None):
  global current_weapon
  weapon = current_weapon
  if not enemy:
    enemy = select_enemy()
  if not tech:
    if enemy.lower() == 'evil_fixato':
      criteria = ['weakest_level', 'current_weapon']
    else:
      criteria = OPTIONS['preferred_tech_criteria'].split()
    weapon, tech = select_tech(criteria)
    weechat.prnt("", "Tech wasn't set, so selected %s as tech based on %s criteria" % (tech, ' & '.join(criteria)))
    
  weechat.prnt("", "Will attack %s with tech %s using %s" % (enemy, tech, weapon))
  if weapon != current_weapon:
    weechat.command(arena_buffer(), equip_weapon_cmd(weapon))
    weechat.hook_timer(4 * 1000, 0, 1, "cb_battlecommand", tech_cmd(tech, enemy))
  else:
    weechat.hook_timer(4 * 1000, 0, 1, "cb_battlecommand", tech_cmd(tech, enemy))

def cb_battlecommand(data, remaining_calls):
  weechat.prnt("", "Battle command! Remaining: %s" % remaining_calls)
  weechat.command(arena_buffer(), data)
  return weechat.WEECHAT_RC_OK

def cb_botcommand(data, remaining_calls=0):
  global retry_counter
  buffer = bot_buffer()
  if not buffer:
    if retry_counter < 1:
      weechat.prnt(weechat.current_buffer(), "Error: You need to open a query with the bot first. Will retry in 2 seconds.")
      weechat.command(arena_buffer(),'/query %s' % (botnick()))
      weechat.hook_timer(2 * 1000, 0, 1, "cb_botcommand", data)
    else:
      weechat.prnt(weechat.current_buffer(), "Error: You need to open a query with the bot first. Already tried retrying once; won't try again.")
      return weechat.WEECHAT_RC_ERROR
  else:
    retry_counter = 0
    weechat.command(buffer,data)
  return weechat.WEECHAT_RC_OK

def botcommand(cmd):
  return cb_botcommand(cmd, 0)

def cb_botmsg(data, remaining_calls=0):
  buffer = bot_buffer()
  if not buffer:
    weechat.command(arena_buffer(),'/msg %s %s' % (botnick(), data))
  else:
    weechat.command(buffer,'%s' % (data))
  return weechat.WEECHAT_RC_OK

def cb_botaction(data, remaining_calls=0):
  buffer = bot_buffer()
  if not buffer:
    weechat.command(arena_buffer(),'/CTCP %s ACTION %s' % (botnick(), data))
  else:
    weechat.command(buffer,'/me %s' % (data))
  return weechat.WEECHAT_RC_OK

def taunt_cmd(enemy):
  return "!taunt %s" % enemy

def steal_cmd(enemy):
  return "!steal %s" % enemy

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

#=========================Bar items=============================
def cb_player_turn_item(data, item, window):
  global player_turn
  if player_turn and len(player_turn) > 0:
    return 'Turn: %s' % player_turn
  else:
    return ''

def update_player_turn(player_string):
  global player_turn
  player_turn = player_string.strip()
  weechat.bar_item_update("battlearena_player_turn")

def cb_health_status_item(data, item, window):
  global health_status
  if health_status and len(health_status) > 0:
    if health_status == 'Perfect':
      color = '*green'
      pct = '100%'
    elif health_status == 'Great':
      color = 'green'
      pct = '90-100%'
    elif health_status == 'Good':
      color = '*lightgreen'
      pct = '80-90%'
    elif health_status == 'Decent':
      color = 'lightgreen'
      pct = '70-80%'
    elif health_status == 'Scratched':
      color = '*yellow'
      pct = '60-70%'
    elif health_status == 'Bruised':
      color = 'yellow'
      pct = '50-60%'
    elif health_status == 'Hurt':
      color = '*brown'
      pct = '40-50%'
    elif health_status == 'Injured':
      color = 'brown'
      pct = '30-40%'
    elif health_status == 'Injured Badly':
      color = 'lightred'
      pct = '15-30%'
    elif health_status == 'Critical':
      color = 'red'
      pct = '2-15%'
    elif health_status == "Alive by a hair's bredth":
      color = 'darkgrey'
      pct = '0-2%'
    else:
      color = 'gray'
      pct = '0%'
    status_string = weechat.color(color) + health_status + weechat.color('reset') + ' (%s)' % pct
    return weechat.color('bold') + 'Health: ' + weechat.color('-bold') + status_string
  else:
    return ''

def update_health_status(health_string):
  global health_status
  if health_string:
    health_status = health_string.strip()
  else:
    health_status = ''
  weechat.bar_item_update("battlearena_health_status")
  return health_status



def cb_status_effects_item(data, item, window):
  global status_effects
  if len(status_effects) > 0:
    status_string = weechat.color('red') + '; '.join(status_effects) + weechat.color(COLORRESET)
    return weechat.color('bold') + 'Status: ' + weechat.color('-bold') + status_string
  else:
    return ''

def update_status_effects(status_effects_string):
  global status_effects
  status_effects = map(lambda s: s.strip(), status_effects_string.split('|'))
  if status_effects_string and status_effects_string != '':
    status_effects = map(lambda s: s.strip(), status_effects_string.split('|'))
  else:
    status_effects = []
  weechat.bar_item_update("battlearena_status_effects")
  return status_effects



def cb_active_skills_item(data, item, window):
  global active_skills
  if active_skills and len(active_skills) > 0:
    status_string = weechat.color('green') + '; '.join(active_skills) + weechat.color(COLORRESET)
    return weechat.color('bold') + 'ASkills: ' + weechat.color('-bold') + status_string
  else:
    return ''

def update_active_skills(skills_string):
  global active_skills
  if skills_string and skills_string != '':
    active_skills = map(lambda s: s.strip(), skills_string.split('|'))
  else:
    active_skills = []
  weechat.bar_item_update("battlearena_active_skills")
  return active_skills


#===============================================================


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
        start_autobattle('autoattack')
      if args[1] == 'orbtrain':
        start_autobattle('orbtrain')
      elif args[1] == 'stop':
        stop_autobattle()
      elif args[1] == 'tracking':
        start_autobattle('tracking')

    elif args[0] == 'debug':
      if args[1] == 'techs':
        weechat.prnt("", "Weakest current weapon:")
        debug_select_tech(['weakest_level', 'current_weapon'])
        weechat.prnt("", "Best current weapon:")
        debug_select_tech(['max_level', 'current_weapon'])
        weechat.prnt("", "Defaults:")
        debug_select_tech()
      if args[1] == 'save':
        save_known_battlers()

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
  if 'orbs' in option:
    weechat.bar_item_update("battlearena_orbs")
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
    weechat.hook_completion("plugin_battlers", "Battlers (All) completion", "cb_completion_battle_order", "")
    weechat.hook_completion("plugin_players", "Battlers (Players) completion", "cb_completion_battle_players", "")
    weechat.hook_completion("plugin_enemies", "Battlers (Enemies) completion", "cb_completion_battle_enemies", "")
    weechat.hook_signal("EsperNET,irc_in2_privmsg", "cb_store_battle_order_colors", "")
    # weechat.hook_signal("EsperNET,irc_out_privmsg", "cb_store_battle_order_colors", "")
    if arena_buffer():
      if not is_voiced():
        weechat.prnt("", "Not voiced.")
        weechat.command(arena_buffer(),'/msg %s !id %s' % (botnick(), OPTIONS['password']))
      get_known_techs()
      get_available_techs()
      get_battlers()
      load_known_battlers()
      add_orbcount_hooks()
      get_orbcount()
      orbs_bar_item = weechat.bar_item_new("battlearena_orbs", "cb_orbs_item", "")
      current_weapon_item = weechat.bar_item_new("battlearena_current_weapon", "cb_current_weapon_item", "")
      battle_mode_item = weechat.bar_item_new("battlearena_battle_mode", "cb_battle_mode_item", "")
      player_turn_item = weechat.bar_item_new("battlearena_player_turn", "cb_player_turn_item", "")
      health_item = weechat.bar_item_new("battlearena_health_status", "cb_health_status_item", "")
      status_effects_item = weechat.bar_item_new("battlearena_status_effects", "cb_status_effects_item", "")
      active_skills_item = weechat.bar_item_new("battlearena_active_skills", "cb_active_skills_item", "")
    weechat.hook_command("battlearena", "BattleArena client script with autobattle functions.",
        "[shop [list [items|techs|skills|stats|weapons|styles|orbs|ignitions|portal|misc|gems|alchemy]|buy [items|techs|skills|stats [hp|tp|ig|str|def|int|spd]|weapons|styles|orbs|ignitions|portal|misc|gems|alchemy]]] | autobattle [start|end]",
        "description of arguments...",
        "items|skills|weapons|styles|orbs|ignitions|portal|misc|gems|alchemy list|buy"
        " || stats buy|list hp|tp|ig|str|def|int|spd"
        " || styles buy|list|change TRICKSTER|WEAPONMASTER|GUARDIAN|SPELLMASTER|DOPPELGANGER|HITENMITSURUGI-RYU|QUICKSILVER"
        " || techs list|buy %(plugin_available_techs)"
        " || use %(plugin_known_techs) %(plugin_enemies)|%(plugin_players)"
        " || setup bot "
        " || autobattle orbtrain|start|stop|tracking",
        "cb_command", "")

## TODO LIST
#
# - Add bar items for:
#   - (Last reported) Level
#   - Shop level
#   - HP
#   - TP
#   - IG
#   - (Passive / Available) Skills
#   - Owned Weapons
#   - Techs
#   - Alive enemies
#   - Players
#   - Accessory
#   - Keys
#   - Battle Status
#
# - Fix bar items for active skills and status effects so they don't show if there are none.
#
# - Parse "The following players have absorbed a black orb from the boss: Raiden, FiXato"
# - Skip techs when cursed
# - Warn when you have a key for a chest on the battle arena.
#   - FiXato has the following keys: BrownKey(2), RedKey(1), GreenKey(1), GoldKey(1), PurpleKey(2)
# - Keep track of received and used items
# - Keep track of shop level and auto-use UltraDiscountCard when above 25 (Or above 26 if you have a VIP-Membercard)
# - Update the command description and tab completion.
# - Add support for skills
# - Add support for styles
# - Make use of enemy info details such as:
#   - "Water Elemental is a glowing orb of water magic. It seems resistant to melee."
#   - "Volcano Wasp uses all of her health to perform this technique!" (Should move the enemy to dead_enemies)
# - Capture the output of !shop list weapons and sort the weapons list by cost.