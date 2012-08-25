#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

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
  parser.add_option("-b", "--military", dest="military",
                    action="store_true", default=False, help="build military base")
  parser.add_option("-m", "--mindcontrol", dest="mindcontrol",
                    action="store_true", default=False, help="build mind control")
  parser.add_option("-d", "--defense", dest="defense",
                    action="store_true", default=False, help="build planetary defense")
  parser.add_option("-t", "--tax", dest="tax", type="float",
                    action="store", help="set tax rate")
  (options, args) = parser.parse_args()

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  BuildUpgrades(g, options.doupgrade, options.mindcontrol, options.defense, options.military, options.tax)
  g.write_planet_cache()

def BuildUpgrade(p, doupgrade, upgrade):
  total = 0
  if doupgrade:
    if p.start_upgrade(upgrade):
      print "\tbuilt %s at %s." % (upgrade, p.name)
      total += 1
    else:
      print "\tfailed to build %s at %s." % (upgrade, p.name)
  else:
    print "\twould have built %s at %s." % (upgrade, p.name)
  return total

def BuildUpgrades(g, doupgrade, domindcontrol, dodefense, domilitary, tax):
  has_pd = []
  total = 0

  for p in g.planets:
    p.load()
    print "looking at planet " + p.name
    # min upgrades assuming 7% tax
    if p.can_upgrade('Trade Incentives') and p.population >= 5000:
      total += BuildUpgrade(p, doupgrade, 'Trade Incentives')
    if p.society > 10 and p.can_upgrade('Long Range Sensors 1') and p.population >= 50000:
      total += BuildUpgrade(p, doupgrade, 'Long Range Sensors 1')
    if p.society > 20 and p.can_upgrade('Long Range Sensors 2') and p.population >= 150000:
      total += BuildUpgrade(p, doupgrade, 'Long Range Sensors 2')
    if p.society > 40 and p.can_upgrade('Matter Synth 1') and p.population >= 400000:
      total += BuildUpgrade(p, doupgrade, 'Matter Synth 1')
    if p.society > 50 and p.can_upgrade('Matter Synth 2') and p.population >= 900000:
      total += BuildUpgrade(p, doupgrade, 'Matter Synth 2')
    if p.society > 50 and p.can_upgrade('Slingshot') and p.population >= 1750000:
      total += BuildUpgrade(p, doupgrade, 'Slingshot')
    if p.society > 50 and p.can_upgrade('Petrochemical Power Plant') and p.population >= 5000000:
      total += BuildUpgrade(p, doupgrade, 'Petrochemical Power Plant')
    if domilitary and p.society > 50 and p.can_upgrade('Military Base') and p.population >= 5000000:
      total += BuildUpgrade(p, doupgrade, 'Military Base')
    if dodefense and p.can_upgrade('Planetary Defense 1') and p.population >= 5000000:
      total += BuildUpgrade(p, doupgrade, 'Planetary Defense 1')
    if domindcontrol and p.can_upgrade('Mind Control'):
      if p.society < 90 and p.society > 70:
        total += BuildUpgrade(p, doupgrade, 'Mind Control')

    if tax != None:
      if p.tax < float(tax):
        print "\tsetting tax rate to " + str(tax)
        p.set_tax(tax)

  print "started %d upgrades" % total

if __name__ == "__main__":
    main()
