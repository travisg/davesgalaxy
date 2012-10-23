#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

import game
from optparse import OptionParser
import sys
import shape
import random

def main():
  parser = OptionParser()
  parser.add_option("-U", "--username", dest="username",
                    help="username of login")
  parser.add_option("-P", "--password", dest="password",
                    help="password for login")
  parser.add_option("-n", "--noupgrade", dest="doupgrade",
                    action="store_false", default=True, help="dry run")
  parser.add_option("-f", "--fleet", dest="fleet",
                    action="store", type="string", help="fleet composition")

  parser.add_option("-m", "--maxdistance", dest="maxdistance",
                    action="store", type="float", default=-1.0, help="max distance")
  parser.add_option("-i", "--mindistance", dest="mindistance",
                    action="store", type="float", default=-1.0, help="min distance")
  parser.add_option("-z", "--size", dest="size",
                    action="store", type="float", default=5.0, help="size of sector box to scan for empty")

  parser.add_option("-x", "--sx", dest="sx",
                    action="store", type="float", help="source x coordinate")
  parser.add_option("-y", "--sy", dest="sy",
                    action="store", type="float", help="source y coordinate")
  parser.add_option("-r", "--sr", dest="sr",
                    action="store", type="float", default=20.0, help="builder radius to consider")

  parser.add_option("-s", "--source_route", dest="source",
                    type="string", help="route enclosing source")

  (options, args) = parser.parse_args()

  if ((options.sx == None or options.sy == None) and options.source == None) or options.fleet == None:
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

  source_shape = None
  if options.source != None:
    source_route = g.find_route(options.source)
    source_shape = shape.Polygon(*(source_route.points))
  else:
    source_shape = shape.Circle([options.tx, options.ty], options.tr)

  SeedArcs(g, options.doupgrade, 
            source_shape, options.fleet, 
            options.mindistance, options.maxdistance, options.size)

def SeedArcs(g, doupgrade, source, fleetstr, mindistance, maxdistance, size):

  fleet = game.ParseFleet(fleetstr)
  print fleet

  # find a list of potential builders
  print "looking for builders..."
  total = 0
  builders = []
  for p in g.planets:
    if source.inside(p.location):
      p.load()
      count = p.how_many_can_build(fleet)
      if count > 0:
        print "planet " + str(p) + " can build " + str(count) + " fleets"
        builders.append(p)
        total += count

  print "found " + str(len(builders)) + " building planets capable of building " + str(total) + " fleets"

  for p in builders:
    print p

    done = False
    while not done:
      # pick a random spot approximately near the starting location
      x = random.uniform(p.location[0] - maxdistance, p.location[0] + maxdistance)
      y = random.uniform(p.location[1] - maxdistance, p.location[1] + maxdistance)

      distance = game.distance_between((x,y),p.location)
      if maxdistance > 0 and distance > maxdistance:
        continue
      if mindistance > 0 and distance < mindistance:
        continue
  
      #print x
      #print y

      #print "distance %f" % distance

      sect = g.load_sectors(((x-size,y-size),(x+size,y+size)))
      #print sect

      # make sure the sector is uninhabited
      if len(sect["planets"]["owned"]) > 0 or len(sect["planets"]["unowned"]) == 0:
        continue

      # trim sparse sectors
      numplanets = len(sect["planets"]["unowned"])
      if numplanets < 5:
        continue

      print "found a potential sect with %d planets at around %f %f" % (numplanets, x, y)
      done = True

      # pick a target
      target = sect["planets"]["unowned"][random.randrange(numplanets - 1)]
      print "target planet %s, distance %f" % (str(target), game.distance_between(p.location, target.location))

      if doupgrade:
        f = p.build_fleet(fleet)
        if f:
          f.move_to_planet(target)
        else:
          print " failed to build fleet"
          continue

  g.write_planet_cache()
  g.write_fleet_cache()

if __name__ == "__main__":
    main()
