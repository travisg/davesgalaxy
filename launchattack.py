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
  parser.add_option("-n", "--noupgrade", dest="doupgrade",
                    action="store_false", default=True, help="dry run")
  parser.add_option("-f", "--fleet", dest="fleet",
                    action="store", type="string", help="fleet type")
  parser.add_option("-m", "--maxfleet", dest="maxfleet",
                    action="store", type="int", help="max fleets")

  parser.add_option("-d", "--dest_route", dest="dest",
                    type="string", help="destination route")

  (options, args) = parser.parse_args()

  if options.fleet == None or options.dest == None or options.maxfleet == None:
    print "not enough arguments"
    parser.print_help()
    sys.exit(1)

  print "options " + str(options)

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  g.load_routes()
  try:
    dest_route = g.find_route(options.dest)
  except:
    print "could't find dest route"
    sys.exit(1)

  LaunchAttack(g, options.doupgrade, options.fleet, options.maxfleet, dest_route)

def LaunchAttack(g, doupgrade, fleetstring, num, dest_route):
  f = game.ParseFleet(fleetstring)
  print f

  dest_shape = shape.Polygon(*(dest_route.points))

  # find a list of potential fleet builders
  print "looking for fleet builders..."
  total_fleets = 0
  fleet_builders = []
  for p in g.planets:
    p.load()
    count = p.how_many_can_build(f)
    if count > 0:
      print "planet " + str(p) + " can build " + str(count) + " fleets"
      p.distance_to_target = dest_shape.distance(p.location)
      fleet_builders.append(p)
      total_fleets += count

  # sort fleet builders by distance to target
  fleet_builders = sorted(fleet_builders, key=lambda planet: planet.distance_to_target)

  print "found " + str(len(fleet_builders)) + " fleet building planets capable of building " + str(total_fleets) + " fleets"

  g.load_fleet_cache()
  built = 0
  print "building assault fleets"
  done = False
  for p in fleet_builders:
    if done:
      break

    count = p.how_many_can_build(f);
    print "planet " + str(p) + " can build " + str(count) + " fleets"

    while not done and count > 0 and p.can_build(f):
      print "looking to build from " + str(p) + "  distance: " + str(p.distance_to_target)
      if doupgrade:
        fleet = p.build_fleet(f)
        if fleet:
          print "moving fleet to new route"
          if fleet.move_to_route(dest_route) == False:
            print "error moving fleet"
        else:
          print " failed to build fleet"
          count = 0
          break

      built += 1
      count -= 1
      if built >= num:
        done = True

  if built > 0:
    if doupgrade:
      print "built %d fleets" % built
    else:
      print "would have built %d fleets" % built

  g.write_planet_cache()
  g.write_fleet_cache()

if __name__ == "__main__":
    main()
