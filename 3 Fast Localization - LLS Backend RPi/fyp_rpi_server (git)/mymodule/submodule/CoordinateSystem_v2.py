"""
# Modified from: LAM KA HO (2017-2018):/Simulation.Mphil/GPS2XY/CoordinateSystem.py
# Last Modified: 10th Feb 2020
# Modified by: Sing (2019-2020)

Functions of this program::
1) Set an origin of the x-y coordinate system map, inputs are the GPS (lat, lng)
2) Convertion between GPS (lat, lng) and x-y coordinate (x,y) based on the origin
"""

import math

#Not useful
# class CoordinateSystem:
# 	#Set the origin of the x-y coordinate, input = GPS(lat,lng)
# 	def __init__(self,origin):
# 		self.origin = origin
# 		self.origin.x = 0
# 		self.origin.y = 0
	
# 	#Convert BS GPS to (x,y)
# 	def setStations(self,locations):
# 		self.stations = locations
# 		for station in self.stations:
# 			station.convertGPS2XY(self.origin)
	
# 	#Unknown
# 	def setReferencePoint(self,refPoint):
# 		self.referencePoint = refPoint
# 		self.referencePoint.convertGPS2XY(self.origin)
		
class Location:
	"""
	Initialize this class also set the origin of the coordinate system at the same time.
	
	Example:
	----------
	# Set the origin
	> origin = this_file_name.Location(origin_lat, origin_lng)
	"""
	# Assign object attributes
    # ------------------------
	D2R = (math.pi / 180.0)	#Degree to radians
	R = 6367000				#Earth radius in meters
	x = float
	y = float

	"""
	 originlat - y ; originlng - x
	 originlat	equivalent to Y
	 originlng 	equivalent to X
	"""

	def __init__(self,originlat=float,originlng=float):
		self.longitude = originlng
		self.latitude = originlat
	
	"""=================== 'class Location' By Ka Ho <BEGIN> =============================================="""
	
	# def setXY(self,x,y):
	# 	self.x = x
	# 	self.y = y
		
	#Calculate distance between 2 points based on GPS (lat, lng)
	# def distanceGPS(self,l):
	# 	dlong = (self.longitude - l.longitude) *self.D2R
	# 	dlat = (self.latitude - l.latitude) *self.D2R
	# 	a = math.pow(math.sin(dlat / 2.0), 2.0) + (math.cos(l.latitude *self.D2R) * math.cos(self.latitude *self.D2R) * math.pow(math.sin(dlong / 2.0), 2.0))
	# 	c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
	# 	d =self.R * c
	# 	return d
		
	#Not useful
	# def distance(self,l):
	# 	d = math.sqrt(math.pow(self.x-l.x,2) + math.pow(self.y-l.y, 2))
	# 	return d
	
	#Not useful
	# def distanceX(self,l):
	# 	"""Calculate coordinate x based on GPS (lat, lng)"""

	# 	dlong = (self.longitude - l.longitude) *self.D2R
	# 	dlat = (self.latitude - self.latitude) *self.D2R
	# 	a = math.pow(math.sin(dlat/2.0), 2.0) + math.cos(self.latitude*self.D2R) * math.cos(self.latitude*self.D2R) * math.pow(math.sin(dlong/2.0), 2.0)
	# 	c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
	# 	d =self.R * c

	# 	#System.out.println("distanceX")
	# 	#System.out.println(math.cos(l.latitude*self.D2R) * math.cos(latitude*self.D2R) * math.pow(math.sin(dlong/2.0d), 2))
	# 	#System.out.println(String.format("dLon: %f  a: %f  c: %f  d: %f  g: %f", dlong,a,c,d,math.pow(math.tan(2.0d*c), 2)))
	# 	return d
	
	#Not useful
	# def distanceY(self,l):
	# 	"""Calculate coordinate y based on GPS (lat, lng)"""

	# 	dlong = (self.longitude - self.longitude) *self.D2R
	# 	dlat = (self.latitude - l.latitude) *self.D2R
	# 	a = math.pow(math.sin(dlat/2.0), 2.0) + math.cos(l.latitude*self.D2R) * math.cos(self.latitude*self.D2R) * math.pow(math.sin(dlong/2.0), 2.0)
	# 	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	# 	d =self.R * c

	# 	# System.out.println("distanceY")
	# 	# System.out.println(math.cos(l.latitude*self.D2R) * math.cos(latitude*self.D2R) * math.pow(math.sin(dlong/2.0d), 2))
	# 	# System.out.println(String.format("dLat: %f  a: %f  c: %f  d: %f", dlat,a,c,d))
	# 	return d
		
	# def convertGPS2XY(self,origin):
	# 	""" Sing thinks this func is difficult to use. See new convertGPS2XY_v2() below. """

	# 	self.x = self.distanceX(origin)
	# 	self.y = self.distanceY(origin)

	def convertXY2GPS(self, dX=float, dY=float):
		"""
		Convert the (x,y) to GPS. Returns the object attributes .x and .y in this class.
		
		Must set the  origin first.
		
		Example: Set the origin and convert (x,y) coordinate to GPS.
		----------
		1st	# Set the origin
			origin = this_file_name.Location(origin_lat, origin_lng) 

		2nd	# Converts (x,y) to GPS
			gps = origin.convertXY2GPS(x,y)
			
		3rd	# Get the converted result
			lat = gps.latitude
			lat = gos.longitude
		"""

		c = dY/self.R
		g = math.pow(math.tan(c/2.0), 2.0)
		
		a = g/(1+g)
		dlat = math.asin(math.sqrt(a))*2.0
		
		lat = (dlat/self.D2R) + self.latitude
		
		c = dX/self.R
		g = math.pow(math.tan(c/2.0), 2)
		
		a = g/(1+g)
		F = math.cos(self.latitude*self.D2R)*math.cos(self.latitude*self.D2R)
		if(F < 0):
			print("convertXY2GPS: F<0")
			return Location(0,0)
		
		dlon = 2.0*math.asin(math.sqrt(a/F))
		
		lng = (dlon/self.D2R) + self.longitude
		
		return Location(lat,lng)
		
	# def __repr__(self):
	# 	return ("Lat:%11.6f Lng:%10.6f\n  X:%11.6f   Y:%10.6f" % (latitude,longitude,x,y) )
		
	""" =================== 'class Location' By Ka Ho <END> =============================================="""


	""" ############# 'class Location' By Sing <BEGIN> ############# """

	def distanceX_v2(self, lat=float, lng=float):
		"""
		unit: meter(s), type: float, Calculate horizontal distance from origin based on GPS (lat, lng)
		OR Calculate x coordinate of the GPS based on given origin.
		Returns the distance.

		Must set the  origin first.
		
		Example: Set the origin and convert (x,y) coordinate to GPS.
		----------
		1st	# Set the origin
			origin = this_file_name.Location(origin_lat, origin_lng)
		
		2nd	# Return the distance in float
			xdistance = origin.distanceX_v2(lat=lat_val, lng=lng_val)
		"""

		dlong = (self.longitude - lng) *self.D2R
		dlat = (self.latitude - self.latitude) *self.D2R
		a = math.pow(math.sin(dlat/2.0), 2.0) + math.cos(self.latitude*self.D2R) * math.cos(self.latitude*self.D2R) * math.pow(math.sin(dlong/2.0), 2.0)
		c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
		d =self.R * c
		return d

	def distanceY_v2(self, lat=float, lng=float):
		"""
		unit: meter(s), type: float, Calculate the vertical distance (y coordinate) from origin based on GPS (lat, lng)
		OR Calculate y coordinate of the GPS based on given origin.
		Returns the distance.

		Must set the  origin first.
		
		Example: Set the origin and convert (x,y) coordinate to GPS.
		----------
		1st	# Set the origin
			origin = this_file_name.Location(origin_lat, origin_lng)
		
		2nd	# Return the distance in float
			ydistance = origin.distancey_v2(lat=lat_val, lng=lng_val)
		"""

		dlong = (self.longitude - self.longitude) *self.D2R
		dlat = (self.latitude - lat) *self.D2R
		a = math.pow(math.sin(dlat/2.0), 2.0) + math.cos(lat*self.D2R) * math.cos(self.latitude*self.D2R) * math.pow(math.sin(dlong/2.0), 2.0)
		c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
		d =self.R * c
		return d

	def distance_btw2xy(self, x1=float, y1=float, x2=float, y2=float):
		"""
		unit: meter(s), type: float, Calculate the distance between two (x,y) points.
		Returns the distance.

		Must set the  origin first.
		
		Example: Set the origin and convert (x,y) coordinate to GPS.
		----------
		1st	# Set the origin
			origin = this_file_name.Location(origin_lat, origin_lng)
		
		2nd	# Return the distance in float
			distance = origin.distance_btw2xy(lat=lat_val, lng=lng_val)
		"""
		d = math.sqrt(math.pow(x1-x2,2) + math.pow(y1-y2, 2))
		return d

	def convertGPS2XY_v2(self, lat=float, lng=float) -> dict:
		"""
		Convert GPS (latitude, longitude) to (x,y) based on origin. Returns (x,y) as a dict.
		
		Example
		----------
		1st	# Set the origin
			origin = this_file_name.Location(origin_lat, origin_lng)

		2nd	# Converts GPS to (x,y)
			xy = origin.convertGPS2XY_v2(lat,lng)

		3rd	# Get the converted result
			# xy = dict {'x': x, 'y': y}
		"""
		self.x = self.distanceX_v2(lat, lng)
		self.y = self.distanceY_v2(lat,lng)
		return {'x': self.x, 'y': self.y}

	def distance_btw2gps(self, lat1=float, lng1=float, lat2=float, lng2=float):
		"""
		Calculate the distance bewteen two GPS locations.
		
		unit: meter(s), type: float. Return a float.
		
		Must set the  origin first.

		Function illustration
		----------
		1st Convert two GPS to (x,y) coordinates based on the origin set before.
		2nd Calculate the distance bewteeb two (x,y).
		3rd Return the distance (float).

		Example
		----------
		1st	# Set the origin
			origin = this_file_name.Location(origin_lat, origin_lng)
		2nd	distance = distance_btw2gps(lat1=lat_val1, lng1=lng_val1, lat2=lat_val2, lng2=lng_val2)
		"""

		#1st Convert GPS to (x,y)
		xy1 = self.convertGPS2XY_v2(lat1, lng1)
		xy2 = self.convertGPS2XY_v2(lat2, lng2)
		
		#2nd Find distance between two points
		distance = self.distance_btw2xy(x1=xy1['x'], y1=xy1['y'], x2=xy2['x'], y2=xy2['y'])
		
		return distance

	""" ############# 'class Location' By Sing <END> ############# """

""" Method by Ka Ho <BEGIN> """
# def test():
# 	##Origin of X-Y coordinate system: Tai a Chau Landing No. 2, 大鴉洲2號梯台
# 	#22.167615, 113.908514
# 	origin = Location(22.167615, 113.908514)  
# 	sys = CoordinateSystem(origin)
		
# 	#22.289719, 114.145529
# 	#A list that contains a class 'Location'
# 	stations = []
# 	stations.append(Location(22.289666,114.145099))
# 	stations.append(Location(22.289558,114.145130))
# 	stations.append(Location(22.289414,114.145246))
# 	sys.setStations(stations)
	
# 	print()
# 	for an in stations:
# 		print(str(an.latitude) + ',' +str(an.longitude))
# 		print("%f\t%f\t%f" % ( origin.distanceX(an),origin.distanceY(an),origin.distance(an) ) )
# 	print()
""" Method by Ka Ho <END> """

""" ######## By Sing <BEGIN> ######## """
def demo_xy2gps(originlat=float, originlng=float, x=float, y=float):
	xy = Location(originlat,originlng).convertXY2GPS(x,y)
	print(xy.latitude)
	print(xy.longitude)

#2020.02.10
#Show the difference between the Ka Ho func and Sing func
def test2():
	origin_lat = 22.167615
	origin_lng = 113.908514
	lat = 22.289666
	lng = 114.145099

	print('\n====== Ka Ho - GPS (lat,lng) to (x,y) ======')
	x = Location(22.167615, 113.908514).distanceX(Location(lat,lng))  #Two ways but with same effect
	y = Location(origin_lat, origin_lng).distanceY(Location(lat,lng)) #
	print('GPS lat:\t{0:f}'.format(lat))
	print('GPS lng:\t{0:f}'.format(lng))
	print('converted xy x:\t{0:f}'.format(x))
	print('converted xy y:\t{0:f}'.format(y))

	print('\n====== Sing - GPS (lat,lng) to (x,y) ======')
	#1st way to convert GPS to xy coordinate
	x = Location(originlat=origin_lat, originlng=origin_lng).distanceX_v2(lat=22.289666,lng=114.145099)
	y = Location(origin_lat, origin_lng).distanceY_v2(22.289666,114.145099)
	#2nd way to convert GPS to xy coordinate
	xy = Location(originlng=origin_lat, originlat=origin_lng).convertGPS2XY_v2(lat=22.289666,lng=114.145099)
	print('GPS lat:\t{0:f}'.format(lat))
	print('GPS lng:\t{0:f}'.format(lng))
	print('converted x:\t{0:f}'.format(x))
	print('converted y:\t{0:f}'.format(y))
	print('converted xy:\t{0}'.format(xy))

	print('\n====== Sing - Distance between two xy/GPS ======')
	coordsys = Location(22.167615, 113.908514)
	xy1 = {'x':0,'y':0}
	xy2 = {'x':1,'y':1}
	xy_distance = coordsys.distance_btw2xy(x1=xy1['x'],y1=xy1['y'], x2=xy2['x'],y2=xy2['y'])

	print('xy1:\t\t{0},{1}'.format(xy1['x'],xy1['y']))
	print('xy2:\t\t{0},{1}'.format(xy2['x'],xy2['y']))
	print('xy dist:\t{0}'.format(xy_distance))

	gps1 = {'lat':22.293210, 'lng':114.172877}
	gps2 = {'lat':22.293025, 'lng':114.173606}
	gps_distance = coordsys.distance_btw2gps(lat1=gps1['lat'], lng1=gps1['lng'], lat2=gps2['lat'], lng2=gps2['lng'])
	print()
	print('gps1:\t\t{0:f}, {1:f}'.format(gps1['lat'], gps1['lng']))
	print('gps2:\t\t{0:f}, {1:f}'.format(gps2['lat'], gps2['lng']))
	print('gps dist:\t{0}'.format(gps_distance))
	print()


# test()
# test2()
# demo_xy2gps(originlat=22.167615, originlng=113.908514, x=24347.241376, y=13562.931225)

""" ######## By Sing <END> ######## """