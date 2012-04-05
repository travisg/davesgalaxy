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
  parser.add_option("-l", "--limit", dest="limit",
                    type="int", default = 10000,
                    help="maximum number of fleets to build")
  (options, args) = parser.parse_args()
  planetid = args[0]

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  try:
    planet = game.Planet(g, int(planetid))
  except ValueError:
    planet = g.find_planet(planetid)
    print "using planet %d with name %s" % (planet.planetid, planet.name)
    
  buildbuildbulkfreighters(g, planet, options.limit)

#TODO abstract out this pattern: build and deploy nearby
def buildbuildbulkfreighters(g, planet, limit):
  """Build bulkfreighters at a planet and deploy them nearby."""
  merchant = {'bulkfreighters': 1}
  planet.load()

  built = 0
  neighbors = None
  neighbors = g.my_planets_near(planet)
  print "building no more than %d bulkfrighters at %s" % (limit, planet.name)
  while planet.can_build(merchant) and len(neighbors) > 0 and built < limit:
    try:
      fleet = planet.build_fleet(merchant,
                                 interactive=False,
                                 skip_check=True)
      sink = neighbors.pop(0)['planet']
      print "  moving %d to %s" % (fleet.fleetid, sink.name)
      fleet.move_to_planet(sink)
      built += 1
    except:
      # something blew up, move on
      neighbors = []

  print "built %d bulkfreighters at %s" % (built, planet.name)


if __name__ == "__main__":
    main()
