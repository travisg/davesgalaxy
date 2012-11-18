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

  (options, args) = parser.parse_args()

  print "options " + str(options)

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  g.load_fleet_cache()

  g.load_routes()
  for r in g.routes.keys():
    route = g.routes[r]

    used = False
    for f in g.fleets:
      f.load()

      if f.routeid == r:
        used = True
        break

    if not used and route.name.find("assault") == 0:
      print "route %s is unused" % route.name
      if options.doupgrade:
        print "removing"
        route.delete()

  g.write_fleet_cache()

if __name__ == "__main__":
    main()
