#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

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
  parser.add_option("-n", "--noupgrade", dest="doupgrade",
                    action="store_false", default=True, help="dry run")
  parser.add_option("-o", "--old", dest="old",
                    help="minimum society level to create bulk fleet",
                    default=80,
                    type="int")
  parser.add_option("-b", "--bulks", dest="bulks",
                    type="int", default = 40,
                    help="maximum number of bulkfrieghters per planet")
  (options, args) = parser.parse_args()

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()
    
  buildbulkfreighters(g, options.doupgrade, options.old, options.bulks)
  g.write_planet_cache()
  g.write_fleet_cache()

def buildbulkfreighters(g, doupgrade, old, limit_in):
  """Build bulkfreighters at advanced planets and deploy them nearby."""
  merchant = {'bulkfreighters': 1}
  for planet in g.planets:
    limit = limit_in
    planet.load()
    if planet.society > old:
      already_has = 0
      for f in g.fleets:
        f.load()
        if f.home == planet and 'bulkfreighters' in f.ships:
          already_has += 1
      limit -= already_has
    
      built = 0
      neighbors = None
      neighbors = g.my_planets_near(planet)
      if limit > 0:
        print "building no more than %d bulkfrighters at %s" % (limit,
                                                                planet.name)
      else:
        print "already %d bulkfrighters at %s" % (already_has, planet.name)
      if doupgrade:
        done = False
        while not done and planet.can_build(merchant) and built < limit:
          fleet = planet.build_fleet(merchant,
                                     interactive=False,
                                     skip_check=True)
          if fleet:
            sink = neighbors.pop(0)['planet']
            print "  moving %d to %s" % (fleet.fleetid, sink.name)
            fleet.move_to_planet(sink)
            built += 1
          else:
            print "  build failed."
            done = True
        if built > 0:
          print "built %d bulkfreighters at %s for %d total" % (
            built, planet.name, built + already_has)

if __name__ == "__main__":
    main()
