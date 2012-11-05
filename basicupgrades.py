#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

import game
from optparse import OptionParser
import sys
import random

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
  parser.add_option("--dp", "--defensepercent", dest="defensepercent",
                    action="store", default=30, type="int", help="ratio of defense to military bases")
  parser.add_option("-t", "--tax", dest="tax", type="float",
                    action="store", help="set tax rate")
  (options, args) = parser.parse_args()

  print options

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  BuildUpgrades(g, options.doupgrade, options.mindcontrol, options.defense, options.military, options.tax, options.defensepercent)
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

def BuildUpgrades(g, doupgrade, domindcontrol, dodefense, domilitary, tax, defensepercent=30):
  has_pd = []
  total = 0

  for p in g.planets:
    p.load()
    print "looking at planet " + p.name

    if tax != None:
      if p.tax < float(tax):
        print "\tsetting tax rate to " + str(tax)
        if doupgrade:
          p.set_tax(tax)

    # ratio to skew the upgrades based on what the actual tax rate is relative to 7%
    taxconstant = 7 / p.tax
    #print taxconstant

    # min upgrades assuming 7% tax

    #if p.can_upgrade('Antimatter Power Plant'):
    #  total += BuildUpgrade(p, doupgrade, 'Antimatter Power Plant')
    if p.can_upgrade('Trade Incentives') and p.population >= 5000 * taxconstant:
      total += BuildUpgrade(p, doupgrade, 'Trade Incentives')
    if p.society > 10 and p.can_upgrade('Long Range Sensors 1') and p.population >= 50000 * taxconstant:
      total += BuildUpgrade(p, doupgrade, 'Long Range Sensors 1')
    if p.society > 20 and p.can_upgrade('Long Range Sensors 2') and p.population >= 150000 * taxconstant:
      total += BuildUpgrade(p, doupgrade, 'Long Range Sensors 2')
    if p.society > 40 and p.can_upgrade('Matter Synth 1') and p.population >= 400000 * taxconstant:
      total += BuildUpgrade(p, doupgrade, 'Matter Synth 1')
    if p.society > 50 and p.can_upgrade('Matter Synth 2') and p.population >= 900000 * taxconstant:
      total += BuildUpgrade(p, doupgrade, 'Matter Synth 2')
    if p.society > 50 and p.can_upgrade('Slingshot') and p.population >= 1500000 * taxconstant:
      total += BuildUpgrade(p, doupgrade, 'Slingshot')
    if p.society > 50 and p.can_upgrade('Petrochemical Power Plant') and p.population >= 5000000 * taxconstant:
      total += BuildUpgrade(p, doupgrade, 'Petrochemical Power Plant')
    if domindcontrol and p.can_upgrade('Mind Control'):
      if p.society < 90 and p.society >= 75: # mind control at 80
        total += BuildUpgrade(p, doupgrade, 'Mind Control')

    # deal with military and defense
    # if both mil and defense are selected, try to randomly decide between the two
    if domilitary and dodefense:
      # try to distribute defense and military semi-randomly
      if p.society > 50 and p.population >= 5000000 * taxconstant:
        if p.can_upgrade('Military Base') and p.can_upgrade('Planetary Defense 1'):
          # this planet can either go military or defense
          print "planet %s can go either military or defense" % p

          # decide randomly
          # 30% (defensepercent) will go defense
          if random.randrange(0, 100) < defensepercent:
            total += BuildUpgrade(p, doupgrade, 'Planetary Defense 1')
          else:
            total += BuildUpgrade(p, doupgrade, 'Military Base')
        if p.has_upgrade('Military Base') and p.has_upgrade('Planetary Defense 1') and not p.has_upgrade('Regional Government'):
          print "WARNING: planet %s has both PD and MB, probably can't afford it" % str(p)

        # XXX special case, leave disabled
        #if p.has_upgrade('Planetary Defense 1') and not p.has_upgrade('Regional Government'):
          #print "planet %s should get PD reevaluated" % str(p)
          #if random.randrange(0, 100) >= int(defensepercent):
            #print "switching planet %s to base from defense" % str(p)
            #if doupgrade:
              #p.scrap_upgrade('Planetary Defense 1')
              #total += BuildUpgrade(p, doupgrade, 'Military Base')
    else:
      if domilitary and p.society > 50 and p.can_upgrade('Military Base') and p.population >= 5000000 * taxconstant:
        total += BuildUpgrade(p, doupgrade, 'Military Base')
      if dodefense and p.can_upgrade('Planetary Defense 1') and p.population >= 5000000 * taxconstant:
        total += BuildUpgrade(p, doupgrade, 'Planetary Defense 1')

  print "started %d upgrades" % total

if __name__ == "__main__":
    main()
