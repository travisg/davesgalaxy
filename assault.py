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
  parser.add_option("-m", "--minfleet", dest="minfleet",
                    action="store", type="int", default=10, help="minimum sized fleet to build")

  parser.add_option("-o", "--owner", dest="owner",
                    type="string", help="owner to assault")
  parser.add_option("-s", "--source_route", dest="source",
                    type="string", help="route enclosing source")
  parser.add_option("-S", "--sink_route", dest="sink",
                    type="string", help="route enclosing sink")

  (options, args) = parser.parse_args()

  if options.source == None or options.sink == None or options.owner == None:
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
    sink_route = g.find_route(options.sink)
    sink_shape = shape.Polygon(*(sink_route.points))
  except:
    print "could't find sink route"
    sys.exit(1)

  try:
    source_route = g.find_route(options.source)
    source_shape = shape.Polygon(*(source_route.points))
  except:
    print "could't find source route"
    sys.exit(1)

  print source_shape
  print sink_shape

  Assault(g, options.doupgrade, options.minfleet, source_shape, sink_shape, options.owner)


def Assault(g, doupgrade, minfleet, source, sink, owner):
  built = 0

  # find a list of potential fleet builders
  print "looking for fleet builders..."
  total_fleets = 0
  fleet_builders = []
  for p in g.planets:
    if source.inside(p.location):
      p.load()
      count = p.how_many_can_build({'frigates': minfleet})
      if count > 0:
        print "planet " + str(p) + " can build " + str(count) + " fleets"
        p.distance_to_target = sink.distance(p.location)
        fleet_builders.append(p)
        total_fleets += count

  # sort fleet builders by distance to target
  fleet_builders = sorted(fleet_builders, key=lambda planet: planet.distance_to_target)

  print "found " + str(len(fleet_builders)) + " fleet building planets capable of building " + str(total_fleets) + " fleets"

  # load the sectors around the target point
  print "looking for owned planets at target location..."
  sect = g.load_sectors(sink.bounding_box())
  #print sect
  targets = []
  for p in sect["planets"]["owned"]:
    #print p
    if p.owner == owner:
      targets.append(p)

  print "found " + str(len(targets)) + " target planets"

  g.load_fleet_cache()
  build = 0
  if len(targets) > 0:
    print "building assault fleets"
    f = { 'frigates': minfleet }
    done = False
    for p in fleet_builders:
      if done:
        break

      # for this builder, find the closest unowned planets
      for t in targets:
        t.distance_to_target = game.distance_between(p.location, t.location)
      targets = sorted(targets, key=lambda planet: planet.distance_to_target)

      count = p.how_many_can_build(f);

      print "planet " + str(p) + " can build " + str(count) + " fleets"
      while not done and count > 0 and p.can_build(f):
        t = targets[0]
        print "looking to build to " + str(t) + " distance: " + str(t.distance_to_target)
        if doupgrade:
          fleet = p.build_fleet(f)
          if fleet:
            fleet.move_to_planet(t)
          else:
            print " failed to build fleet"
            count = 0
            break

        # cull this target from the list
        targets.remove(t)
        built += 1
        count -= 1
        if len(targets) == 0:
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
