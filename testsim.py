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

            
def init_at(n_ac):


	c=0
	lat = [60.40897167983416,59.57525990982919,60.00000000000000,46.04697135433401,48.88922174240424,54.121162723303954,60.83724689614433]
	lon = [31.462639470088053,31.42623834789694,30.00000000000000,31.974454048718737,36.179884293737025,28.99213207956443,32.10480959860338]
	heading = [-150,-30,90,-28.802249443672203,-98.79351176442376,131.61686166084806,85.99336082202467]
	while c<n_ac:
		acid = str(c+1)
		bs.traf.cre(acid, actype="B747", aclat=lat[c], aclon=lon[c], acspd=300, achdg=heading[c])
		c=c+1
    

def complexity_simulation(ScreenDummy, center, radius, n_ac, sim_time, n_sources):
	# Initialize global settings
	settings.init("")
	# Manually set the performance model to the one defined in the settings before
	PerfBase.setdefault(settings.performance_model)
	# Init dummy screen
	bs.scr = ScreenDummy()
	# Manually create singletons

	traf = tr.Traffic()
	bs.traf = traf

	navdb = Navdatabase()
	bs.navdb = navdb

	sim = Simulation()
	bs.sim = sim


	## We initialize the simulation ##

	bs.sim.simdt = 1
	bs.sim.simt = 0
	t_max = sim_time #15 mins

	ntraf = traf.ntraf
	n_steps = t_max//bs.sim.simdt + 1
	t = np.linspace(0, t_max, n_steps)


	init_at(n_ac)
    
    
    
	
	logger = Logger("type","lat", "lon", dt = 10, name = "COMP_LOGGER")
	
	""" Main loop """
	for i in range(n_steps):

		
		logger.log()
		
		""" Check if the acs are out of bounds and delete them if so """
		check_boundaries(traf, center, radius)

		""" Spawning aircrafts in the sources """
		#if bs.traf.ntraf < n_ac:
			#spawn_ac(sources_position, radius, center, number_of_aircrafts = n_ac - bs.traf.ntraf)


		bs.sim.simt += bs.sim.simdt

		traf.update()
		
		if bs.traf.ntraf != 7:
			print(bs.traf.ntraf)

	logger.stop()
	del logger

if __name__ == '__main__':
	complexity_simulation(ScreenDummy, center=(60, 30), radius=1000, n_ac=7, sim_time=15 * 60, n_sources=100)

	