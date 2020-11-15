'''
# Modified from: Sham Yik Yee (2018-19): /Sigfox vs LoRa/FYP/myNCR.py
				 LAM KA HO (2017-2018): /Simulation.Mphil/module/NCR.py
# Last Modified: 27th Feburary 2020
# Modified by: Sing (2019-2020)
# Description: 

Functions:
1. Find out the combination of the inputs

'''

import math
import numpy

count = 1
allCombin = []

def printCombination(arr, n, r): 
    data = [0]*r
    combinationUtil(arr, data, 0, n - 1, 0, r)

def combinationUtil(arr, data, start,end, index, r):
	global count
	global allCombin

	if (index == r):
		print("combination "+str(count)+": ")
		tempString = ""
		for j in range(r):
			tempString = (tempString + data[j]) 		#make the temp string in allCombin[i] as [BS1;x1,y1,rssi1#BS2;x2,y2;rssi2#BS3...]
			if (j<(len(range(r)))-1):					#j<2
				tempString = (tempString + "#")

			print(data[j], end = " ")  				#data[j] can be a string or integer
		allCombin.append(tempString) 					#add them into the allCombin[]
		count+=1
		print()
		#print(allCombin)
		return
	i = start
	while(i <= end and end - i + 1 >= r - index):
		data[index] = arr[i]
		combinationUtil(arr, data, i + 1,end, index + 1, r)
		i += 1
         
         

""" Test """
#Staring of the main function
#Change the input here
# arr = ["BS1;32,60;-76", "BS2;32,60;-80","BS3;32,60;-76", "BS4;32,60;-76", "BS5;32,60;-76"]
# r = 3			# How many BS as a combination r=3
# n = len(arr)	# How any BS are there totally
# print('===========')
# printCombination(arr, n, r)	# Call the printCombination()
# print('===========')
# print(allCombin)





