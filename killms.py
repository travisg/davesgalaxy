#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

# needed to kill a few upgrades i had accidentally started too early

import game
from optparse import OptionParser
import sys

def main():
  parser = OptionParser()
  parser.add_option("-U", "--username", dest="username",
                    help="username of login")
  parser.add_option("-P", "--password", dest="password",
                    help="password for login")
  parser.add_option("-n", "--noupgrade", dest="doupgrade",
                    action="store_false", default=True, help="dry run")
  (options, args) = parser.parse_args()
  
  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  KillUpgrades(g, options.doupgrade)

def KillUpgrades(g, doupgrade):
  for p in g.planets:
    p.load()
    print "looking at planet " + p.name

    if p.building_upgrade_zeropercent('Matter Synth 1'):
      print "is building MS1"
      if doupgrade:
        p.scrap_upgrade('Matter Synth 1')
    if p.building_upgrade_zeropercent('Matter Synth 2'):
      print "is building MS2"
      if doupgrade:
        p.scrap_upgrade('Matter Synth 2')

if __name__ == "__main__":
    main()
