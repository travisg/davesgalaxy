#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

import game
from optparse import OptionParser
import sys

parser = OptionParser()
parser.add_option("-U", "--username", dest="username",
                  help="username of login")
parser.add_option("-P", "--password", dest="password",
                  help="password for login")
(options, args) = parser.parse_args()

g=game.Galaxy()
if options.username and options.password:
  # explicit login
  g.login(options.username, options.password, force=True)
else:
  # try to pick up stored credentials
  g.login()

print "loading planets..."
count = 0
for p in g.planets:
  if p.load():
    count += 1
    if (count % 100) == 0:
      print "refreshed " + str(count) + " planets"
      g.write_planet_cache()

if count > 0:
  g.write_planet_cache()
print "loaded " + str(len(g.planets)) + " planets"

print "loading fleets..."
count = 0
for f in g.fleets:
  if f.load():
    count += 1
    if (count % 100) == 0:
      print "refreshed " + str(count) + " fleets"
      g.write_fleet_cache()

if count > 0:
  g.write_fleet_cache()
print "loaded " + str(len(g.fleets)) + " fleets"
