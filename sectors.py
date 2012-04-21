#!/usr/bin/python

import game
import re
from optparse import OptionParser
import sys

parser = OptionParser()
parser.add_option("-U", "--username", dest="username",
                  help="username of login")
parser.add_option("-P", "--password", dest="password",
                  help="password for login")
parser.add_option("-x", "--xcoord", dest="x", 
                  type="float", default = 1645.0,
                  help="center X coordinate")
parser.add_option("-y", "--ycoord", dest="y", 
                  type="float", default = 1470.4,
                  help="center Y coordinate")
parser.add_option("-b", "--bound", dest="bound", 
                  type="string", default = 'Core Worlds',
                  help="route to use as a bound")
(options, args) = parser.parse_args()

g = game.Galaxy()
if options.username and options.password:
  # explicit loginpython

  g.login(options.username, options.password, force=True)
else:
  # try to pick up stored credentials
  g.login()

x = options.x
y = options.y

r = g.load_sector([options.x, options.y])
print r.points
    
