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
  parser.add_option("-s", "--skip_level", dest="skip_level",
                    help="maximum society level to initiate a skip arc",
                    default=20,
                    type="int")
  (options, args) = parser.parse_args()

  g=game.Galaxy()
  if options.username and options.password:
    # explicit login
    g.login(options.username, options.password, force=True)
  else:
    # try to pick up stored credentials
    g.login()

  buildarcs(g, options.skip_level)

    
def buildarcs(g, level):
  escorted = {'arcs': 1, 'frigates': 1}
  solo = {'arcs': 1}
  
  SOLO_PROMPT = 'build solo arc at "%s"? (Y/v/n): '
  ESCORTED_PROMPT = 'build escorted arc at "%s"? (Y/v/n): '
  
  print 'Looking for planets younger than %d to build arcs.' % level
  print 'Name, ID, Society, Money, Antimatter, Steel'
  for p in g.planets:
    p.load()
    if p.society < level:
      confirm = 'y'
      if p.can_build(solo):
        print '"%s", %d, %d, %d, %d, %d' % (
          p.name, p.planetid, p.society, p.money, p.antimatter, p.steel
          )
      while confirm == 'y' and p.can_build(solo):
        if p.can_build(escorted):
          confirm = default_input(ESCORTED_PROMPT % (p.name), 'y')
          if confirm == 'y':
            p.build_fleet(escorted, interactive=True)
          elif confirm == 'v':
            p.view()
            confirm = 'y'
        else:
          confirm = default_input(SOLO_PROMPT % (p.name), 'y')
          if confirm == 'y':
            p.build_fleet(solo, interactive=True)
          elif confirm == 'v':
            p.view()
            confirm = 'y'


if __name__ == "__main__":
    main()
