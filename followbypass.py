#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

from optparse import OptionParser
import sys
import types

import game
import shape

def main():
  parser = OptionParser()
  parser.add_option("-U", "--username", dest="username",
                    help="username of login")
  parser.add_option("-P", "--password", dest="password",
                    help="password for login")

  (options, args) = parser.parse_args()
  route_name = args[0]

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()
    
  route = g.find_route(route_name)
  for fleet in  g.fleets:
    fleet.load()
    FollowBypass(g, fleet, route)

  g.write_planet_cache()
  g.write_fleet_cache()


def FollowBypass(g, fleet, route):
  try:
    p = shape.Polygon(*(route.points))
    if fleet.disposition == 'Colonize':
      if type(fleet.destination) == types.InstanceType:
        planetid = fleet.destination.planetid
      elif type(fleet.destination) == types.ListType:
        return
      else:
        planetid = int(fleet.destination.split('-')[-1])
      d = game.Planet(g, planetid)
      d.load()
      ramp = (shape.distance(fleet.coords, p.nearest_to(fleet.coords)) +
              shape.distance(p.nearest_to(d.location), d.location))
      travel = shape.distance(p.nearest_to(fleet.coords), p.nearest_to(d.location))
      if travel > (2 * ramp):
        plan=[p.nearest_to(fleet.coords),
              p.nearest_to(d.location),
              d.location]
        print "re-routing %d" % fleet.fleetid
        fleet.route_to(plan, d.planetid)
  except ValueError:
    pass

if __name__ == "__main__":
    main()
