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
  parser.add_option("-m", "--maxarcs", dest="maxarcs",
                    action="store", type="int", default=-1, help="maximum arcs to build")
  parser.add_option("-p", "--perplanet", dest="perplanet",
                    action="store", type="int", default=-1, help="max arcs per planet")
  parser.add_option("-l", "--leave", dest="leave",
                    action="store", type="int", default=0, help="min of arcs to leave on planet")
  parser.add_option("-e", "--escort", dest="escort",
                    action="store", type="string", help="escort fleet")

  parser.add_option("-x", "--sx", dest="sx",
                    action="store", type="float", help="source x coordinate")
  parser.add_option("-y", "--sy", dest="sy",
                    action="store", type="float", help="source y coordinate")
  parser.add_option("-r", "--sr", dest="sr",
                    action="store", type="float", default=20.0, help="builder radius to consider")

  parser.add_option("-X", "--tx", dest="tx",
                    action="store", type="float", help="target x coordinate")
  parser.add_option("-Y", "--ty", dest="ty",
                    action="store", type="float", help="target y coordinate")
  parser.add_option("-R", "--tr", dest="tr",
                    action="store", type="float", help="target radius to consider")

  parser.add_option("-s", "--source_route", dest="source",
                    action="append", type="string", help="route(s) enclosing source")
  parser.add_option("-S", "--sink_route", dest="sink",
                    action="append", type="string", help="route(s) enclosing sink")

  (options, args) = parser.parse_args()

  if (options.sx == None or options.sy == None) and options.source == None:
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

  # compute the source shape(s) passed in from the command line
  source_shapes = []
  if options.source != None:
    for source in options.source:
      print "adding source route %s" % source
      route = g.find_route(source)
      if route == None:
        print "source route %s not found" % source
        sys.exit(1)
      s = shape.Polygon(*(route.points))
      s.name = source
      source_shapes.append(s)
  elif options.sx != None and options.sy != None and options.sr != None:
    print "adding source circle"
    source_shapes.append(shape.Circle([options.sx, options.sy], options.sr))

  # compute the sink shape(s) passed in from the command line
  sink_shapes = []
  if options.sink != None:
    for sink in options.sink:
      print "adding sink route %s" % sink
      route = g.find_route(sink)
      if route == None:
        print "sink route %s not found" % sink
        sys.exit(1)
      s = shape.Polygon(*(route.points))
      s.name = sink
      sink_shapes.append(s)
  elif options.tx != None and options.ty != None and options.tr != None:
    print "adding sink circle"
    sink_shapes.append(shape.Circle([options.tx, options.ty], options.tr))

  # check to see if they passed in any source shapes
  if len(source_shapes) == 0:
    print "no source shapes or coordinates found"
    parser.print_help()
    sys.exit(1)

  # if they didn't pass any sink shapes or coordinates, copy from source
  if len(sink_shapes) == 0:
    sink_shapes = source_shapes

  BuildArcs(g, options.doupgrade, options.maxarcs,
            options.perplanet, options.leave,
            source_shapes, sink_shapes, options.escort)

def uniqify(seq, idfun=None):
   # f5 from http://www.peterbe.com/plog/uniqifiers-benchmark
   # order preserving
   if idfun is None:
       def idfun(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = idfun(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result

def BuildArcs(g, doupgrade, maxarcs, perplanet, leave, sources, sinks, escort):

  escortfleet = game.ParseFleet(escort)
  print escortfleet

  # construct fleet we want to build
  arc = { 'arcs': 1 }
  arc.update(escortfleet)

  # find a list of potential arc builders
  print "looking for arc builders..."
  total_arcs = 0
  arc_builders = []
  for p in g.planets:
    for s in sources:
      if s.inside(p.location):
        p.load()
        count = p.how_many_can_build(arc)
        if count > 0 and ((p.society > 40 and p.population > 1000000) or p.population > 5000000):
          print "planet " + str(p) + " can build " + str(count) + " arcs"

          arc_builders.append(p)
          total_arcs += count

  print "found " + str(len(arc_builders)) + " arc building planets capable of building " + str(total_arcs) + " arcs"

  # load the sectors around the target point
  unowned_targets = []
  for s in sinks:
    print "looking for unowned planets at target shape %s..." % s.name
    t = game.FindUnownedPlanetsInShape(g, s)
    print "\tfound %d targets" % len(t)
    unowned_targets.extend(t)

  # remove duplicates
  print "found %d unowned planets total" % len(unowned_targets)
  print "removing duplicates..."
  unowned_targets = uniqify(unowned_targets, idfun=lambda p: p.planetid)
  print "\tnow have %d unowned planets" % len(unowned_targets)

  # trim the list of targets to ones that dont have an arc already incoming
  print "trimming list of unowned planets..."
  unowned_targets = game.TrimColonyTargettedPlanets(g, unowned_targets)
  print "\tnow have %d unowned planets" % len(unowned_targets)

  # build arcs
  built = 0
  if len(unowned_targets) > 0:
    print "building arcs..."

    # sort the shortest distances for each arc builder to all the targets
    for p in arc_builders:
      p.targets = sorted(unowned_targets, key=lambda planet: game.distance_between(planet.location, p.location))
      p.arcs_can_build = p.how_many_can_build(arc) # delete later
      p.arcs_built = 0

    # iterate through the list, building the shortest builder -> target path until out of arcs or one of the passed in terminating conditions
    while len(arc_builders) > 0 and len(unowned_targets) > 0:
      print "%d builders and %d targets remain" % (len(arc_builders), len(unowned_targets))

      # sort all of the arc builders by the shortest closest target
      arc_builders = sorted(arc_builders, key=lambda planet: game.distance_between(planet.location, planet.targets[0].location))

      p = arc_builders[0]
      t = p.targets[0]

      count = p.arcs_can_build

      # trim the number we can build by the min left limit
      count -= leave
      if count <= 0 or (perplanet > 0 and p.arcs_built >= perplanet):
        arc_builders.remove(p)
        continue

      #print "planet " + str(p) + " can build " + str(count) + " arcs"
      print "looking to build from " + str(p) + " to " + str(t) + " distance: " + str(game.distance_between(p.location, t.location))
      if doupgrade:
        fleet = p.build_fleet(arc)
        if fleet:
          fleet.move_to_planet(t)
        else:
          print " failed to build fleet"
          p.arcs_can_build = 0
          continue

      unowned_targets.remove(t)
      built += 1
      p.arcs_can_build -= 1
      p.arcs_built += 1

      # cull this target from the list
      for p in arc_builders:
        p.targets.remove(t)

      if maxarcs > 0 and built >= maxarcs:
        break

    # make sure we dont leave any extra metadata on the planets
    for p in arc_builders:
      del p.arcs_built
      del p.arcs_can_build
      del p.targets

  if built > 0:
    if doupgrade:
      print "built %d arc fleets" % built
    else:
      print "would have built %d arc fleets" % built

  g.write_planet_cache()
  g.write_fleet_cache()

if __name__ == "__main__":
    main()
