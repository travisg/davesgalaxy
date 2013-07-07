# vim: set ts=2 sw=2 expandtab:
import json
import math
import os
import pickle
import re
import subprocess
import shape
import sys
import time
import types
import urllib
import urllib2
import httplib
import zlib
import gzip
import StringIO
from itertools import izip
from BeautifulSoup import BeautifulSoup

HOST = "http://davesgalaxy.com/"
URL_LOGIN = HOST + "/login/"
URL_VIEW = HOST + "/view/"
URL_PLANETS = HOST + "/planets/list/all/%d/"
URL_FLEETS = HOST + "/fleets/list/all/%d/"
URL_PLANET_DETAIL = HOST + "/planets/%d/info/"
URL_PLANET_UPGRADES =  HOST + "/planets/%d/upgradelist/"
URL_PLANET_UPGRADE_ACTION =  HOST + "/planets/%d/upgrades/%s/%d/"
URL_PLANET_MANAGE = HOST + "/planets/%d/manage/"
URL_PLANET_BUDGET = HOST + "/planets/%d/budget/"
URL_FLEET_DETAIL = HOST + "/fleets/%d/info/"
URL_PLANETS_JSON = HOST + "/planets/list2/"
URL_FLEETS_JSON = HOST + "/fleets/list2/"
URL_MOVE_TO_PLANET = HOST + "/fleets/%d/movetoplanet/"
URL_MOVE_TO_ROUTE = HOST + "/fleets/%d/onto/"
URL_MOVE_ROUTE_TO = HOST + "/fleets/%d/routeto/"
URL_BUILD_FLEET = HOST + "/planets/%d/buildfleet/"
URL_SCRAP_FLEET = HOST + "/fleets/%d/scrap/"
URL_BUILD_ROUTE = HOST + '/routes/named/add/'
URL_DELETE_ROUTE = HOST + '/routes/%d/delete/'
URL_RENAME_ROUTE = HOST + '/routes/%d/rename/'
URL_SECTORS = HOST + "sectors/"

UPGRADE_UNAVAILABLE = 0
UPGRADE_AVAILABLE = 1
UPGRADE_INACTIVE = 2
UPGRADE_STARTED = 3
UPGRADE_STARTED_0 = 4
UPGRADE_ACTIVE = 5

CACHE_STALE_TIME = 12 * 60 * 60
PLANET_CACHE_FILE = 'planet.dat'
FLEET_CACHE_FILE = 'fleet.dat'
CREDENTIAL_CACHE_FILE = 'login.dat'

ALL_SHIPS = {
  'superbattleships': {'steel':8000,
                       'unobtanium':102,
                       'population':150,
                       'food':300,
                       'antimatter':1050,
                       'money':32485,
                       'krellmetal':290,
                       'needbase':True},
  'bulkfreighters': {'steel':2500,
                     'unobtanium':0,
                     'population':20,
                     'food':20,
                     'antimatter':50,
                     'money':5649,
                     'krellmetal':0,
                     'needbase':False},
  'subspacers': {'steel':625,
                 'unobtanium':0,
                 'population':50,
                 'food':50,
                 'antimatter':250,
                 'money':5414,
                 'krellmetal':16,
                 'needbase':False},
  'arcs': {'steel':10000,
           'unobtanium':0,
           'population':2000,
           'food':1000,
           'antimatter':500,
           'money':10000,
           'krellmetal':0,
           'needbase':False},
  'blackbirds': {'steel':500,
                 'unobtanium':25,
                 'population':5,
                 'food':5,
                 'antimatter':125,
                 'money':9500,
                 'krellmetal':50,
                 'needbase':False},
  'merchantmen': {'steel':750,
                  'unobtanium':0,
                  'population':20,
                  'food':20,
                  'antimatter':50,
                  'money':5433,
                  'krellmetal':0,
                  'needbase':False},
  'scouts': {'steel':250,
             'unobtanium':0,
             'population':5,
             'food':5,
             'antimatter':25,
             'money':108,
             'krellmetal':0,
             'needbase':False},
  'battleships': {'steel':4000,
                  'unobtanium':20,
                  'population':110,
                  'food':200,
                  'antimatter':655,
                  'money':10828,
                  'krellmetal':155,
                  'needbase':True},
  'destroyers': {'steel':1200,
                 'unobtanium':0,
                 'population':60,
                 'food':70,
                 'antimatter':276,
                 'money':5000,
                 'krellmetal':0,
                 'needbase':False},
  'frigates': {'steel':950,
               'unobtanium':0,
               'population':50,
               'food':50,
               'antimatter':200,
               'money':541,
               'krellmetal':0,
               'needbase':False},
  'cruisers': {'steel':1625,
               'unobtanium':0,
               'population':80,
               'food':100,
               'antimatter':385,
               'money':14000,
               'krellmetal':67,
               'needbase':True},
  'harvesters': {'steel':5000,
               'unobtanium':0,
               'population':25,
               'food':20,
               'antimatter':50,
               'money':2815,
               'krellmetal':0,
               'needbase':True},
}

UPGRADES = [
  'Long Range Sensors 1',
  'Long Range Sensors 2',
  'Trade Incentives',
  'Regional Government',
  'Mind Control',
  'Matter Synth 1',
  'Matter Synth 2',
  'Military Base',
  'Slingshot',
  'Farm Subsidies',
  'Drilling Subsidies',
  'Planetary Defense 1',
  'Petrochemical Power Plant',
  'Fusion Power Plant',
  'Antimatter Power Plant'
]

ME = 'me'

def pairs(t):
  return izip(*[iter(t)]*2)

def parse_coords(s):
  m = re.match(r'\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)', s)
  if m: return map(float, m.groups())
  return None

def ship_cost(manifest):
  cost = {'money': 0,
          'steel': 0,
          'population': 0,
          'unobtanium': 0,
          'food': 0,
          'antimatter': 0,
          'krellmetal': 0,
          'needbase': False}
  for type,quantity in manifest.items():
    cost['money'] += quantity * ALL_SHIPS[type]['money']
    cost['steel'] += quantity * ALL_SHIPS[type]['steel']
    cost['population'] += quantity * ALL_SHIPS[type]['population']
    cost['unobtanium'] += quantity * ALL_SHIPS[type]['unobtanium']
    cost['food'] += quantity * ALL_SHIPS[type]['food']
    cost['antimatter'] += quantity * ALL_SHIPS[type]['antimatter']
    cost['krellmetal'] += quantity * ALL_SHIPS[type]['krellmetal']

    # if one of the ships on the list needs a military base, mark it
    if ALL_SHIPS[type]['needbase']:
      cost['needbase'] = True
  return cost

def distance_between(locationA, locationB):
    return math.sqrt(math.pow(abs(locationA[0]-locationB[0]), 2) +
                     math.pow(abs(locationA[1]-locationB[1]), 2))

def ParseFleet(fleetstr):
  fleet = { }

  if fleetstr == None:
    return fleet

  #print "parsefleet " + fleetstr

  num = 0
  for c in fleetstr:
    if c >= '0' and c <= '9':
      num *= 10
      num += int(c)
    elif c == 's':
      fleet.update(scouts=num)
      num = 0
    elif c == 'f':
      fleet.update(frigates=num)
      num = 0
    elif c == 'd':
      fleet.update(destroyers=num)
      num = 0
    elif c == 'c':
      fleet.update(cruisers=num)
      num = 0
    elif c == 'l':
      fleet.update(blackbirds=num)
      num = 0
    elif c == 'b':
      fleet.update(battleships=num)
      num = 0
    elif c == 'B':
      fleet.update(superbattleships=num)
      num = 0
    elif c == 'u':
      fleet.update(subspacers=num)
      num = 0
    elif c == 'a':
      fleet.update(arcs=num)
      num = 0
    elif c == 'r':
      fleet.update(freighters=num)
      num = 0
    elif c == 'm':
      fleet.update(merchantmen=num)
      num = 0
    elif c == 'h':
      fleet.update(harvesters=num)
      num = 0
    else:
      print "bad fleet token " + c
      num = 0

    #print "fleet " + str(fleet)

  return fleet

def FindUnownedPlanetsInShape(g, shape):
  sect = g.load_sectors(shape.bounding_box())

  planets = []
  for p in sect["planets"]["unowned"]:
    if shape.inside(p.location):
      planets.append(p)

  return planets

def FindOwnedPlanetsInShape(g, shape):
  sect = g.load_sectors(shape.bounding_box())

  planets = []
  for p in sect["planets"]["owned"]:
    if shape.inside(p.location):
      planets.append(p)

  return planets

def FindAllPlanetsInShape(g, shape):
  sect = g.load_sectors(shape.bounding_box())

  planets = []
  for p in sect["planets"]["owned"]:
    if shape.inside(p.location):
      planets.append(p)
  for p in sect["planets"]["unowned"]:
    if shape.inside(p.location):
      planets.append(p)

  return planets

def TrimColonyTargettedPlanets(g, targets):
  # trim the list of targets to ones that dont have an arc already incoming
  for f in g.fleets:
    f.load()
    try:
      if f.disposition == "Colonize":
      # look for destinations in the NAME-NUMBER form
        pnum = int(f.destination.split('-')[1])
        for p in targets:
          if p.planetid == pnum:
            #print "fleet " + str(f) + " already heading for dest"
            targets.remove(p)
            break
    except:
      pass

  return targets

def FleetDestToPlanetID(destination):
  # if it's a real planet target, get the id
  dest_planet_id = None
  try:
    dest_planet_id = int(destination.planetid)
  except:
    pass

  # if its a string target, try to extract the planetid from it
  if dest_planet_id == None:
    try:
      s = destination.split('-')
      dest_planet_id = int(s[len(s)-1])
    except:
      pass

  return dest_planet_id


class Planet:
  def __init__(self, galaxy, planetid='0', name='unknown', location=None, owner=ME):
    self.galaxy = galaxy
    self.planetid = int(planetid)
    self.owner = str(owner)
    self.name = str(name)
    self.location = location
    self._loaded = False
    self._upgrades = None
  def __repr__(self):
    return "<Planet #%d \"%s\" owner %s>" % (self.planetid, self.name, self.owner)
  def __getstate__(self):
    return dict(filter(lambda x:  x[0] != 'galaxy',  self.__dict__.items()))
  def load(self, force=False):
    if not force and self._loaded: return False
    req = self.galaxy.urlopen(URL_PLANET_DETAIL % self.planetid)

    soup = BeautifulSoup(json.loads(req)['tab'])

    self.society = int(soup('div',{'class':'info1'})[0]('div')[2].string)
    data = [x.string.strip() for x in soup('td',{'class':'planetinfo2'})]
    i = 0
    if self.name == 'unknown':
      self.name = str(data[i])
    i+=1
    self.owner=data[i]; i+=1
    if self.location == None:
      self.location=map(float, re.findall(r'[0-9.]+', data[i]));
    i+=1
    if soup.find(text='Distance to Capital:'):
      self.distance=float(data[i]) ; i+=1
    else:
      self.distance=0.0
    if soup.find(text='Income Tax Rate:'):
      self.tax=float(data[i]) ; i+=1
    else:
      self.tax=0.0
    if soup.find(text='Open Ship Yard:'): i+=1
    if soup.find(text='Trades Rare Commodities:'): i+=1
    if soup.find(text='Open Trading:'): i+=1
    if soup.find(text='Tariff Rate:'):
      self.tarif=float(data[i]) ; i+=1
    else:
      self.tarif=0.0
    try:
      self.population=int(data[i]) ; i+=1
      self.money=int(data[i].split()[0]) ; i+=1
      self.steel=int(data[i:i+3]) ; i+=3
      self.unobtanium=int(data[i:i+3]) ; i+=3
      self.strangeness=int(data[i:i+3]) ; i+=3
      self.food=int(data[i:i+3]) ; i+=3
      self.antimatter=int(data[i:i+3]) ; i+=3
      self.consumergoods=int(data[i:i+3]) ; i+=3
      self.charm=int(data[i:i+3]) ; i+=3
      self.helium3=int(data[i:i+3]) ; i+=3
      self.hydrocarbon=int(data[i:i+3]) ; i+=3
      self.krellmetal=int(data[i:i+3]) ; i+=3
    except IndexError:
      sys.stderr.write("loaded alien planet\n")
    self.loadUpgrades()
    self._loaded = True
    return True
  def load_from_json(self, data, resource_map):
#   resources:
# {u'steel': 9,
#  u'unobtanium': 11,
#  u'strangeness': 10,
#  u'people': 7,
#  u'food': 3,
#  u'antimatter': 0,
#  u'consumergoods': 2,
#  u'charm': 1,
#  u'quatloos': 8,
#  u'helium3': 4,
#  u'hydrocarbon': 5,
#  u'krellmetal': 6}
#  planet data:
#   data map from top level view.js
#   { "name":3,"sector_id":2,"hexcolor":6,"inctaxrate":9,"tariffrate":10,"y":12,"society":4,"sensorrange":5,"r":7,"flags":13,"resourcelist":8,"x":11,"id":0,"owner_id":1, };
#   flags from view.js
#   { "farm_subsidies":512,"in_nebulae":8192,"open_trade":64,"food_subsidy":1,"famine":2,"player_owned":128,"military_base":16,"matter_synth1":8,"matter_synth2":32,"can_build_ships":4096,"planetary_defense":256,"damaged":2048,"drilling_subsidies":1024,"rgl_govt":4, };
#  0:  [5994573, id
#  1:  953, owner
#  2:  228228, sector
#  3:  u'Theta Auriinus', name
#  4:  79, society level
#  5:  2.28, scanner range
#  6:  u'#ffff73', color
#  7:  0.0537592276003, radius
#  8:  [100619, 0, 135671, 237091, 0, 248002, 15272, 14021240, 9261281, 25479, 0, 4149], resourcelist
#  9:  30.0, tax rate
#  10: 0.0, tariff rate
#  11: 1140.16897901, xcoord
#  12: 1140.79188543, ycoord
#  13: 4160] flags
    try:
    # load basics
      self.planetid = int(data[0])
      self.name = str(data[3])
      self.society = int(data[4])
      self.tax = float(data[9])
      self.tarif = float(data[10])
      self.location = [ float(data[11]), float(data[12]) ]
      self.flags = int(data[13])

    # load commodities
      resources = data[8]
      self.population = int(resources[resource_map['people']])
      self.money = int(resources[resource_map['quatloos']])
      self.steel = int(resources[resource_map['steel']])
      self.unobtanium = int(resources[resource_map['unobtanium']])
      self.strangeness = int(resources[resource_map['strangeness']])
      self.food = int(resources[resource_map['food']])
      self.antimatter = int(resources[resource_map['antimatter']])
      self.consumergoods = int(resources[resource_map['consumergoods']])
      self.charm = int(resources[resource_map['charm']])
      self.helium3 = int(resources[resource_map['helium3']])
      self.hydrocarbon = int(resources[resource_map['hydrocarbon']])
      self.krellmetal = int(resources[resource_map['krellmetal']])

      self._loaded = True
    except:
      return False

    return True

  def how_many_can_build(self, manifest):
    self.load()
    cost = ship_cost(manifest)
    count = -1

    has_base = self.has_active_upgrade('Military Base')
    if cost['needbase'] and not has_base:
      return 0

    if cost['money'] > 0:
      newcount = self.money / cost['money']
      if (count < 0 or newcount < count): count = newcount
    if cost['steel'] > 0:
      newcount = self.steel / cost['steel']
      if (count < 0 or newcount < count): count = newcount
    if cost['population'] > 0:
      newcount = self.population / cost['population']
      if (count < 0 or newcount < count): count = newcount
    if cost['unobtanium'] > 0:
      newcount = self.unobtanium / cost['unobtanium']
      if (count < 0 or newcount < count): count = newcount
    if cost['food'] > 0:
      newcount = self.food / cost['food']
      if (count < 0 or newcount < count): count = newcount
    if cost['antimatter'] > 0:
      newcount = self.antimatter / cost['antimatter']
      if (count < 0 or newcount < count): count = newcount
    if cost['krellmetal'] > 0:
      newcount = self.krellmetal / cost['krellmetal']
      if (count < 0 or newcount < count): count = newcount

    if (count < 0): count = 0
    return count
  def can_build(self, manifest):
    return self.how_many_can_build(manifest) > 0
  def build_fleet(self, manifest, interactive=False, skip_check=False):
    fleet = None
    if skip_check or self.can_build(manifest):
      formdata = {}
      formdata['submit-build-%d' % self.planetid] = 1
      formdata['submit-build-another-%d' % self.planetid] =1
      for type,quantity in manifest.items():
        formdata['num-%s' % type] = quantity
      req = self.galaxy.urlopen(URL_BUILD_FLEET % self.planetid,
                                    urllib.urlencode(formdata))
      if 'Fleet Built' in req:
        j = json.loads(req)
        fleet = Fleet(self.galaxy,
                      j['newfleet']['i'],
                      [j['newfleet']['x'], j['newfleet']['y']],
                      True) # feets are created at planets
        if self.galaxy._fleets:
          self.galaxy.fleets.append(fleet)
        if self._loaded:
          cost = ship_cost(manifest)
          self.money -= cost['money']
          self.steel -= cost['steel']
          self.population -= cost['population']
          self.unobtanium -= cost['unobtanium']
          self.food -= cost['food']
          self.antimatter -= cost['antimatter']
          self.krellmetal -= cost['krellmetal']
        if interactive:
          js = 'javascript:handleserverresponse(%s);' % req
          subprocess.call(['osascript', 'EvalJavascript.scpt', js ])
      else:
        sys.stderr.write('error when building')
    else:
      sys.stderr.write('cannot build %s\n' % str(manifest))
    return fleet
  def scrap_fleet(self, fleet):
    if fleet.scrap() and self._loaded and fleet._loaded:
      value = ship_cost(fleet.ships)
      self.money += value['money']
      self.steel += value['steel']
      self.population += value['population']
      self.unobtanium += value['unobtanium']
      self.food += value['food']
      self.antimatter += value['antimatter']
      self.krellmetal += value['krellmetal']
      return value
    else:
      return None
  def view(self):
    js = 'javascript:gm.centermap(%d, %d);' % (self.location[0],
                                               self.location[1])
    subprocess.call(['osascript', 'EvalJavascript.scpt', js ])
  def distance_to(self, other):
    return distance_between(self.location, other.location)
  def loadUpgrades(self):
    if self._upgrades: return self._upgrades
    self._upgrades = map(lambda x: UPGRADE_UNAVAILABLE, range(0,len(UPGRADES)))
    try:
      req = self.galaxy.urlopen(URL_PLANET_UPGRADES % self.planetid)
      soup = BeautifulSoup(json.loads(req)['tab'])
      for row in soup('tr')[1:]:
        if 'td' in str(row):
          cells=row('td')
          if len(cells) > 3:
            m=re.search(r'/planets/[0-9]+/upgrades/([a-z]+)/([0-9]+).',
                        str(row))
            idx = int(m.group(2))
            self._upgrades[idx] = UPGRADE_AVAILABLE
            if m.group(1) == 'scrap':
              self._upgrades[idx] = UPGRADE_STARTED
              if 'Active' in str(cells[2]):
                self._upgrades[idx] = UPGRADE_ACTIVE
              elif '100%' in str(cells[3]):
                self._upgrades[idx] = UPGRADE_INACTIVE
              elif '0%' in str(cells[3]):
                self._upgrades[idx] = UPGRADE_STARTED_0
    except:
      pass
    return self._upgrades
  @property
  def upgrades(self):
    if self._upgrades: return self._upgrades
    self.loadUpgrades()
    return self._upgrades
  def can_upgrade(self, upgrade):
    self.loadUpgrades()
    index = UPGRADES.index(upgrade)
    return self.upgrades[index] == UPGRADE_AVAILABLE
  def has_upgrade(self, upgrade):
    self.loadUpgrades()
    index = UPGRADES.index(upgrade)
    return self.upgrades[index] > UPGRADE_AVAILABLE
  def has_active_upgrade(self, upgrade):
    self.loadUpgrades()
    index = UPGRADES.index(upgrade)
    return self.upgrades[index] == UPGRADE_ACTIVE
  def building_upgrade_zeropercent(self, upgrade):
    self.loadUpgrades()
    index = UPGRADES.index(upgrade)
    return self.upgrades[index] == UPGRADE_STARTED_0
  def building_upgrade(self, upgrade):
    self.loadUpgrades()
    index = UPGRADES.index(upgrade)
    return self.upgrades[index] == UPGRADE_STARTED or self.upgrades[index] == UPGRADE_STARTED_0
  def start_upgrade(self, upgrade):
    index = UPGRADES.index(upgrade)
    if not self.can_upgrade(upgrade):
      return False

    req = self.galaxy.urlopen(URL_PLANET_UPGRADE_ACTION %
                            (self.planetid, 'start', index))
    if req == None:
      return False

    self.upgrades[index] = UPGRADE_STARTED_0
    return True
  def scrap_upgrade(self, upgrade):
    index = UPGRADES.index(upgrade)
    req = self.galaxy.urlopen(URL_PLANET_UPGRADE_ACTION %
                            (self.planetid, 'scrap', index))
    if req == None:
      return False
    self.upgrades[index] = UPGRADE_AVAILABLE
    return True

  def manage(self, name, taxrate, tariff):
    if (taxrate >= 0.0 and taxrate <= 30.0):
      self.tax = float(taxrate)
    if (tariff >= 0.0 and tariff <= 30.0):
      self.tarif = float(tariff)

    self.name = name

    formdata = {}
    formdata['name'] = self.name
    formdata['tariffrate'] = str(self.tarif)
    formdata['inctaxrate'] = str(self.tax)
    req = self.galaxy.urlopen(URL_PLANET_MANAGE % self.planetid,
                                  urllib.urlencode(formdata))
    success = 'Planet Managed' in req
    if not success:
      sys.stderr.write('%s/n' % response)
    return success

  def set_tax(self, rate):
    return self.manage(self.name, rate, self.tarif)

  def set_tariff(self, rate):
    return self.manage(self.name, self.tax, rate)

  def set_name(self, name):
    return self.manage(name, self.tax, self.tarif)

class Fleet:
  def __init__(self, galaxy, fleetid, coords, at=False):
    self.galaxy = galaxy
    self.fleetid = int(fleetid)
    self.coords = coords
    self.at_planet = at
    self.home = None
    self.disposition = None
    self._loaded = False
  def __repr__(self):
    return "<Fleet #%d%s @ (%.1f,%.1f)>" % (self.fleetid,
      (' (%s, %d ships)' % (self.disposition, self.shipcount())) \
        if self._loaded else '',
      self.coords[0], self.coords[1])
  def __getstate__(self):
    return dict(filter(lambda x:  x[0] != 'galaxy',  self.__dict__.items()))
  def load(self, force=False):
    if not force and self._loaded: return False
    retry = 0
    done = False
    while not done:
      retry += 1
      if retry >= 5:
        return False
      done = True
      try:
        url = URL_FLEET_DETAIL % self.fleetid
        #print url
        req = self.galaxy.urlopen(url)
        soup = BeautifulSoup(json.loads(req)['pagedata'])
        home = str(soup.find(text="Home Port:").findNext('td').string)
        homesplit = home.split('-')
        homeid = homesplit[len(homesplit)-1]
        self.home = self.galaxy.find_planet(int(homeid))
        dest = str(soup.find(text="Destination:").findNext('td').string)
        self.destination = parse_coords(dest)
        if not self.destination:
          dsplit = dest.split('-')
          self.destination = self.galaxy.find_planet(int(dsplit[len(dsplit)-1]))
          if not self.destination:
            # must be headed for a unowned planet
            self.destination = dest
        self.disposition = str(soup.find(text="Disposition:")
                             .findNext('td').string).split(' - ')[1]
        try:
          self.speed = float(soup.find(text="Current Speed:")
                             .findNext('td').string)
        except: self.speed = 0

        try:
          routestr = soup.find(text="On Route:").findNext('td').string

          if routestr.find("Named Route --") == 0:
            # this has a named route field in the format 'Named Route -- <name of the route with spaces>(number)'
            a = routestr.rsplit(')')
            b = a[0].rsplit('(')
            routeid = int(b[1])
            self.routeid = routeid
        except:
          self.routeid = -1
          pass

        self.ships = dict()
        try:
          for k,v in pairs(soup('h3')[0].findAllNext('td')):
            shiptype = re.match(r'[a-z]+', k.string).group()
            if not shiptype in ALL_SHIPS.keys(): continue
            self.ships[shiptype] = int(v.string)
        except IndexError:
          pass  # empty fleet
      except (IndexError, ValueError):
        # stale fleet
        print "stale fleet %d" % self.fleetid
        self.destination = None
        self.disposition = "unknown"
        self.speed = 0.0
        self.routeid = -1
        self.ships = dict()

    self._loaded = True
    return True
  def move_to_planet(self, planet):
    formdata = {}
    formdata['planet' ] = planet.planetid
    req = self.galaxy.urlopen(URL_MOVE_TO_PLANET % self.fleetid,
                                  urllib.urlencode(formdata))
    success = 'Destination Changed' in req
    if not success:
      sys.stderr.write('%s/n' % req)

    # force a reload to get any new destination
    self.load(True)
    return success
  def move_to_route(self, route, insertion_point=None):
    formdata = {}
    formdata['route' ] = route.routeid
    if insertion_point == None:
      route_shape = shape.Polygon(*(route.points))
      insertion_point = route_shape.nearest_to(self.coords)
    formdata['sx'] = insertion_point[0]
    formdata['sy'] = insertion_point[1]
    req = self.galaxy.urlopen(URL_MOVE_TO_ROUTE % self.fleetid,
                                  urllib.urlencode(formdata))
    success = 'Fleet Routed' in req
    if not success:
      sys.stderr.write('%s/n' % req)
    # force a reload to get any new destination
    self.load(True)
    return success
  def route_to(self, points, planetid=None):
    formdata = {}
    formdata['circular'] = False
    formdata['route'] = ','.join(map(lambda p:
                                     '/'.join(map(lambda x: str(x), p)),
                                     points))
    if planetid:
      formdata['route'] = "%s, %s" % (formdata['route'], str(planetid))
    req = self.galaxy.urlopen(URL_MOVE_ROUTE_TO % self.fleetid,
                                  urllib.urlencode(formdata))
    success = 'Fleet Routed' in req
    if not success:
      sys.stderr.write('%s/n' % req)
    return success
  def at(self, planet):
    if not self.at_planet:
      return False
    if not planet:
      return False
    if type(self.coords) == types.ListType:
      return math.sqrt(math.pow(self.coords[0]-planet.location[0], 2) +
                       math.pow(self.coords[1]-planet.location[1], 2)) < 0.1
    return str(planet.planetid) in self.coords
  def scrap(self):
    if not self.at_planet:
      return False
    req = self.galaxy.urlopen(URL_SCRAP_FLEET % self.fleetid)
    fleet = None
    return 'Fleet Scrapped' in req
  def shipcount(self):
    count = 0
    for s in self.ships:
      count += self.ships[s]
    return count
  def view(self):
    js = 'javascript:gm.centermap(%d, %d);' % (self.coords[0],
                                               self.coords[1])
    subprocess.call(['osascript', 'EvalJavascript.scpt', js ])

class Route:
  def __init__(self, galaxy, id, circular, name, points):
    self.galaxy = galaxy
    self.routeid = int(id)
    self.circular = circular
    self.name = name
    self.points = points

    for p in points:
      if len(p) == 3:
        del p[0]
  def __repr__(self):
    return "<Route #%d \"%s\">" % (self.routeid, self.name)
  def __getstate__(self):
    return dict(filter(lambda x:  x[0] != 'galaxy',  self.__dict__.items()))
  def rename(self, name):
    formdata = {}
    formdata['name'] = name
    req = self.galaxy.urlopen(URL_RENAME_ROUTE % self.routeid,
                                  urllib.urlencode(formdata))
    if 'Route Renamed' in req:
      self.name = name
    return self.name
  def delete(self):
    formdata = {}
    formdata['hi'] = 1
    req = self.galaxy.urlopen(URL_DELETE_ROUTE % self.routeid,
                                  urllib.urlencode(formdata))
    if 'Route Deleted' in req:
      # remove us from the galaxy we're in
      del self.galaxy.routes[self.routeid]
      return True
    return False

class Galaxy:
  def __init__(self):
    self._planets = None
    self._fleets = None
    self._routes = None
    self._stars = None # alien planets
    self._logged_in = False
    self.session = None
    try:
      cache_file = open(CREDENTIAL_CACHE_FILE, 'r')
      cache_data = pickle.load(cache_file)
      cache_file.close()
      self.session = cache_data
      self._logged_in = True
    except:
      pass
    self.http = httplib.HTTPConnection("davesgalaxy.com")
    self.http.connect()
  def login(self, u='', p='', force=False):
    if force or not self._logged_in:
      self.urlopen(URL_LOGIN,
        urllib.urlencode(dict(usernamexor=u, passwordxor=p)))
      if self.session != None:
        self._logged_in = True
        self.write_cache(CREDENTIAL_CACHE_FILE, self.session)
    else:
      sys.stderr.write("using stored credentials\n")

  def urlopen(self, url, data=None):
    #print "opening url %s" % url
    #print data

#    i = 0
#    req = None
#    while i < 5:
#      i = i + 1
#      try:
#        req = self.opener.open(url)
#        break
#      except urllib2.HTTPError:
#        sys.stderr.write("http error opening url %s, attempt %d" % (str(url), i))
#        time.sleep(1)

    i = 0
    while i < 5:
      i = i + 1

      # construct a http header
      sessionheader = {}
      if self.session:
        sessionheader["Cookie"] = self.session.split(";")[0]
        #print sessionheader
      headers = {"Content-Type": "application/x-www-form-urlencoded",
                 "Accept": "application/json, text/javascript, */*",
                 "Accept-Encoding": "gzip",
                 "Connection": "keep-alive",
      }
      headers.update(sessionheader)

      if data != None:
        self.http.request("POST", url, data, headers)
      else:
        self.http.request("GET", url, None, headers)

      try:
        r1 = self.http.getresponse()
        #print r1.status, r1.reason
      except httplib.BadStatusLine:
        print "bad status line, reconnecting"
        self.http = httplib.HTTPConnection("davesgalaxy.com")
        self.http.connect()
        continue

      # look for login session
      session = r1.getheader("set-cookie")
      if session != None:
        self.session = session

      req = r1.read()

      # if it's gzipped, decompress it
      encoding = r1.getheader("content-encoding", "")
      if encoding == "gzip":
        #print "GZIP compressed len %d" % len(req)
        f = gzip.GzipFile('', 'rb', 9, StringIO.StringIO(req))
        req = f.read()
        #print "uncompressed len %d" % len(req)

      #print req
      return req

    return None

  def get_planet(self, id):
    for p in self.planets:
      if id == p.planetid:
        return p
    return None

  def find_route(self, query):
    if type(query) == types.StringType:
      for route in self.routes.values():
        if route.name == query:
          return route
      return None
    if type(query) == types.IntType:
      try:
        return self.routes[query]
      except KeyError:
        return None

  def find_fleet(self, query):
    if type(query) == types.IntType:
      for f in self.fleets:
        if query == f.fleetid:
          return f
      return None
    return None

  def find_planet(self, query):
    if type(query) == types.StringType:
      for p in self.planets:
        if query == p.name:
          return p
      return None
    if type(query) == types.IntType:
      for p in self.planets:
        if query == p.planetid:
          return p
      return None
    return None

  def load_all_planets(self):
    all_loaded = True
    for p in self.planets:
      all_loaded = p._loaded and all_loaded
    if not all_loaded:
      sys.stderr.write("loading all planets\n")
      for p in self.planets:
        p.load()
    return None

  def load_all_fleets(self):
    all_loaded = True
    for f in self.fleets:
      all_loaded = f._loaded and all_loaded
    if not all_loaded:
      sys.stderr.write("loading all fleets\n")
      for f in self.fleets:
        f.load()
      self.write_fleet_cache()
    return None

  def my_planets_near(self, pivot):
    survey = []
    for p in self.planets:
      if p != pivot:
        survey.append({'planet': p, 'distance': pivot.distance_to(p)})
    survey.sort(lambda a, b: cmp(a['distance'], b['distance']))
    return survey

  @property
  def routes(self):
    if self._routes: return self._routes
    self.load_routes()
    return self._routes

  @property
  def planets(self):
    if self._planets: return self._planets

    self.load_planet_cache()
    if self._planets: return self._planets

    print("fetching planets")

    sys.stderr.write('no planet cache, fetching list of planets')
    i=1
    planets = []
    try:
      req = self.urlopen(URL_PLANETS_JSON)
      j = json.loads(req)

      commodities = j['commodities']

      planetlist = j['planetlist']
      #print planetlist
      for value in planetlist:
        #print value
        p = Planet(self)
        if not p.load_from_json(value, commodities):
          continue
        #print p
        i += 1
        planets.append(p)

    except:
      sys.stderr.write('error fetching from json planet url\n');

    sys.stderr.write('\nfinished fetching, fetched %i planets total\n' % len(planets))
    self._planets = planets
    self.write_planet_cache()
    return planets

  @property
  def fleets(self):
    if self._fleets: return self._fleets

    self.load_fleet_cache()
    if self._fleets: return self._fleets

    sys.stderr.write('no fleet cache, fetching list of fleets\n')
    i=1
    fleets = []
    while True:
      try:
        url = URL_FLEETS % i
        req = self.urlopen(url)
        soup = BeautifulSoup(json.loads(req)['tab'])
        for row in soup('tr')[1:]:
          cells=row('td')
          fleetid=re.search(r'/fleets/([0-9]*)/',
                             str(row('td')[0])).group(1)
#class=\"rowheader\"/>\n      <th class=\"rowheader\">ID</th><th
#class=\"rowheader\">Ships</th>\n      <th
#class=\"rowheader\">Disposition</th><th
#class=\"rowheader\">Destination</th>\n      <th
#class=\"rowheader\">Att.</th><th class=\"rowheader\">Def.</th>\n
          coords = parse_coords(
            re.search(r'gm.centermap(\([0-9.,]+\))', str(row)).group(1))
          at_planet = bool(re.search(r'\'scrapfleet\':[0-9]+', str(row)))
          fleets.append(Fleet(self, fleetid, coords, at=at_planet))
        sys.stderr.write('\rfetched %i fleets total' % len(fleets))
        i += 1
      except KeyError:
        break
      except ValueError:
        break
    sys.stderr.write('\nfinished fetching, fetched %i fleets total\n' % len(fleets))
    self._fleets = fleets
    self.write_fleet_cache()
    return fleets

  def load_routes(self):
    formdata = {}
    formdata['0'] = 1
    formdata['getnamedroutes'] = 'yes'
    req = self.urlopen(URL_SECTORS,
                           urllib.urlencode(formdata))
    j = json.loads(req)

    routes = self.parse_routes(j)
    if self._routes:
      self._routes.update(routes)
    else:
      self._routes = routes
    return self._routes

  def load_raw_sectors(self, bounding_box):
    formdata = {}
    routes = {}

    topx = int(bounding_box[0][0])/5
    topy = int(bounding_box[0][1])/5
    bottomx = int(bounding_box[1][0])/5
    bottomy = int(bounding_box[1][1])/5
    #print "%s,%s %s,%s" % (str(topx), str(topy), str(bottomx), str(bottomy))

    for x in range(topx, bottomx+1):
      for y in range(topy, bottomy+1):
        sector = x * 1000 + y
        formdata[str(sector)] = 1
    if routes:
      formdata['getnamedroutes'] = 'yes'
    #print formdata
    req = self.urlopen(URL_SECTORS,
                           urllib.urlencode(formdata))
    #print req
    return req

  def load_sectors(self, bounding_box):
    #print "load sectors " + str(bounding_box)
    j = json.loads(self.load_raw_sectors(bounding_box))

    unowned_planets = []
    owned_planets = []
    # parse the result, looking for planetary data
    secs = j["sectors"]["sectors"]
    #print secs
    for secnum in secs:
      if "planets" in secs[secnum]:
        planets = secs[secnum]["planets"]
        for pnum in planets:
          #print "\tplanet " + str(pnum)
          try:
            p = planets[pnum]
            pid = int(p["i"])
            owner = int(p.get("o", 0))
            locationx = float(p["x"])
            locationy = float(p["y"])
            name = str(p["n"])
            #print planet
            if owner == 0:
              planet = Planet(self, pid, name, [ locationx, locationy ], "unowned")
              unowned_planets.append(planet)
            else:
              planet = Planet(self, pid, name, [ locationx, locationy ], str(owner))
              owned_planets.append(planet)
          except:
            pass
    result = {}
    result["planets"] = {}
    result["planets"]["unowned"] = unowned_planets
    result["planets"]["owned"] = owned_planets
    result["routes"] = self.parse_routes(j)
    return result

  def parse_routes(self, j):
    routes = {}
    for key, value in j['sectors']['routes'].iteritems():
      if re.match(r'[\[,.\]0-9\" ]+$', value['p']): # check input
        p = eval(value['p'])
        n = "Unnamed Route (%d)" % int(key)
        if 'n' in value.keys():
          n = str(value['n'])
        routes[int(key)] = Route(self, int(key), value['c'], n, p)
    return routes

  def load_sector_at(self, location):
    return self.load_sectors([location, location])

  def load_raw_sector_at(self, location):
    return self.load_raw_sectors([location, location])

  def create_route(self, name, circular, points):
    formdata = {}
    formdata['name'] = name
    formdata['circular'] = str(circular).lower()
    formdata['route'] = ','.join(map(lambda p:
                                     '/'.join(map(lambda x: str(x), p)),
                                     points))
    req = self.urlopen(URL_BUILD_ROUTE,
                           urllib.urlencode(formdata))
    route = None
    if 'Route Built' in req:
      j = json.loads(req)
      routeid = int(j['sectors']['routes'].keys()[0])
      route = Route(self, routeid, circular, name, points)
      self.routes[routeid] = route
    return route

  def write_planet_cache(self):
    # TODO: planets fail to pickle due to a lock object, write a reduce
    print "writing planet cache..."
    self.write_cache(PLANET_CACHE_FILE, self._planets)
    return None

  def load_planet_cache(self):
    self._planets = self.load_cache(PLANET_CACHE_FILE )
    return None

  def write_fleet_cache(self):
    print "writing fleet cache..."
    self.write_cache(FLEET_CACHE_FILE, self._fleets)
    return None

  def load_fleet_cache(self):
    self._fleets = self.load_cache(FLEET_CACHE_FILE )
    if self._fleets:
      for item in self._fleets:
        if hasattr(item, 'home') and item.home:
          item.home = self.find_planet(item.home.planetid)
    return None

  def write_cache(self, filename, data):
    # need to bump the recursion limit to let it work
    sys.setrecursionlimit(10000)
    try:
      cache_file = open(filename + ".tmp", 'w')
      pickle.dump(data, cache_file)
      cache_file.flush()
      cache_file.close()
      os.rename(filename + ".tmp", filename)
    except Exception as e:
      print "exception writing cache"
      print type(e)
      print e
      pass
    return None

  def load_cache(self, filename):
    sys.stderr.write("loading cached data from %s...\n" % filename)
    cache_data = None
    try:
      if (time.time() - os.stat(filename).st_mtime) < CACHE_STALE_TIME:
        cache_file = open(filename, 'r')
        cache_data = pickle.load(cache_file)
        cache_file.close()
        for item in cache_data:
          item.galaxy = self
        sys.stderr.write("loaded cached data from %s\n" % filename)
      else:
        sys.stderr.write("cached data in %s is stale\n" % filename)
        pass
    except OSError:
        sys.stderr.write("cache file %s is missing or corrupt\n" % filename)
    return cache_data
