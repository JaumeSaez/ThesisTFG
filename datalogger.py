import csv
import os
from tkinter import INSIDE
import numpy as np 
import datetime as datetime
import bluesky as bs
from bluesky.core import varexplorer as ve
from bluesky.traffic.asas import detection
import networkx as nx
from bluesky import traffic
from bluesky.tools import geo, areafilter
from bluesky.tools.aero import vcasormach, nm, casormach2tas, tas2cas, ft
#from sector_LECM import Sector
dintre = []
class Logger():
	"""
	Data logger class

	Methods:
	-__create_fname(): Generate the name of the logged file
	--------

	"""

	def __init__(self, *variables, dt: float, name: str = ",", aircrafts_id: str = None):
	
		self.dt = dt
		self.variables = [variable for variable in variables]
        
        
		self.name = name
		self.tlog = 0

		if aircrafts_id:
			self.aircrafts_id = aircrafts_id  
			self.id_dynamic = False

		else:
			self.aircrafts_id = bs.traf.id
			self.id_dynamic = True

		# checks if any acid or variable does not exists
		for aircraft_id in self.aircrafts_id:

			if aircraft_id not in bs.traf.id:
				raise ValueError(f"The aircraft {aircraft_id} does not exist") 

		self.__create_directory()
		
		fname = self.__create_fname()
		self.__open_file(fname)
		

	def __update_acids(self):
		self.aircrafts_id = bs.traf.id


	def __create_fname(self) -> str:
		"""
		Generate the name of the logged file with the format: "name_yyymmdd_hh-mm-ss.csv" 
		where name referes to the constructor argument "name"
		"""

		timestamp = datetime.datetime.now().strftime('%Y%m%d_%H-%M-%S')
		fname = self.name + "_" + timestamp + ".csv"

		return fname

	def __open_file(self, fname):
		"""
		Create and open the output file with the created name and create the csv_writer object
		"""
		self.file = open(self.directory_path + "/" + fname, "w", newline = "")

		col_header = "time , aircraft_id "
		for variable in self.variables:
			col_header += "," + variable

		#col_header += "conflict_pairs compound_conflicts"
		col_header += "\n"

		self.file.write(col_header)

		self.csv_writer = csv.writer(self.file)

	def __close_file(self):
		"""
		Close the output file
		"""
		self.file.close()

	def __create_directory(self):
		"""
		Create a folder to store the output file and returns its path
		"""
		if self.name:
			self.directory_path = "./" + self.name + "_output"

		else:
			self.directory_path = "./" + "output"

		if(not os.path.isdir(self.directory_path)):
			os.mkdir(self.directory_path)

	def detect(self, ownship, intruder, rpz, hpz, dtlookahead):
		''' Conflict detection between ownship (traf) and intruder (traf/adsb).'''
		# Identity matrix of order ntraf: avoid ownship-ownship detected conflicts
		#print("estoy aquí")
		I = np.eye(ownship.ntraf)

        # Horizontal conflict ------------------------------------------------------

        # qdrlst is for [i,j] qdr from i to j, from perception of ADSB and own coordinates
		qdr, dist = geo.kwikqdrdist_matrix(np.asmatrix(ownship.lat), np.asmatrix(ownship.lon),
		                       	np.asmatrix(intruder.lat), np.asmatrix(intruder.lon))

		# Convert back to array to allow element-wise array multiplications later on
		# Convert to meters and add large value to own/own pairs
		qdr = np.asarray(qdr)
		dist = np.asarray(dist) * nm + 1e9 * I
		#print(qdr)
		#print(dist)
        
		# Calculate horizontal closest point of approach (CPA)
		qdrrad = np.radians(qdr)
		dx = dist * np.sin(qdrrad)  # is pos j rel to i
		dy = dist * np.cos(qdrrad)  # is pos j rel to i

		# Ownship track angle and speed
		owntrkrad = np.radians(ownship.trk)
		ownu = ownship.gs * np.sin(owntrkrad).reshape((1, ownship.ntraf))  # m/s
		ownv = ownship.gs * np.cos(owntrkrad).reshape((1, ownship.ntraf))  # m/s

		# Intruder track angle and speed
		inttrkrad = np.radians(intruder.trk)
		intu = intruder.gs * np.sin(inttrkrad).reshape((1, ownship.ntraf))  # m/s
		intv = intruder.gs * np.cos(inttrkrad).reshape((1, ownship.ntraf))  # m/s

		du = ownu - intu.T  # Speed du[i,j] is perceived eastern speed of i to j
		dv = ownv - intv.T  # Speed dv[i,j] is perceived northern speed of i to j

		dv2 = du * du + dv * dv
		dv2 = np.where(np.abs(dv2) < 1e-6, 1e-6, dv2)  # limit lower absolute value
		vrel = np.sqrt(dv2)

		tcpa = -(du * dx + dv * dy) / dv2 + 1e9 * I

		# Calculate distance^2 at CPA (minimum distance^2)
		dcpa2 = np.abs(dist * dist - tcpa * tcpa * dv2)

		# Check for horizontal conflict
		# RPZ can differ per aircraft, get the largest value per aircraft pair
		rpz = np.asarray(np.maximum(np.asmatrix(rpz), np.asmatrix(rpz).transpose()))
		R2 = rpz * rpz
		swhorconf = dcpa2 < R2  # conflict or not

		# Calculate times of entering and leaving horizontal conflict
		dxinhor = np.sqrt(np.maximum(0., R2 - dcpa2))  # half the distance travelled inzide zone
		dtinhor = dxinhor / vrel

		tinhor = np.where(swhorconf, tcpa - dtinhor, 1e8)  # Set very large if no conf
		touthor = np.where(swhorconf, tcpa + dtinhor, -1e8)  # set very large if no conf

		# Vertical conflict --------------------------------------------------------

		# Vertical crossing of disk (-dh,+dh)
		dalt = ownship.alt.reshape((1, ownship.ntraf)) - \
		intruder.alt.reshape((1, ownship.ntraf)).T  + 1e9 * I

		dvs = ownship.vs.reshape(1, ownship.ntraf) - \
		intruder.vs.reshape(1, ownship.ntraf).T
		dvs = np.where(np.abs(dvs) < 1e-6, 1e-6, dvs)  # prevent division by zero

		# Check for passing through each others zone
		# hPZ can differ per aircraft, get the largest value per aircraft pair
		hpz = np.asarray(np.maximum(np.asmatrix(hpz), np.asmatrix(hpz).transpose()))
		tcrosshi = (dalt + hpz) / -dvs
		tcrosslo = (dalt - hpz) / -dvs
		tinver = np.minimum(tcrosshi, tcrosslo)
		toutver = np.maximum(tcrosshi, tcrosslo)

		# Combine vertical and horizontal conflict----------------------------------
		tinconf = np.maximum(tinver, tinhor)
		toutconf = np.minimum(toutver, touthor)

		swconfl = np.array(swhorconf * (tinconf <= toutconf) * (toutconf > 0.0) *
		               np.asarray(tinconf < np.asmatrix(dtlookahead).T) * (1.0 - I), dtype=np.bool)

		# --------------------------------------------------------------------------
		# Update conflict lists
		# --------------------------------------------------------------------------
		# Ownship conflict flag and max tCPA
		inconf = np.any(swconfl, 1)

		try:
			tcpamax = np.max(tcpa * swconfl, 1)
		except ValueError:
			tcpamax = 0

		# Select conflicting pairs: each a/c gets their own record
		confpairs = [(ownship.id[i], ownship.id[j]) for i, j in zip(*np.where(swconfl))]
		swlos = (dist < rpz) * (np.abs(dalt) < hpz)
		lospairs = [(ownship.id[i], ownship.id[j]) for i, j in zip(*np.where(swlos))]
		#print(confpairs)
		#print(lospairs)

		return confpairs, lospairs, inconf, tcpamax, \
		qdr[swconfl], dist[swconfl], np.sqrt(dcpa2[swconfl]), \
		    tcpa[swconfl], tinconf[swconfl]


	def __comp_conf(self, conf_pairs):
		"""
		Return a list with all compound conficts
		"""
		g = nx.Graph()
		g.add_nodes_from(self.aircrafts_id)

		for pair in conf_pairs:
			g.add_edge(pair[0], pair[1])

		if conf_pairs:
			d = list(nx.connected_components(g))
			#print("hi")
			return d
		#print("no hi")
		return []

	def __extract_data(self):
		"""
		Returns the current data generated by the simulation
		for the specified variables and aircrafts
		"""
		# update aircraft ids
		if self.id_dynamic:
			self.__update_acids()
		#print(self.__update_acids())

		aircraft_data = []
		
		Sector = ([43.7194442749023,-2.16583347320557,43.6833343505859,-2.06666660308838,
43.6672248840332,-2.02138876914978,43.6463890075684,-1.96250009536743,43.5833320617676,
-1.78333330154419,43.4316673278809,-1.78416669368744,43.3833351135254,-1.78333330154419,
43.3549995422363,-1.7402777671814,43.3138885498047,-1.72111117839813,43.2908325195312,
-1.61805558204651,43.2633323669434,-1.5797221660614,43.2919425964355,-1.51361107826233,
43.2838897705078,-1.4913889169693,43.2874984741211,-1.46666669845581,43.0816650390625,
-1.47000002861023,43.0499992370605,-1.33333337306976,43.0091667175293,-1.10805559158325,
42.9727783203125,-0.97916662693024,42.9319458007812,-0.84444445371628,42.8963890075684,
-0.72777777910233,42.8772201538086,-0.67916667461395,42.875,-0.65694439411163,42.823055267334,
-0.48111110925674,42.7522239685059,-0.99777781963348,42.4599990844727,-1.24583339691162,41.3819427490234,
-2.1358335018158,41.0347213745117,-2.4219446182251,41.033332824707,-2.5,41.033332824707,-2.83333325386047,41.3030548095703,-2.8486111164093,40.9944458007812,-3.51111102104187,40.9330558776855,-3.64111089706421,
40.9949989318848,-3.83527779579163,41.0611114501953,-4.04527759552002,41.2216682434082,-4.5527777671814,
41.2641677856445,-4.68694448471069,41.3708305358887,-4.65750026702881,42.1363906860352,-4.43249988555908,
42.3333320617676,-4.375,42.3513870239258,-4.93916654586792,42.3705520629883,-5.67749977111816,
42.9655570983887,-5.25833320617676,43.404167175293,-4.94500017166138,44.3758316040039,-4.23138904571533,
44.3330535888672,-4,44.2658348083496,-3.79250001907349,44.0513877868652,-3.15027785301209,43.9486122131348,
-2.84027767181397,43.9141693115234,-2.73861122131348,43.9000015258789,-2.69861125946045,43.8388862609863
,-2.51944446563721,43.7194442749023,-2.16583347320557])

		areafilter.defineArea('Sector_CRIDA', 'POLY',Sector)
		#inside = areafilter.checkInside('Sector', bs.traf.lat, bs.traf.lon)
		#dintre.append(inside)
		#print(dintre)
		
		if areafilter.hasArea('Sector_CRIDA'):
			ownship = bs.traf
			inside = areafilter.checkInside('Sector_CRIDA', ownship.lat, ownship.lon,ownship.alt)

			#print(ownship.id,inside)
			
		index = 0
		b = []
		for i in inside:
			if i ==True:
				b.append(index)
			index +=1
		#print(b)
		#for idx in sorted(b, reverse = True):
			#del ownship.idd[idx]
		#print(ownship.id)
		for variable in self.variables:
			
			try:
				aircraft_data.append(getattr(bs.traf, variable))

			except AttributeError:
				print(f"The variable {variable} does not exist")
				#exit()
		
                

		# Extract conflict pairs and add them to each record
		#conf_pairs = self.detect(ownship = bs.traf, intruder = bs.traf, rpz = 0.12959, hpz = 1, dtlookahead = 15)[0]
		
		#conf_data = [len(conf_pairs)/2 for _ in range(len(self.aircrafts_id))]
		
		
			
		#aircraft_data.append(conf_data)

		# Compute compound conflict and add them to the records

		#comp_confs = self.__comp_conf(conf_pairs)
		#comp_confs = [conf for conf in comp_confs if len(conf) > 1]
		
		#comp_data = [len(comp_confs) for _ in range(len(self.aircrafts_id))]


		#aircraft_data.append(comp_data)

		return aircraft_data,b

	def log(self):
		"""
		Writes data in the csv file
		"""
		if self.file and bs.sim.simt >= self.tlog:
			# Extract the data 
			self.__extract_data()

			# Increment the tlog for the next iteration
			self.tlog += self.dt

			# Create the new row to log and log it
			new_data,lista = self.__extract_data()

			#print(new_data[0],new_data[1],new_data[2])
			#for idx in sorted(lista, reverse = True):
				#del aircraft_id[idx]
			#print(inside,aircraft_data)
			
			for aircraft_id in self.aircrafts_id:

				aircraft_index = self.aircrafts_id.index(aircraft_id)
				if aircraft_index in lista:
				#print(lista)
				#for idx in sorted(lista, reverse = True):
					#del aircraft_index[idx]
				#print(aircraft_index)

					new_row = [bs.sim.simt, aircraft_id]
					[new_row.append(new_data[i][aircraft_index]) for i, val in enumerate(new_data)]

					self.csv_writer.writerow(new_row)
	
	def stop(self):
		"""
		Close the file and reset some atributtes
		"""
		self.__close_file()
		self.tlog = 0

