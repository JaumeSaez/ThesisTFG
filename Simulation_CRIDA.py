import numpy as np
import bluesky as bs
from bluesky import traffic as tr
from bluesky import settings
from bluesky.traffic.route import Route
from bluesky.navdatabase import Navdatabase
from bluesky.simulation import Simulation
from bluesky.traffic.performance.perfbase import PerfBase
import matplotlib.pyplot as plt
from datalogger import Logger
#import rand_conflict
from bluesky.tools import geo
import random
from bluesky.tools.aero import cas2tas, casormach2tas, fpm, kts, ft, g0, Rearth, nm, tas2cas,\
                         vatmos,  vtas2cas, vtas2mach, vcasormach
import os
import json
from datetime import datetime

def rwgs84(latd):
    """ Calculate the earths radius with WGS'84 geoid definition
        In:  lat [deg] (latitude)
        Out: R   [m]   (earth radius) """
    lat    = np.radians(latd)
    a      = 6378137.0       # [m] Major semi-axis WGS-84
    b      = 6356752.314245  # [m] Minor semi-axis WGS-84
    coslat = np.cos(lat)
    sinlat = np.sin(lat)

    an     = a * a * coslat
    bn     = b * b * sinlat
    ad     = a * coslat
    bd     = b * sinlat

    # Calculate radius in meters
    r = np.sqrt((an * an + bn * bn) / (ad * ad + bd * bd))

    return r

def qdrpos(latd1, lond1, qdr, dist):
    """ Calculate vector with positions from vectors of reference position,
        bearing and distance.
        In:
             latd1,lond1  [deg]   ref position(s)
             qdr          [deg]   bearing (vector) from 1 to 2
             dist         [nm]    distance (vector) between 1 and 2
        Out:
             latd2,lond2 (IN DEGREES!)
        Ref for qdrpos: http://www.movable-type.co.uk/scripts/latlong.html """

    # Unit conversion
    R = rwgs84(latd1)/nm
    lat1 = np.radians(latd1)
    lon1 = np.radians(lond1)

    # Calculate new position
    lat2 = np.arcsin(np.sin(lat1)*np.cos(dist/R) +
                     np.cos(lat1)*np.sin(dist/R)*np.cos(np.radians(qdr)))

    lon2 = lon1 + np.arctan2(np.sin(np.radians(qdr))*np.sin(dist/R)*np.cos(lat1),
                             np.cos(dist/R) - np.sin(lat1)*np.sin(lat2))
    return np.degrees(lat2), np.degrees(lon2)

def create_ac(n_ac1, radius,center,lista):
    c=0
    
    while c < n_ac1:
        
        random_angle = random.random() * 360
        random_distance = radius * np.sqrt(random.random())

        random_lat, random_lon = geo.qdrpos(center[0], center[1], random_angle, random_distance)

        random_speed = np.random.uniform(10,20)

        angle = geo.qdrdist(random_lat, random_lon, center[0], center[1])[0]
        limit_angle = np.arccos(random_distance/(2 * radius)) * 180 / np.pi 

        acid = str(random.getrandbits(32))
        heading = random.uniform(angle - limit_angle, angle + limit_angle)


        
        lista.append([acid,random_lat,random_lon,heading])
        
        c+=1
    return lista


def create_ac_conf2(lat1, lon1, qdr, dist, n_ac2, lista):
    c=0
    lon1 =lon1+10
    qdr = 70
    dist = 250
    
    while c<n_ac2:
        
        lat2, lon2 = qdrpos(lat1, lon1, qdr, dist)
        acid = str(random.getrandbits(16))
            
        
        if qdr +100 < 180 and qdr > 0:
            qdr= qdr + 100
            lista.append([acid,lat2,lon2,qdr])
            
            
        elif qdr + 100 >= 180:
            qdr = 180 - (qdr + 100)
            lista.append([acid,lat2,lon2,qdr])
            
        elif qdr < 0 and qdr > -80:
            qdr = qdr - 100
            lista.append([acid,lat2,lon2,qdr])
            
        elif qdr - 100 <= -180:
            qdr = -180 - (qdr - 100)
            lista.append([acid,lat2,lon2,qdr])
        
        lat1=lat2
        lon1=lon2
        c+=1
    
    return lista

def create_ac_conf(lat1, lon1, n_ac, qdr, dist):
    c=0
    list_conf=[]
   
    while c<n_ac:
        
        lat2, lon2 = qdrpos(lat1, lon1, qdr, dist)
        acid = str(random.getrandbits(16))
        
        
        if qdr +100 < 180 and qdr > 0:
            qdr= qdr + 100
            list_conf.append([acid,lat2,lon2,qdr])
          
            
        elif qdr + 100 >= 180:
            qdr = 180 - (qdr + 100)
            list_conf.append([acid,lat2,lon2,qdr])
     
            
        elif qdr < 0 and qdr > -80:
            qdr = qdr - 100
            list_conf.append([acid,lat2,lon2,qdr])
            
            
        elif qdr - 100 <= -180:
            qdr = -180 - (qdr - 100)
            list_conf.append([acid,lat2,lon2,qdr])
            
            
        
        lat1=lat2
        lon1=lon2
        c+=1
    return list_conf


class ScreenDummy:

 	def __init__(self):
 		pass

 	def echo(self, text="", flags = 0):
 		pass

def check_boundaries(traf, center, radius):
	"""
	Check if any aircraft is out of the scenario bounds. It deletes it if so.
	"""
	radius = radius * 1852 # From nm to meters
	id_to_delete = []
	for i in range(traf.ntraf):
		if geo.latlondist(traf.lat[i], traf.lon[i] , center[0], center[1]) > radius:
			id_to_delete.append(traf.id[i])

	if id_to_delete:
		for idx in id_to_delete:
			traf.delete(bs.traf.id.index(idx))

  
def init_at(n_ac,center,radius):

    c = 0
    lat = []
    lon = []
    hdg = []
    
    #print(n_ac1, n_ac2, n_ac3)
    lista =[]
    lista = create_ac(n_ac, radius, center, lista)
    #↨print(r)
    for l in lista:
        lat.append(l[1])
        lon.append(l[2])
        hdg.append(l[3])
    
    #print(lat,lon,hdg)    
    lat = np.array(lat)
    lon = np.array(lon)
    hdg = np.array(hdg)
    g = open('finaldata_4.scn','w') 
    
    while c < n_ac:
        acid = str(c+1)
        
        newline = "00:00:00.00>CRE "+str(acid)+","+"B747"+","+str(lat[c])+","+str(lon[c])+","+str(hdg[c])+","+"30000"+","+"300"+"\n"
        g.write(newline)
        
        bs.traf.cre(acid, actype="B747", aclat=lat[c], aclon=lon[c], acspd=300, achdg=hdg[c])
        c=c+1
        
    g.close()
'''
def readscn(fname):
    Read a scenario file. 
    # Split the incoming filename into a path + filename and an extension
    base, ext = os.path.splitext(fname.replace("\\", "/"))
    if not os.path.isabs(base):
        base = os.path.join(settings.scenario_path, base)
    ext = ext or ".scn"

    # The entire filename, possibly with added path and extension
    fname_full = os.path.normpath(base + ext)

    with open(fname_full, "r") as fscen:
        prevline = ''
        for line in fscen:
            line = line.strip()
            # Skip emtpy lines and comments
            if len(line) < 12 or line[0] == "#":
                continue
            line = prevline + line

            # Check for line continuation
            if line[-1] == '\\':
                prevline = f'{line[:-1].strip()} '
                continue
            prevline = ''

            # Try reading timestamp and command
            try:
                icmdline = line.index(">")
                tstamp = line[:icmdline]
                ttxt = tstamp.strip().split(":")
                ihr = int(ttxt[0]) * 3600.0
                imin = int(ttxt[1]) * 60.0
                xsec = float(ttxt[2])
                cmdtime = ihr + imin + xsec

                yield (cmdtime, line[icmdline + 1:].strip("\n"))
            except (ValueError, IndexError):
                # nice try, we will just ignore this syntax error
                if not (len(line.strip()) > 0 and line.strip()[0] == "#"):
                    print("except this:" + line)

def wpt_lat_lon(wpt_id):
    with open("navaidfinal.dat") as file:
        for line in file:
            data = [data.split() for data in file]
            for i in data:
                if i[0] == wpt_id:
                    return float(i[1]),float(i[2])
def scenario(text):
    with open(text) as file:
        _data_ = json.load(file)
        g = open('Data_CRIDA.scn','w')
        time2 = "08:37:35"
    
        for ac in _data_["trafficInformation"]:
            time1 = (ac['EntryTime'])
            formato = "%H:%M:%S"
            h1 = datetime.strptime(time1, formato)
            h2 = datetime.strptime(time2, formato)
            time = h1 - h2
            
            results = ac['Route']
            ac1 = results[0]
            res = list(ac1.values())
            ac2 = results[1]
            res1 = list(ac2.values())
            ac1_lat, ac1_lon = wpt_lat_lon(res[0])
            ac2_lat, ac2_lon = wpt_lat_lon(res1[0])
            hdg,dnm = geo.qdrdist(ac1_lat, ac1_lon, ac2_lat, ac2_lon)
    
            newline = str(time)+">CRE "+str(ac['Callsign'])+","+str(ac['AircraftModel'])+","+str(ac1_lat)+","+str(ac1_lon)+","+str(hdg)+","+str(ac['EntryLevel'])+"00,"+str(res[2])+"\n"
            print(newline)
            #g.write(newline)
            bs.traf.cre(str(ac['Callsign']), actype=str(ac['AircraftModel']), aclat=float(ac1_lat), aclon=float(ac1_lon), acalt = int(ac['EntryLevel'])+"00",acspd=int(res[2]), achdg=float(hdg))
            
            for i in ac['Route']:
                if res[0] != i['waypoint']:
                    lat,lon = wpt_lat_lon(i['waypoint'])
                    newline = str(time)+">ADDWPT "+str(ac['Callsign'])+","+str(lat)+","+str(lon)+","+str(i['flightlevel'])+"00,"+str(i['speed'])+"\n"
                    #g.write(newline)
                    bs.traf.addwpt(name = str(ac['Callsign']),wplat=float(lat),wplon=float(lon),wpalt=(int(i['flightlevel'])+"00"),wpspd=int(i['speed']))

    
'''
def complexity_simulation(ScreenDummy, center, radius, n_ac, sim_time):
	# Initialize global settings
	#settings.init("")
	# Manually set the performance model to the one defined in the settings before
	#PerfBase.setdefault(settings.performance_model)
	# Init dummy screen
	#bs.scr = ScreenDummy()
	# Manually create singletons

	#traf = tr.Traffic()
	#bs.traf = traf

	#navdb = Navdatabase()
	#bs.navdb = navdb

	#sim = Simulation()
	#bs.sim = sim
    bs.init('sim-detached')

	## We initialize the simulation ##

    bs.sim.simdt=1

    bs.sim.simt=0
    t_max=sim_time #2 hours

    ntraf=bs.traf.ntraf
    n_steps=t_max//bs.sim.simdt+1
    
    t = np.linspace(0, t_max, n_steps)

    
   
    
    bs.stack.simstack.ic(r"C:\Users\Jaume\OneDrive\Desktop\jaume\TFG\bluesky-master\bluesky-master\scenario\case2_b.scn")
    
	
    logger = Logger("type","lat", "lon", dt = 10, name = "COMP_LOGGER")
	
    """ Main loop """
    for i in range(n_steps):

		
        bs.sim.ffmode = True
        bs.sim.dtmult = 1.0
        bs.sim.step()
        bs.net.step()
        logger.log()



		#bs.sim.simt += bs.sim.simdt

		#traf.update()

		
        #if bs.traf.ntraf != 30:
            #(bs.traf.ntraf)

    logger.stop()
    del logger

if __name__ == '__main__':	
    
    complexity_simulation(ScreenDummy, center=(40, -4), radius=300, n_ac=30, sim_time=20*60)

	