import json
from datetime import datetime
import numpy as np
import pickle
from bluesky.tools import geo
from os import path
from weakref import WeakValueDictionary
from numpy import *
import bluesky as bs
from bluesky.tools import geo
from bluesky.core import Replaceable
from bluesky.tools.aero import ft, kts, g0, nm, mach2cas, casormach2tas
from bluesky.tools.misc import degto180, txt2tim, txt2alt, txt2spd
from bluesky.tools.position import txt2pos
from bluesky import stack
from bluesky.stack.cmdparser import Command, command, commandgroup


def wpt_lat_lon(wpt_id):
    with open("navaidfinal.dat") as file:
        for line in file:
            data= [data.split() for data in file]
            for i in data:
                if i[0] == wpt_id:
                    return float(i[1]),float(i[2])

                

text = '19_08_22_H9.json'
with open(text) as file:
    data = json.load(file)
    g = open('Data_CRIDA.scn','w')
    time2 = "08:37:35"

    for ac in data["trafficInformation"]:
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
        g.write(newline)
        #bs.traf.cre(ac['Callsign'], actype=ac['AircraftModel'], aclat=c1_lat, aclon=ac1_lon, acalt = str((ac['EntryLevel'])+"00,"),acspd=res[2], achdg=hdg)
        
        for i in ac['Route']:
            if res[0] != i['waypoint']:
                lat,lon = wpt_lat_lon(i['waypoint'])
                newline = str(time)+">ADDWPT "+str(ac['Callsign'])+","+str(lat)+","+str(lon)+","+str(i['flightlevel'])+"00,"+str(i['speed'])+"\n"
                g.write(newline)
                #bs.traf.addwpt(name = ac['Callsign'],wplat=str(lat),wplon=str(lon),wpalt=(str(i['flightlevel'])+"00"),wpspd=str(i['speed']))

                
        '''
        time1 = (ac['ExitTime'])
        formato = "%H:%M:%S"
        h1 = datetime.strptime(time1, formato)
        h2 = datetime.strptime(time2, formato)
        time = h1 - h2
        newline = str(time)+'>DEL '+str(ac['Callsign'])+"\n"
        g.write(newline)
        '''