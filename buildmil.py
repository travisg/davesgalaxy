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
  parser.add_option("-l", "--leave", dest="leave",
                    action="store", type="int", default=0, help="min of ships to leave on planet")
  parser.add_option("-m", "--minfleet", dest="minfleet",
                    action="store", type="int", default=10, help="minimum sized fleet to build")
  parser.add_option("-t", "--type", dest="type",
                    type="string", default="cruisers", help="type of ship to build")

  parser.add_option("-s", "--source_route", dest="source",
                    type="string", help="route enclosing source")
  parser.add_option("-d", "--dest_route", dest="dest",
                    type="string", help="destination route")

  (options, args) = parser.parse_args()

  if options.source == None or options.dest == None:
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
    if dest_route == None:
      raise Exception
  except:
    print "could't find dest route"
    sys.exit(1)

  try:
    source_route = g.find_route(options.source)
    source_shape = shape.Polygon(*(source_route.points))
  except:
    print "could't find source route"
    sys.exit(1)

  print source_shape

  Assault(g, options.doupgrade, options.minfleet, options.type, options.leave, source_shape, dest_route)


def Assault(g, doupgrade, minfleet, fleettype, leavecount, source, dest):
  built = 0

  # find a list of potential fleet builders
  print "looking for fleet builders..."
  total_fleets = 0
  fleet_builders = []
  for p in g.planets:
    if source.inside(p.location):
      p.load()
      count = p.how_many_can_build({fleettype: 1})
      count -= leavecount
      if count > minfleet:
        print "planet " + str(p) + " can build " + str(count) + " ships"
        fleet_builders.append(p)
        total_fleets += count

  print "found " + str(len(fleet_builders)) + " fleet building planets capable of building " + str(total_fleets) + " ships"

  g.load_fleet_cache()
  build = 0
  if count > 0:
    print "building assault fleets"
    for p in fleet_builders:

      count = p.how_many_can_build({fleettype: 1})
      count -= leavecount

      print "planet " + str(p) + " can build " + str(count) + " ships"
      f = {fleettype: count}
      if doupgrade:
        fleet = p.build_fleet(f)
        if fleet:
          fleet.move_to_route(dest)
        else:
          print " failed to build fleet"
          count = 0
          break

      # cull this target from the list
      built += 1

  if built > 0:
    if doupgrade:
      print "built %d fleets" % built
    else:
      print "would have built %d fleets" % built

  g.write_planet_cache()
  g.write_fleet_cache()

if __name__ == "__main__":
    main()
