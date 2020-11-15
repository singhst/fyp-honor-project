'''
# Modified from: Leung Ki Fung (2018-2019):/Sigfox localization/Data_Analysis/RadioPropagation.py
# Last Modified: 10th Feburary 2020
# Modified by: Sing (2019-2020)
# Description: A module related to the radio propagation parameters

Functions::
1. find the reference RSSI, z0
2. find the path loss exponent, alpha
3. find the expected RSSI by the distance between a receiver and transimitter
4. find the distance between 2 (x,y) coordinates
5. 
(X)6. find the best 'alpha' & the best 'reference RSSI'

'''

from math import sqrt,log10
import numpy 

# 1. 
def find_Ref_RSSI(alpha=float, distanceBtwTwoPts=float, measuredRssi=float):
    """Return float, Find the reference RSSI if path loss exponent (alpha), the distance between two points and measured RSSI are known."""
    Z0 = measuredRssi + 10*alpha*(log10(distanceBtwTwoPts))
    return Z0

# 2.
def find_alpha(rssi1=float,rssi2=float,distance1=float,distance2=float):
    rssi = rssi1-rssi2
    alpha = rssi/(10*(log10(distance2)-log10(distance1)))
    return alpha

# 3.
# input parameters: reference RSSI, path loss exponent, distance between a receiver and a transmitter
def log_Normal_RSSI_With_Distance(alpha=2.3,z0=-31.0,distance=float):
    """Find expected RSSI between two points if the reference RSSI, 
    path loss exponent and the distance between two points are known."""
    z = z0 - ((10.*alpha)*numpy.log10(distance))
    return z


""" The functions in CoordinateSysten_v?.py are the better alternatives from the below """
#4. 
#Find distance between two (x,y) coordinates
#P.S.
#Xan/Yan: x/y coordinate of anchor node (base stations)
#Xt/Yt: x/y coordinate of target node (sigfox xkit)
# def square_distance(Xan, Yan, Xt, Yt):
#     xSquare = (Xan-Xt)*(Xan-Xt)
#     ySquare = (Yan-Yt)*(Yan-Yt)
#     dist = sqrt(xSquare+ySquare)
#     return dist

#5.
# def distance (TX,TY,c):
#     xSquare = (TX-c[0])*(TX-c[0])
#     ySquare = (TY-c[1])*(TY-c[1])
#     dist = sqrt(xSquare+ySquare)
#     return dist


