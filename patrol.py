#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

import game
from optparse import OptionParser
import sys
import shape

def main():
  parser = OptionParser()
  parser.add_option("-U", "--username", dest="username",
                    help="username of login")
  parser.add_option("-P", "--password", dest="password",
                    help="password for login")
  parser.add_option("-n", "--noop", dest="noop",
                    action="store_true", default=False, help="dry run")
  parser.add_option("-m", "--maximum", dest="maximum",
                    type="int", default=100, help="maximum manifest multiplier")
  parser.add_option("-r", "--patrol_route", dest="patrol",
                    type="string", help="route that the patrol should join")

  (options, args) = parser.parse_args()
  planetid = args[0]
  tobuild = args[1:]

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()
    
  patrol_route = g.find_route(options.patrol)

  source = None
  try:
    source = g.get_planet(int(planetid))
  except ValueError:
    source = g.find_planet(planetid)
  source.load()

  manifest = {}
  for pr in tobuild:
    ship, qty = pr.split("=")
    if ship in game.ALL_SHIPS.keys():
      if ship in manifest:
        manifest[ship] += float(qty)
      else:
        manifest[ship] = float(qty)
    else:
      print "error: unknown ship type: " + ship
      sys.exit(1)
  
  BuildPatrol(g, source, patrol_route, manifest, options.maximum, options.noop)

def BuildPatrol(g, source, route, manifest, maximum, noop=False):

  count = source.how_many_can_build(manifest)
  count = min(maximum, count)
  for key in manifest.keys():
    manifest[key] = int(count * manifest[key])
  print "planet " + str(source) + " can build " + str(manifest) + " ships"

  count = min(maximum, count)
  for key in manifest.keys():
    manifest[key] = int(count * manifest[key])
  print "planet " + str(source) + " will build " + str(manifest) + " ships"

  if not noop:
    fleet = source.build_fleet(manifest)
    if fleet:
      fleet.move_to_route(route)
      print " build fleed %d and dispatched to %s" % (fleet.fleetid, route.name)
    else:
      print " failed to build fleet"
      count = 0
          
  if count > 0:
    if not noop:
      print "built %s" % str(manifest)
    else:
      print "would have built %s" % str(manifest)

  g.write_planet_cache()
  g.write_fleet_cache()

if __name__ == "__main__":
    main()
