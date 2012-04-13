#!/usr/bin/env python

import game
from optparse import OptionParser
import sys

def main():
  parser = OptionParser()
  parser.add_option("-U", "--username", dest="username",
                    help="username of login")
  parser.add_option("-P", "--password", dest="password",
                    help="password for login")
  parser.add_option("-q", "--quick",
                    action="store_true", dest="quick", default=False,
                    help="only issue the build request, without sanity checks.")
  parser.add_option("-A", "--all",
                    action="store_true", dest="all", default=False,
                    help="use manifest as template of largest possible fleet.")
  parser.add_option("-i", "--interactive",
                    action="store_true", dest="interactive", default=False,
                    help="catch reply and send to the browser.")
  (options, args) = parser.parse_args()
  
  planetid = args[0]
  tobuild = args[1:]
  
  g = game.Galaxy()
  
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()
  
  manifest = {}
  for pr in tobuild:
    ship, qty = pr.split("=")
    if ship in game.ALL_SHIPS.keys():
      if ship in manifest:
        manifest[ship] += int(qty)
      else:
        manifest[ship] = int(qty)
    else:
      print "error: unknown ship type: " + ship
      sys.exit(1)
  
  try:
    planet = game.Planet(g, int(planetid), 'unknown', [])
  except ValueError:
    planet = g.find_planet(planetid)
    print "using planet %d with name %s" % (planet.planetid, planet.name)
    
  if not planet:
    print "error: unknown planet: " + planetid
    sys.exit(1)
  
  fleet = buildfleet(g, planet, manifest, 
                     quick=options.quick,
                     all=options.all,
                     interactive=options.interactive)
  if fleet:
    print fleet.fleetid
  else:
    print "build failed"

def buildfleet(g, planet, manifest,
               quick=False, all=False, interactive=False):
  """Build a fleet at the planet.
  quick: don't check for resources
  all: use manifest as a template to build as large a fleet as possible.
  interactive: launch interactive routing UI in browser.
  """
  fleet = None
  if quick or planet.can_build(manifest):
    if all:
      proportions = manifest.copy()
      while planet.can_build(manifest):
        for key in manifest.keys():
          manifest[key] += proportions[key]
      for key in manifest.keys():
        manifest[key] -= proportions[key]
    fleet = planet.build_fleet(manifest,
                               interactive=interactive,
                               skip_check=True)
    sys.stderr.write("built %s\n" % str(manifest))
  else:
    sys.stderr.write("error: planet cannot afford that fleet.\n")
  return fleet


if __name__ == "__main__":
  main()
