#!/usr/bin/env python
# vim: set ts=2 sw=2 expandtab:

import game
from optparse import OptionParser
import sys
from operator import itemgetter, attrgetter

def main():
  usage = "usage: %prog [options] <ship types>"
  parser = OptionParser(usage=usage)
  parser.add_option("-U", "--username", dest="username",
                    help="username of login")
  parser.add_option("-P", "--password", dest="password",
                    help="password for login")
  parser.add_option("-m", "--minimum", dest="min", type="int", default=0,
                    help="minimum ships the planet has to be able to build")

  (options, args) = parser.parse_args()

  if len(args) == 0:
    print "not enough options"
    parser.print_usage()
    sys.exit(1)

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  shiptypes = { 'superbattleships', 
    'bulkfreighters', 
    'subspacers', 
    'arcs', 
    'blackbirds', 
    'merchantmen', 
    'scouts', 
    'battleships',
    'destroyers',
    'frigates',
    'cruisers'
  };

  buildlist = []

  didload = False
  for p in g.planets:
    if p.load(): didload = True
    for s in args:
      if s in shiptypes:
        count = p.how_many_can_build({ s : 1 })
        if count > options.min:
          buildlist.append((p, count))

  buildlist = sorted(buildlist, key=itemgetter(1), reverse=True) 

  for b in buildlist:
    print "Planet " + str(b[0]) + " can build " + str(b[1]) + " " + s

if __name__ == "__main__":
    main()
