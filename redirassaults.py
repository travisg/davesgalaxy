#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

import game
from optparse import OptionParser
import sys
import shape
import re

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

  RedirAssaults(g, options.doupgrade)

def RedirAssaults(g, doupgrade):

  g.load_fleet_cache()
  g.load_planet_cache()
  g.load_routes()

  # make a list of assault routes
  assaultroutesowned = []
  assaultroutesnotowned = []
  for r in g.routes.keys():
    route = g.routes[r]
    assaultmatch = re.search(r'\Aassault([0-9]+)', route.name)
    if assaultmatch == None:
      continue

    #print "assault route %s" % route

    # get the planet id from the route name
    num = int(assaultmatch.group(1))
    route.assaultplanetid = num

    # see if it's one of our planets
    p = g.get_planet(num)

    if p:
      route.assaultplanet = p
      assaultroutesowned.append(route)
    else:
      assaultroutesnotowned.append(route)

  # special case: routes called 'toassault' will be considered as owned fleet routes
  for r in g.routes.keys():
    route = g.routes[r]

    if route.name == "toassault":
      route.assaultplanetid = 0
      assaultroutesowned.append(route)

  # special case: routes called 'assaultme' will be considered as unowned fleet routes
  for r in g.routes.keys():
    route = g.routes[r]

    if route.name == "assaultme":
      route.assaultplanetid = 0
      assaultroutesnotowned.append(route)

#  print "routes around owned planets:"
#  print assaultroutesowned
#  print "routes around unowned planets:"
#  print assaultroutesnotowned

  for route in assaultroutesnotowned:
    route.fleetcount = 0

  # go through the list of fleets orbiting planets we own and find a new place to redir them to
  for route in assaultroutesowned:
    for f in g.fleets:
      f.load()
      if f.routeid == route.routeid:
        print "fleet %s on assault route %s assaulting planet %d" % (f, route, route.assaultplanetid)
        #print route.points

        # we have a fleet orbiting a planet that is owned, find a nearby one to assault
        targets = sorted(assaultroutesnotowned, key=lambda route: game.distance_between(route.points[0], f.coords))
        #print targets

        # try to find a nearby target route, but not pile entirely on one
        # algorithm: pick the closest, least used target route from the list
        # of target routes within 20 units of distance of the nearest one
        mindistance = game.distance_between(targets[0].points[0], f.coords)

        minfleets = -1
        for t in targets:
          distance = game.distance_between(t.points[0], f.coords)
          if distance - mindistance < 20:
            if minfleets < 0 or t.fleetcount < minfleets:
              minfleets = t.fleetcount

        foundtarget = targets[0]
        for t in targets:
          distance = game.distance_between(t.points[0], f.coords)
          #print "%s %d %d %d" % (t, t.fleetcount, distance, mindistance)
          if distance - mindistance < 20:
            if t.fleetcount == minfleets:
              foundtarget = t
              break

        targetroute = foundtarget
        print "nearest route around planet under assault at %s" % targetroute

        targetroute.fleetcount += 1

        if doupgrade:
          print "moving fleet to new route"
          f.move_to_route(targetroute)

  g.write_planet_cache()
  g.write_fleet_cache()

if __name__ == "__main__":
    main()
