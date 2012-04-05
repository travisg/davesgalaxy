#!/usr/bin/env python

import game
from optparse import OptionParser
import sys


def default_input(prompt, default):
  response = raw_input(prompt)
  if response == '':
    return default
  return response.lower()


def main():
  parser = OptionParser()
  parser.add_option("-U", "--username", dest="username",
                    help="username of login")
  parser.add_option("-P", "--password", dest="password",
                    help="password for login")
  parser.add_option("-s", "--skip_level", dest="skip_level",
                    help="maximum society level to initiate a skip arc",
                    default=20,
                    type="int")
  (options, args) = parser.parse_args()

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  buildmerchantmen(g, options.skip_level)

    
def buildmerchantmen(g, level):
  """Build merchants at new planets that could have built an arc but didn't"""
  merchant = {'merchantmen': 1}
  arc = {'arcs': 1}
  arc_cost = game.ship_cost(arc)

  print 'Looking for planets younger than %d to build merchantmen.' % level
  print 'Name, ID, Society, Money, Antimatter, Steel'
  for p in g.planets:
    if p.society < level and p.steel[0] > arc_cost['steel']:
      neighbors = None
      if p.can_build(merchant):
        neighbors = g.my_planets_near(p)
        print '"%s", %d, %d, %d, %d, %d' % (
          p.name, p.planetid, p.society, p.money, p.antimatter[0], p.steel[0]
        )
      while p.can_build(merchant) and len(neighbors) > 0:
        try:
          fleet = p.build_fleet(merchant,
                                interactive=False,
                                skip_check=True)
          sink = neighbors.pop(0)['planet']
          print "moving %d to %s" % (fleet.fleetid, sink.name)
          fleet.move_to_planet(sink)
        except:
          # something blew up, move on
          neighbors = []


if __name__ == "__main__":
    main()
