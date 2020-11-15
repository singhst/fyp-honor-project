"""
# Modified from: Sham Yik Yee (2018-19): /Sigfox vs LoRa/FYP/myLLS.py
# Last Modified: 28th Feburary 2020
# Modified by: Sing (2019-2020)
# Description: 

Functions::
Perform Linear Least Squared LLS localization algorithm to find
1. estimated target location (theta, list[x, y, x^2+y^2])
2. location error (distance between real location and LLS estimated location)
3. the distance between the LLS estimated target location and each base station
"""


""" ======== import module <BEGIN> ======== """
import numpy
import math
# from myMBREC import MBRE
""" ======== import module <END> ======== """

""" ======== import self module <BEGIN> ======== """
#Import module by two ways. Take the below link as reference
# ==> https://stackoverflow.com/questions/8718885/import-module-from-string-variable
err_1 = err_2 = str()
try: #For external use in the outside .py
	from mymodule.submodule import CoordinateSystem_v2 as myCoordinateSystem
except:# ModuleNotFoundError as err:
    pass
##    err_1 = str(err)
try: #For internal testing in this module 
	from submodule import CoordinateSystem_v2 as myCoordinateSystem
except: #ModuleNotFoundError as err:
    pass
##    err_2 = str(err)
#Check whether the self-module imported successfully or not
if (err_1 and err_2):
	#unsuccessful, tell users if the self-module cannot be imported
    print("\nUnsuccessful to import self-module 'CoordinateSystem_v2.py'.")
    print("The name or the path of the module may be changed.")
    print("Check whether the following path and file exists or not, or whether the file name is correct or not,")
    print("  >  ~/rssi_stat_analysis/mymodule/submodule/CoordinateSystem_v2.py")
    print("\nError code: \t{0}\n\t\t{1}".format(err_1,err_2))
##else:
##	#successful importation
##    print("\nSuccessful to import self-module 'CoordinateSystem_v2.py' under ~/rssi_stat_analysis/mymodule/submodule/CoordinateSystem_v2.py")
##    print("Way to import:")
##    if err_2:
##        print("External use >\tfrom mymodule.submodule import CoordinateSystem_v2 as myCoordinateSystem\n")
##    if err_1:
##        print("Internal use >\tfrom submodule import CoordinateSystem_v2 as myCoordinateSystem\n")
""" ======== import self module <END> ======== """


class LLS(object):
	'''
	Just need to input either the GPS(lat.lng) OR (x,y) of the BS.\n
	alpha: type `float`	\n
	Z0: type `float`	\n
	originLat: type `float`, default value = 22.167615. The GPS latitude of the origin. \
		    Origin of X-Y coordinate system: GPS(22.167615, 113.908514), Tai a Chau Landing No. 2, 大鴉洲2號梯台	\n
	originLng: type `float`, default value = 113.908514. The GPS longitude of the origin. \
		    Origin of X-Y coordinate system: GPS(22.167615, 113.908514), Tai a Chau Landing No. 2, 大鴉洲2號梯台	\n	bsCoordinateX: type `list`, `float` inside. The x coordinates of the base stations. The sequence of the x coords must be same as the y coords.
	 e.g. bsCoordinateX 
	 \t= [uint(bs1_x_coordinate), uint(bs2_x_coordinate), ...] 
	 \t= [12322, 32424, 12312,...]
	bsCoordinateY: type `list`, `float` inside. The y coordinates of the base stations. The sequence of the x coords must be same as the y coords.
	 e.g. bsCoordinateY 
	 \t= [uint(bs1_y_coordinate), uint(bs2_y_coordinate), ...] 
	 \t= [6523, 2342, 5433,...]
	bsCoordinateLat: type `list`, `float` inside. The GPS latitude the base stations. The sequence of the x coords must be same as the y coords.
	 e.g. bsCoordinateLat 
	 \t= [uint(bs1_lat), uint(bs2_lat), ...] 
	 \t= [22.123, 22.5323, 22.765,...]
	bsCoordinateLng: type `list`, `float` inside. The GPS longitude of the base stations. The sequence of the x coords must be same as the y coords.
	 e.g. bsCoordinateLng 
	 \t= [uint(bs1_lng), uint(bs2_lng), ...] 
	 \t= [114.534, 114.234, 114.7567,...]
	measuredRssi: type `list`, `float` inside. The measured RSSI values of the base stations. The sequence of the RSSI values must be the same as the BS coordinates.
	 e.g. measuredRssi 
	 \t= [int(bs1_rssi), int(bs2_rssi), ...] 
	 \t= [-113, -98, -87, ...]
	targetRealCoordinate: type `list`, `float` inside. The converted (x,y) coordinate of the actual device location, based on GPS.
	 e.g. targetRealCoordinate 
	 \t= [float(target_x_coor), float(target_y_coor)] 
	 \t= [1231, 2343]
	targetRealGPS: type `list`, `float` inside. The GPS of the actual device location.
	 e.g. targetRealGPS 
	 \t= [float(target_lat), float(target_lng)] 
	 \t= [22.300567, 114.178874]
	'''
	alpha = float()	#path loss exponent, ideal_alpha = 2.449320295			## From Leung Ki Fung (2018-2019):/Sigfox localization/Final_Analysis/Analysis.py
	Z0 = float()	#reference RSSI, ideal_Reference_RSSI = -36.15657229	##
	originLat = 22.167615
	originLng = 113.908514
	bsCoordinateX = list()	#(x, y) coordinates of the base stations, which measure RSSI
	bsCoordinateY = list()	#
	measuredRssi = list()	#RSSI values measured by base stations
	targetRealCoordinate = list()  #the converted (x,y) coordinate of the actual device location, based on GPS

	def __init__(self,alpha=2.5,Z0=-33.0,
				originLat=22.167615,originLng=113.908514,
				bsCoordinateX=None,bsCoordinateY=None, 
				bsCoordinateLat=None,bsCoordinateLng=None,measuredRssi=list,
				targetRealCoordinate=None,targetRealGPS=None):
		self.alpha = alpha
		self.Z0 = Z0
		self.bsCoordinateX = bsCoordinateX
		self.bsCoordinateY = bsCoordinateY
		self.bsCoordinateLat = bsCoordinateLat
		self.bsCoordinateLng = bsCoordinateLng
		self.measuredRssi = measuredRssi
		self.targetRealCoordinate = targetRealCoordinate
		self.targetRealGPS = targetRealGPS

	def matrixA(self): #pass a list of coordinates to the matrix A
		bs_x = self.bsCoordinateX
		bs_y = self.bsCoordinateY
		a = []
		# sp_coor = []
		# sp_coor = bsCoordinate.split(";")  #["x1,y1"]--list ele1 ["x2,y2"]--list ele2...so on
		for i in range(len(bs_x)):
			# aa = []
			# splited = sp_coor[i]     #for i = 1 handle the 1st ele ,["x1,y1"]-->[x1]--list ele1 [x2]--list ele2
			# aa = splited.split(",")
			##By Ka Ho report, p.15, equation (2.16)
			aaa = []
			aaa.append(-2.0*float(bs_x[i]))
			aaa.append(-2.0*float(bs_y[i]))
			aaa.append(1)
			a.append(aaa)
		a = numpy.matrix(a)
		return a

	def matrixB(self):
		Z0 = self.Z0
		alpha = self.alpha
		m_rssi = self.measuredRssi
		bs_x = self.bsCoordinateX
		bs_y = self.bsCoordinateY
		# m_rssi = []
		# m_rssi = measuredRssi.split(",")
		# sp_coor = []
		# sp_coor = bsCoordinate.split(";")
		b = []
		for i in range(len(m_rssi)):
			# aa = []
			# splited = sp_coor[i]     #for i = 1 handle the 1st ele ,["x1,y1"]-->[x1]--list ele1 [x2]--list ele2
			# aa = splited.split(",")  # aa's length is the same as m_rssi[]
			temp = (2/(10*alpha))*(Z0-float(m_rssi[i])) #m_rssi = splited measured rssi in the form of [rssi1,rssi2...]
			temp = pow(10,temp)
			temp = temp - pow(float(bs_x[i]),2) - pow(float(bs_y[i]),2)
			b.append(temp)
		b = numpy.matrix(b).T
		return b

	def Agum(self):
		a = self.matrixA()
		aT = a.T		#By Ka Ho report, p.16, equation (2.21)
		temp = aT*a
		temp = temp.I
		aInv = temp*aT
		return aInv

	def theta(self):
		'''
		Return the LLS estimated target location in list(x_coor, y_coor, value of 'x^2+y^2')
		'''
		Agumm = self.Agum()
		b = self.matrixB()
		theta = Agumm * b
		# return {'x':theta.item(0), 'y':theta.item(1), 'x^2+y^2':theta.item(2)}
		return theta

	def locationError(self):#, targetRealCoordinate=list()):
		'''
		Find the distance between the real location and LLS estimated location
		'''
		theta = self.theta()
		estLocX = theta.item(0)
		estLocY = theta.item(1)
		#print(estLoc[0]) --> x of the estimated location
		# tar = targetRealCoordinate
		tar = self.targetRealCoordinate
		LEsqt = pow((float(estLocX)-float(tar[0])),2) + pow((float(estLocY)-float(tar[1])),2) #((x2-x1)^2+(y2-y1)^2)^1/2
		LLSErr = math.sqrt(LEsqt)
		return LLSErr

	def distToTarget(self):
		'''
		Find the distance between each base station and the LLS estimated target location
		'''

		tar = self.targetRealCoordinate
		bs_coor_x = self.bsCoordinateX
		bs_coor_y = self.bsCoordinateY
		# target1 = tar.split(",")
		# sp_coor = []
		# sp_coor = bsCoordinate.split(";")  #["x1,y1"]--list ele1 ["x2,y2"]--list ele2...so on
		for i in range(len(bs_coor_x)):
			# aa = []
			# splited = sp_coor[i]     #for i = 1 handle the 1st ele ,["x1,y1"]-->[x1]--list ele1 [x2]--list ele2
			# aa = splited.split(",")
			temp = pow(int(bs_coor_x[i])-int(tar[0]),2)+pow(int(bs_coor_y[i])-int(tar[1]),2)
			temp1 = math.sqrt(temp)
			print("The distance between BS "+str(i+1)+" and the target is: "+ str(temp1)+ " m ")
		return
	
	def allResults(self) -> dict:
		'''
		Return a dict
		1. path loss exponent
		2. reference rssi
		3. estimated (x,y) coordinate by the LLS localization
		4. location error (distance) between the real and estimated location, based on (x,y)
		'''
		alpha = self.alpha			#Path loss exponent
		referenceRssi = self.Z0		#Reference RSSI
		theta = self.theta()		#The LLS estimated location (x,y)
		estLocX = theta.item(0)		#x coordinate
		estLocY = theta.item(1)		#y coordinate
		locError = self.locationError()	#The distance between the real and estimated location, based on (x,y)

		results = {'alpha':alpha, 'referenceRssi':referenceRssi, 'llsX':estLocX, 'llsY':estLocY, 'LE':locError}
		return results
		
	def allResultsGPS(self) -> dict:
		'''
		Return a dict
		1. path loss exponent
		2. reference rssi
		3. estimated (x,y) coordinate and GPS (lat,lng) by the LLS localization
		4. location error (distance) between the real and estimated location, based on (x,y)
		
		Illustration of this function
		----------
		1. Convert (1) BS GPS and (2) device GPS to (x,y) based on an origin
		2. Save the converted (x,y)
		3. Perform LLS by the converted BS (x,y) & device (x,y) and RSSI
		4. Get the LLS result & LE, and then convert the (x,y) back to GPS
		'''

		#Convert GPS to (x,y)
		##For BS
		##Origin of X-Y coordinate system: GPS(22.167615, 113.908514), Tai a Chau Landing No. 2, 大鴉洲2號梯台
		# origin_lat = 22.167615
		# origin_lng = 113.908514
		coordsys = myCoordinateSystem.Location(originlat=self.originLat,originlng=self.originLng)
		self.bsCoordinateX = list()
		self.bsCoordinateY = list()
		for index in range(len(self.bsCoordinateLat)):
			bs_coor_lat = self.bsCoordinateLat[index]
			bs_coor_lng = self.bsCoordinateLng[index]
			xy = coordsys.convertGPS2XY_v2(lat=bs_coor_lat,lng=bs_coor_lng)
			self.bsCoordinateX.append(xy['x'])
			self.bsCoordinateY.append(xy['y'])
		##For device GPS -> (x,y)
		xy = coordsys.convertGPS2XY_v2(lat=self.targetRealGPS[0],lng=self.targetRealGPS[1])
		self.targetRealCoordinate = [xy['x'], xy['y']]
		##Perform LLS
		alpha = self.alpha			#Path loss exponent
		referenceRssi = self.Z0		#Reference RSSI
		theta = self.theta()		#The LLS estimated location (x,y)
		estLocX = theta.item(0)		#LLS estimated x coordinate
		estLocY = theta.item(1)		#LLS estimated y coordinate
		##Convert LLS (x,y) to GPS(lat,lng)
		gps = coordsys.convertXY2GPS(dX=estLocX,dY=estLocY)
		estLocLat = gps.latitude
		estLocLng = gps.longitude
		locError = self.locationError()	#The distance between the real and estimated location, based on (x,y)

		results = {'alpha':alpha, 'referenceRssi':referenceRssi, 'llsX':estLocX, 'llsY':estLocY, 
					'llsLat':estLocLat, 'llsLng':estLocLng, 'LE':locError}
		return results

def test_xy_version():
	bs_coor_x = [26267.5635, 23228.2883, 33513.9487, 25004.3291, 35609.4251, 30404.6946, 26994.9396, 27105.7749, 27656.5554, 25930.8383, 30044.4027, 26789.3231, 26986.3979, 27728.1815, 28246.4421, 29050.7956, 23694.2701, 32315.5486, 28963.2182, 28195.7069, 30596.521, 27558.3781, 27823.0656, 24760.6355, 27933.0776, 31735.8502, 30717.4415, 28812.1446, 20475.6205, 29241.4899, 27125.7396, 25569.1055]
	bs_coor_y = [17223.5036, 21664.5076, 15638.9706, 13214.2206, 17365.5215, 13782.7367, 16518.0814, 15903.3372, 16673.4343, 12321.4415, 18884.9352, 16378.9527, 14434.3744, 18682.9097, 16911.6865, 13406.3559, 12984.9695, 18148.8424, 16139.4781, 15563.85, 18086.1678, 12174.4229, 14774.3061, 13251.003, 12392.8949, 16437.9602, 13907.6413, 15789.5451, 20671.0491, 13171.5486, 18150.7315, 8376.27768]
	measured_rssi = [-117.0, -117.0, -95.0, -84.0, -115.0, -105.0, -97.0, -115.0, -126.0, -86.0, -109.0, -103.0, -88.0, -111.0, -117.0, -79.0, -115.0, -112.0, -107.0, -108.0, -112.0, -95.0, -94.0, -91.0, -93.0, -103.0, -99.0, -106.0, -114.0, -89.0, -109.0, -126.0]
	device_x = 1
	device_y = 1
	performLLS = LLS(alpha = 2.5, Z0=-33, bsCoordinateX=bs_coor_x, bsCoordinateY=bs_coor_y,
						measuredRssi=measured_rssi, targetRealCoordinate=[device_x,device_y])
	llsResults = performLLS.allResults()
	print()
	print(llsResults)
	print()

def test_gps_version():
	bs_coor_lat=[22.322607, 22.362571, 22.308348, 22.286528, 22.323885, 22.291644, 22.316259, 22.310727, 22.317657, 22.278494, 22.337558, 22.315007, 22.297508, 22.33574, 22.319801, 22.288257, 22.284465, 22.330934, 22.312852, 22.307672, 22.33037, 22.277171, 22.300567, 22.286859, 22.279137, 22.315538, 22.292768, 22.309703, 22.353631, 22.286144, 22.330951, 22.242992]
	bs_coor_lng=[114.163759, 114.134226, 114.234173, 114.151484, 114.254535, 114.20396, 114.170827, 114.171904, 114.177256, 114.160487, 114.200459, 114.168829, 114.170744, 114.177952, 114.182988, 114.190804, 114.138754, 114.222528, 114.189953, 114.182495, 114.205824, 114.176302, 114.178874, 114.149116, 114.179943, 114.216895, 114.206999, 114.188485, 114.107478, 114.192657, 114.172098, 114.156972]
	measured_rssi = [-117.0, -117.0, -95.0, -84.0, -115.0, -105.0, -97.0, -115.0, -126.0, -86.0, -109.0, -103.0, -88.0, -111.0, -117.0, -79.0, -115.0, -112.0, -107.0, -108.0, -112.0, -95.0, -94.0, -91.0, -93.0, -103.0, -99.0, -106.0, -114.0, -89.0, -109.0, -126.0]
	device_gps_lat = 22.293222
	device_gps_lng = 114.172889
	performLLS = LLS(alpha = 2.5, Z0=-33, bsCoordinateLat=bs_coor_lat, bsCoordinateLng=bs_coor_lng,
						measuredRssi=measured_rssi, targetRealGPS=[device_gps_lat,device_gps_lng])
	llsResults = performLLS.allResultsGPS()
	print()
	print(llsResults)
	print()


""" Test """
# print('\n=== xy version =======')
# test_xy_version()
# print('\n=== GPS lat lng version =======')
# test_gps_version()


