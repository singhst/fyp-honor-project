'''
# Originated by: Sing (2019-2020)
# Last Modified: 30 May 2020
# Modified by: Sing (2019-2020)
# Description: Built for Raspberry Pi real-time localization server (flask - web application)

Functions::
1. Perform Linear Least Squares (LLS) Localization with the received RSSI data from "Google Script <-- sigfox"
2. Return the LLS result in `dictionary` type
'''

import pandas as pd
from mymodule import myHttpInterface
from mymodule import myLLS_v2 as myLLS
from mymodule import mygoodBS_CNN_v1 as mygoodBS #find the good BS/removing bad BS
#To solve issue in MacOS: "OMP: Error #15: Initializing libiomp5.dylib, but found libiomp5.dylib already initialized."
# import os
# os.environ['KMP_DUPLICATE_LIB_OK']='True'
# from mymodule.submodule import CoordinateSystem_v2 as myCoordinateSystem

def perform_lls(dataframe, alpha=2.5, z0=-20, cnn=None):
    print('\n=== LLS performLocalization.py <BEGIN> ===')
    my_dataframe = dataframe.copy()
    # print(my_dataframe.head)

    #store it locally
    '''
    (may develop)
    '''

    #Clear the dataframe, remove the RSSI measurement(s) with unknown base station ID
    ##Remove the row(s) contained empty cell(s)
    unknown_bs_numb = len(my_dataframe[pd.isna(my_dataframe['BaseStationLat'])]) 
    unknown_bs_id = my_dataframe[pd.isna(my_dataframe['BaseStationLat'])]['bsId'].tolist()
    if unknown_bs_numb: #if there is one or more than one unknown base station ID
            print(">>> Number of unknown BS: {}".format(unknown_bs_numb))
            print(">>> Unknown BS ID:\t{}".format(unknown_bs_id))
    my_dataframe.dropna(subset=['BaseStationLat'], inplace=True)
    #Perform LLS localization
    #1
    ##Prepare the needed variables
    ##need: alpha, Z0, origin GPS, BS GPS, measured RSSI, target real location
    ##Origin of X-Y coordinate system: GPS(22.167615, 113.908514), Tai a Chau Landing No. 2, 大鴉洲2號梯台
    origin_gps_lat = 22.167615
    origin_gps_lng = 113.908514
    alpha_path_loss_exponent = alpha #5.803
    Z0_reference_rssi = z0 #-33.0 #-45.0
    bs_gps_lat = my_dataframe['BaseStationLat'].astype('float', copy=False).tolist()
    bs_gps_lng = my_dataframe['BaseStationLng'].astype('float', copy=False).tolist()
    measured_rssi = my_dataframe['rssi'].astype('float', copy=False).tolist()
    # print(bs_gps_lat)		#debug purpose
    # print(bs_gps_lng)		#
    # print(measured_rssi)	#
    
    """
    Convert 'data' in HEX to DEC to get the GPS of the device real location
    #	Format: HHHHHHHH | hhhhhhhh | uuuuuuuu
    #			GPS Latitude | GPS Longitude | Not yet used
    #	e.g. data = str(0154535E06CE3A5A00000000)
    #	> First 8 digits	(HHHHHHHH) = 0154535E
    #	> Second 8 digits	(hhhhhhhh) = 06CE3A5A
    #	> Last 8 digits		(uuuuuuuu) = 00000000
    """
    my_data = my_dataframe['data'].values[0] #type str
    real_gps_lat = int(my_data[0:8], 16) * (10**-6)
    real_gps_lng = int(my_data[8:16], 16) * (10**-6)
    last_eight_d = int(my_data[16:24], 16)
    target_real_gps = [real_gps_lat,real_gps_lng]


    #2
    ##Perform LLS localization to get estimated location of the device by the measured RSSI
    print('=== LLS localization')
    ###Pure LLS localization
    perform_lls = myLLS.LLS(alpha=alpha_path_loss_exponent, Z0=Z0_reference_rssi,
                                                    bsCoordinateLat=bs_gps_lat, bsCoordinateLng=bs_gps_lng,
                                                    measuredRssi=measured_rssi, targetRealGPS=target_real_gps
                                                    )
    lls_results = perform_lls.allResultsGPS() #The function returns a dict
    # print(lls_results)	#debug purpose
    print('> finished.')
    ###LLS-ML localization
    print('=== ML LLS')
    bs_filepath = 'mymodule/BS_list_2020.xlsx'
    ml_filepath = r'mymodule/rssi_cnn_1d_1convlayer_10filtersize_v0 89 acc 50batch.h5'
    distance_threshold = 300
    ##Finding good basestations df OR removing bad basestations by NN classifier
    ml_classification_list = mygoodBS.MLfindGoodBS(my_dataframe, bs_filepath,ml_filepath, alpha_path_loss_exponent, Z0_reference_rssi, distance_threshold, cnn)
    df_good_bs, df_bad_bs, df_all_bs, pred_region_prob, pred_region, pred_region_gps = ml_classification_list
    ml_good_bs = df_good_bs['bsId'].tolist()
    print("> Good BS:\tx{} BS,  {}".format(len(ml_good_bs), ml_good_bs))
    # print('pred_region_prob %:', pred_region_prob[0].tolist())
    # print('pred_region: Region-{}'.format(str(pred_region[0])))
    # print('pred_region_gps:',pred_region_gps)
    if ml_good_bs: #perform LLS-ML localization only if good bs presents
        bs_gps_lat = df_good_bs['BaseStationLat'].astype('float', copy=False).tolist()
        bs_gps_lng = df_good_bs['BaseStationLng'].astype('float', copy=False).tolist()
        measured_rssi = df_good_bs['rssi'].astype('float', copy=False).tolist()
        print(bs_gps_lat)
        print(bs_gps_lng)
        print(measured_rssi)
        perform_ml_lls = myLLS.LLS(alpha=alpha_path_loss_exponent, Z0=Z0_reference_rssi,
                                                        bsCoordinateLat=bs_gps_lat, bsCoordinateLng=bs_gps_lng,
                                                        measuredRssi=measured_rssi, targetRealGPS=target_real_gps
                                                        )
        ml_lls_results = perform_ml_lls.allResultsGPS() #The function returns a dict
    else:
#         ml_lls_lat = pred_region_gps[0]
#         ml_lls_lng = pred_region_gps[1]
#         coordsys = myCoordinateSystem.Location(origin_gps_lat, origin_gps_lng)
#         ml_lls_le = coordsys.distance_btw2gps(lat1=ml_lls_lat, lng1=ml_lls_lng, lat2=real_gps_lat, lng2=real_gps_lng)
        ml_lls_results = {'llsLat':'', 'llsLng':'', 'LE':''}
    print(ml_lls_results)	#debug purpose
    ###LLS and LLS-ML Results
    print('=== LLS results')
    date	= my_dataframe['DateRecorded'].values[1]
    time	= my_dataframe['TimeRecorded'].values[1]
    seq  = my_dataframe['seqNumber'].values[1]
    device_id	= my_dataframe['device'].values[1]
    alpha     = alpha_path_loss_exponent
    ref_rssi	 = Z0_reference_rssi
    lls_x		= lls_results['llsX']
    lls_y		= lls_results['llsY']
    lls_lat		= lls_results['llsLat']
    lls_lng		= lls_results['llsLng']
    lls_loc_error = lls_results['LE']
    ml_lls_lat		= ml_lls_results['llsLat']
    ml_lls_lng		= ml_lls_results['llsLng']
    ml_lls_loc_error = ml_lls_results['LE']
    # print('> LLS xy:\t{0:s}, {1:s}'.format(str(lls_x), str(lls_y)))
    print("> Real GPS:\t{}".format(target_real_gps))
    print('> LLS GPS:\t{0:s}, {1:s},   LE: {2:s} m'.format(str(lls_lat), str(lls_lng), str(lls_loc_error)))
    print('> LLS-ML GPS:\t{0:s}, {1:s},   LE: {2:s} m'.format(str(ml_lls_lat), str(ml_lls_lng), str(ml_lls_loc_error)))

    #3
    ##Return a dictionary containing LLS result
    lls_result_dict = {
        'date': str(date),
        'time': str(time),
        'seqNumber': str(seq),
        'device': str(device_id),
        'pathLossExponentAlpha': str(alpha),
        'referenceRSSIZ0': str(ref_rssi),
        'GPSLat': str(real_gps_lat),
        'GPSLng': str(real_gps_lng),
        'LLSLat': str(lls_lat),
        'LLSLng': str(lls_lng),
        'LLSX': str(lls_x),
        'LLSY': str(lls_y),
        'LLSlocalizationError': str(lls_loc_error),
        'mlRegion': str(pred_region[0]),
        'mlRegionGPSLat': str(pred_region_gps[0]),
        'mlRegionGPSLng': str(pred_region_gps[1]),
        'mlGoodBS': [],
        'mlLLSLat': str(ml_lls_lat),
        'mlLLSLng': str(ml_lls_lng),
        'mlLLSlocalizationError': str(ml_lls_loc_error)
        }
    # print('\nDistance between each base station and the LLS estimated target location')
    # print('------------------------')
    # print(perform_lls.distToTarget())
    print('=== LLS performLocalization.py <END> ===\n')
    return lls_result_dict

# For neural network classification
def mlClassier():
    pass

# For local program debugging
def test():
    received_data_testdict = {
            'DateRecorded': {0: '20200525', 1: '20200525', 2: '20200525', 3: '20200525', 4: '20200525'}, 
            'TimeRecorded': {0: '21:56:05', 1: '21:56:05', 2: '21:56:05', 3: '21:56:05', 4: '21:56:05'}, 
            'bsId': {0: '6E23', 1: '790C', 2: '80C7', 3: '7C6B', 4: '6C6B'}, 
            'rssi': {0: -113.0, 1: -113.0, 2: -97.0, 3: -129.0, 4: -126.0}, 
            'nbRep': {0: 2.0, 1: 2.0, 2: 3.0, 3: 2.0, 4: 1.0}, 
            'snr': {0: 8.57, 1: 8.57, 2: 27.41, 3: 6.0, 4: 10.0}, 
            'device': {0: '3E81CB', 1: '3E81CB', 2: '3E81CB', 3: '3E81CB', 4: '3E81CB'}, 
            'time': {0: '1590387742', 1: '1590387742', 2: '1590387742', 3: '1590387742', 4: '1590387742'}, 
            'data': {0: '01541B8106CE9F0600000000', 1: '01541B8106CE9F0600000000', 2: '01541B8106CE9F0600000000', 3: '01541B8106CE9F0600000000', 4: '01541B8106CE9F0600000000'}, 
            'seqNumber': {0: '2017', 1: '2017', 2: '2017', 3: '2017', 4: '2017'}, 
            'lqi': {0: 'Good', 1: 'Good', 2: 'Good', 3: 'Good', 4: 'Good'}, 
            'linkQuality': {0: '2', 1: '2', 2: '2', 3: '2', 4: '2'}, 
            'fixedLat': {0: '0.0', 1: '0.0', 2: '0.0', 3: '0.0', 4: '0.0'}, 
            'fixedLng': {0: '0.0', 1: '0.0', 2: '0.0', 3: '0.0', 4: '0.0'}, 
            'operatorName': {0: 'SIGFOX_HongKong_Thinxtra', 1: 'SIGFOX_HongKong_Thinxtra', 2: 'SIGFOX_HongKong_Thinxtra', 3: 'SIGFOX_HongKong_Thinxtra', 4: 'SIGFOX_HongKong_Thinxtra'}, 
            'countryCode': {0: '344', 1: '344', 2: '344', 3: '344', 4: '344'}, 
            'deviceTypeId': {0: '5b0e41de3c8789741699c804', 1: '5b0e41de3c8789741699c804', 2: '5b0e41de3c8789741699c804', 3: '5b0e41de3c8789741699c804', 4: '5b0e41de3c8789741699c804'}, 
            'lat': {0: 22.292783054956907, 1: 22.292783054956907, 2: 22.292783054956907, 3: 22.292783054956907, 4: 22.292783054956907}, 
            'lng': {0: 114.20696752212505, 1: 114.20696752212505, 2: 114.20696752212505, 3: 114.20696752212505, 4: 114.20696752212505}, 
            'radius': {0: 5979.0, 1: 5979.0, 2: 5979.0, 3: 5979.0, 4: 5979.0}, 
            'source': {0: 2.0, 1: 2.0, 2: 2.0, 3: 2.0, 4: 2.0}, 
            'status': {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}, 
            'BaseStationLat': {0: None, 1: 22.291644, 2: 22.292768, 3: 22.330934, 4: 22.308348}, 
            'BaseStationLng': {0: None, 1: 114.20396, 2: 114.206999, 3: 114.222528, 4: 114.234173}, 
            'BaseStationHeight': {0: None, 1: 84, 2: 77, 3: 24, 4: 102}, 
            'BaseStationRegion': {0: None, 1: 'Hong Kong Island', 2: 'Hong Kong Island', 3: 'Kowloon', 4: 'Kowloon'}, 
            'SubDistrict': {0: None, 1: 'North Point', 2: 'North Point', 3: 'xxx', 4: 'xxx'}, 
            'BaseStationX': {0: None, 1: 30404.6946, 2: 30717.4415, 3: 32315.5486, 4: 33513.9487}, 
            'BaseStationY': {0: None, 1: 13782.7367, 2: 13907.6413, 3: 18148.8424, 4: 15638.9706}, 
            'OriginGPSLat': {0: None, 1: 22.167615, 2: 22.167615, 3: 22.167615, 4: 22.167615}, 
            'OriginGPSLng': {0: None, 1: 113.908514, 2: 113.908514, 3: 113.908514, 4: 113.908514}, 
            'PathLossExponent': {0: None, 1: None, 2: None, 3: None, 4: None}, 
            'ReferenceRSSI': {0: None, 1: None, 2: None, 3: None, 4: None}, 
            'DeviceLLSLat': {0: None, 1: None, 2: None, 3: None, 4: None}, 
            'DeviceLLSLng': {0: None, 1: None, 2: None, 3: None, 4: None}, 
            'DeviceLLSX': {0: None, 1: None, 2: None, 3: None, 4: None}, 
            'DeviceLLSY': {0: None, 1: None, 2: None, 3: None, 4: None}, 
            'DeviceGPSLat': {0: None, 1: None, 2: None, 3: None, 4: None}, 
            'DeviceGPSLng': {0: None, 1: None, 2: None, 3: None, 4: None}, 
            'LocalizationError': {0: None, 1: None, 2: None, 3: None, 4: None}
    }

    ml_data_testdict={
            'DateRecorded': {0: '2020-01-02 14:55:40.177', 1: '2020-01-02 14:55:40.177', 2: '2020-01-02 14:55:40.177', 3: '2020-01-02 14:55:40.177', 4: '2020-01-02 14:55:40.177', 5: '2020-01-02 14:55:40.177', 6: '2020-01-02 14:55:40.177', 7: '2020-01-02 14:55:40.177', 8: '2020-01-02 14:55:40.177', 9: '2020-01-02 14:55:40.177', 10: '2020-01-02 14:55:40.177', 11: '2020-01-02 14:55:40.177', 12: '2020-01-02 14:55:40.177', 13: '2020-01-02 14:55:40.177', 14: '2020-01-02 14:55:40.177', 15: '2020-01-02 14:55:40.177', 16: '2020-01-02 14:55:40.177', 17: '2020-01-02 14:55:15.095', 18: '2020-01-02 14:55:40.177', 19: '2020-01-02 14:55:40.177', 20: '2020-01-02 14:55:40.177', 21: '2020-01-02 14:55:40.177', 22: '2020-01-02 14:55:40.177', 23: '2020-01-02 14:55:40.177', 24: '2020-01-02 14:55:40.177', 25: '2020-01-02 14:55:40.177', 26: '2020-01-02 14:55:40.177', 27: '2020-01-02 14:55:40.177', 28: '2020-01-02 14:55:40.177', 29: '2020-01-02 14:55:40.177', 30: '2020-01-02 14:55:40.177', 31: '2020-01-02 14:55:40.177', 32: '2020-01-02 14:55:40.177', 33: '2020-01-02 14:55:40.177', 34: '2020-01-02 14:55:40.177'}, 
            'TimeRecorded': {0: '2020-01-02 14:55:40.177', 1: '2020-01-02 14:55:40.177', 2: '2020-01-02 14:55:40.177', 3: '2020-01-02 14:55:40.177', 4: '2020-01-02 14:55:40.177', 5: '2020-01-02 14:55:40.177', 6: '2020-01-02 14:55:40.177', 7: '2020-01-02 14:55:40.177', 8: '2020-01-02 14:55:40.177', 9: '2020-01-02 14:55:40.177', 10: '2020-01-02 14:55:40.177', 11: '2020-01-02 14:55:40.177', 12: '2020-01-02 14:55:40.177', 13: '2020-01-02 14:55:40.177', 14: '2020-01-02 14:55:40.177', 15: '2020-01-02 14:55:40.177', 16: '2020-01-02 14:55:40.177', 17: '2020-01-02 14:55:15.095', 18: '2020-01-02 14:55:40.177', 19: '2020-01-02 14:55:40.177', 20: '2020-01-02 14:55:40.177', 21: '2020-01-02 14:55:40.177', 22: '2020-01-02 14:55:40.177', 23: '2020-01-02 14:55:40.177', 24: '2020-01-02 14:55:40.177', 25: '2020-01-02 14:55:40.177', 26: '2020-01-02 14:55:40.177', 27: '2020-01-02 14:55:40.177', 28: '2020-01-02 14:55:40.177', 29: '2020-01-02 14:55:40.177', 30: '2020-01-02 14:55:40.177', 31: '2020-01-02 14:55:40.177', 32: '2020-01-02 14:55:40.177', 33: '2020-01-02 14:55:40.177', 34: '2020-01-02 14:55:40.177'}, 
            'device': {0: '3E81CB', 1: '3E81CB', 2: '3E81CB', 3: '3E81CB', 4: '3E81CB', 5: '3E81CB', 6: '3E81CB', 7: '3E81CB', 8: '3E81CB', 9: '3E81CB', 10: '3E81CB', 11: '3E81CB', 12: '3E81CB', 13: '3E81CB', 14: '3E81CB', 15: '3E81CB', 16: '3E81CB', 17: '3E81CB', 18: '3E81CB', 19: '3E81CB', 20: '3E81CB', 21: '3E81CB', 22: '3E81CB', 23: '3E81CB', 24: '3E81CB', 25: '3E81CB', 26: '3E81CB', 27: '3E81CB', 28: '3E81CB', 29: '3E81CB', 30: '3E81CB', 31: '3E81CB', 32: '3E81CB', 33: '3E81CB', 34: '3E81CB'}, 
            'seqNumber': {0: 1186, 1: 1186, 2: 1186, 3: 1186, 4: 1186, 5: 1186, 6: 1186, 7: 1186, 8: 1186, 9: 1186, 10: 1186, 11: 1186, 12: 1186, 13: 1186, 14: 1186, 15: 1186, 16: 1186, 17: 1186, 18: 1186, 19: 1186, 20: 1186, 21: 1186, 22: 1186, 23: 1186, 24: 1186, 25: 1186, 26: 1186, 27: 1186, 28: 1186, 29: 1186, 30: 1186, 31: 1186, 32: 1186, 33: 1186, 34: 1186}, 
            'bsId': {0: '6BFE', 1: '6C6B', 2: '6DEB', 3: '6DED', 4: '6E12', 5: '790C', 6: '79BF', 7: '79CD', 8: '7A05', 9: '7A06', 10: '7A32', 11: '7A4E', 12: '7A65', 13: '7B21', 14: '7C43', 15: '7C4B', 16: '7C52', 17: '7C54', 18: '7C59', 19: '7C6B', 20: '7C86', 21: '7F0F', 22: '7F10', 23: '7F1F', 24: '7F27', 25: '8041', 26: '8042', 27: '8043', 28: '80C7', 29: '810F', 30: '8112', 31: '8114', 32: '8117', 33: '8141', 34: '8142'}, 
            'rssi': {0: -123.0, 1: -96.0, 2: -78.0, 3: -115.0, 4: -111.0, 5: -99.0, 6: -97.0, 7: -115.0, 8: -131.0, 9: -115.0, 10: -126.0, 11: -87.0, 12: -108.0, 13: -101.0, 14: -89.0, 15: -106.0, 16: -114.0, 17: -82.0, 18: -109.0, 19: -121.0, 20: -106.0, 21: -114.0, 22: -99.0, 23: -107.0, 24: -91.0, 25: -92.0, 26: -99.0, 27: -105.0, 28: -99.0, 29: -111.0, 30: -112.0, 31: -119.0, 32: -91.0, 33: -111.0, 34: -124.0}, 
            'snr': {0: 15.97, 1: 24.64, 2: 26.21, 3: 20.84, 4: 19.98, 5: 23.86, 6: 22.22, 7: 18.09, 8: 9.38, 9: 23.36, 10: 11.14, 11: 26.21, 12: 22.92, 13: 24.08, 14: 26.17, 15: 25.77, 16: 20.85, 17: 25.24, 18: 23.96, 19: 14.65, 20: 23.72, 21: 22.54, 22: 27.52, 23: 24.98, 24: 26.71, 25: 29.22, 26: 25.66, 27: 25.63, 28: 23.12, 29: 19.97, 30: 18.45, 31: 18.87, 32: 25.8, 33: 6.0, 34: 7.56}, 
            'data': {0: '01542ad206ce23e000000000', 1: '01542ad206ce23e000000000', 2: '01542ad206ce23e000000000', 3: '01542ad206ce23e000000000', 4: '01542ad206ce23e000000000', 5: '01542ad206ce23e000000000', 6: '01542ad206ce23e000000000', 7: '01542ad206ce23e000000000', 8: '01542ad206ce23e000000000', 9: '01542ad206ce23e000000000', 10: '01542ad206ce23e000000000', 11: '01542ad206ce23e000000000', 12: '01542ad206ce23e000000000', 13: '01542ad206ce23e000000000', 14: '01542ad206ce23e000000000', 15: '01542ad206ce23e000000000', 16: '01542ad206ce23e000000000', 17: '01542ad206ce23e000000000', 18: '01542ad206ce23e000000000', 19: '01542ad206ce23e000000000', 20: '01542ad206ce23e000000000', 21: '01542ad206ce23e000000000', 22: '01542ad206ce23e000000000', 23: '01542ad206ce23e000000000', 24: '01542ad206ce23e000000000', 25: '01542ad206ce23e000000000', 26: '01542ad206ce23e000000000', 27: '01542ad206ce23e000000000', 28: '01542ad206ce23e000000000', 29: '01542ad206ce23e000000000', 30: '01542ad206ce23e000000000', 31: '01542ad206ce23e000000000', 32: '01542ad206ce23e000000000', 33: '01542ad206ce23e000000000', 34: '01542ad206ce23e000000000'}, 
            'time': {0: 1577948112.0, 1: 1577948112.0, 2: 1577948112.0, 3: 1577948112.0, 4: 1577948112.0, 5: 1577948112.0, 6: 1577948112.0, 7: 1577948112.0, 8: 1577948112.0, 9: 1577948112.0, 10: 1577948112.0, 11: 1577948112.0, 12: 1577948112.0, 13: 1577948112.0, 14: 1577948112.0, 15: 1577948112.0, 16: 1577948112.0, 17: 1577948112.0, 18: 1577948112.0, 19: 1577948112.0, 20: 1577948112.0, 21: 1577948112.0, 22: 1577948112.0, 23: 1577948112.0, 24: 1577948112.0, 25: 1577948112.0, 26: 1577948112.0, 27: 1577948112.0, 28: 1577948112.0, 29: 1577948112.0, 30: 1577948112.0, 31: 1577948112.0, 32: 1577948112.0, 33: 1577948112.0, 34: 1577948112.0}, 
            'BaseStationLat': {0: 22.362571, 1: 22.308348, 2: 22.286528, 3: 22.323885, 4: 22.322607, 5: 22.291644, 6: 22.316259, 7: 22.310727, 8: 22.370572, 9: 22.317657, 10: 22.362317, 11: 22.278494, 12: 22.337558, 13: 22.315007, 14: 22.297508, 15: 22.33574, 16: 22.319801, 17: 22.288257, 18: 22.284465, 19: 22.330934, 20: 22.312852, 21: 22.307672, 22: 22.33037, 23: 22.277171, 24: 22.300567, 25: 22.286859, 26: 22.279137, 27: 22.315538, 28: 22.292768, 29: 22.309703, 30: 22.350155, 31: 22.353631, 32: 22.286144, 33: 22.330951, 34: 22.242992}, 
            'BaseStationLng': {0: 114.134226, 1: 114.234173, 2: 114.151484, 3: 114.254535, 4: 114.163759, 5: 114.20396, 6: 114.170827, 7: 114.171904, 8: 114.130405, 9: 114.177256, 10: 114.105205, 11: 114.160487, 12: 114.200459, 13: 114.168829, 14: 114.170744, 15: 114.177952, 16: 114.182988, 17: 114.190804, 18: 114.138754, 19: 114.222528, 20: 114.189953, 21: 114.182495, 22: 114.205824, 23: 114.176302, 24: 114.178874, 25: 114.149116, 26: 114.179943, 27: 114.216895, 28: 114.206999, 29: 114.188485, 30: 114.110168, 31: 114.107478, 32: 114.192657, 33: 114.172098, 34: 114.156972}, 
            'BaseStationHeight': {0: 90.0, 1: 102.0, 2: 87.0, 3: 132.0, 4: 50.0, 5: 84.0, 6: 83.0, 7: 24.0, 8: 57.0, 9: 38.0, 10: 28.0, 11: 193.0, 12: 78.0, 13: 80.0, 14: 53.0, 15: 34.0, 16: 34.0, 17: 126.0, 18: 38.0, 19: 24.0, 20: 28.0, 21: 27.0, 22: 108.0, 23: 71.0, 24: 39.0, 25: 75.0, 26: 75.0, 27: 36.0, 28: 77.0, 29: 45.0, 30: 56.0, 31: 93.0, 32: 83.0, 33: 26.0, 34: 110.0}, 
            'BaseStationRegion': {0: 'New Territories', 1: 'Kowloon', 2: 'Hong Kong Island', 3: 'New Territories', 4: 'Kowloon', 5: 'Hong Kong Island', 6: 'Kowloon', 7: 'Kowloon', 8: 'New Territories', 9: 'Kowloon', 10: 'New Territories', 11: 'Hong Kong Island', 12: 'Kowloon', 13: 'Kowloon', 14: 'Kowloon', 15: 'Kowloon', 16: 'Kowloon', 17: 'Hong Kong Island', 18: 'Hong Kong Island', 19: 'Kowloon', 20: 'Kowloon', 21: 'Kowloon', 22: 'Kowloon', 23: 'Hong Kong Island', 24: 'Kowloon', 25: 'Hong Kong Island', 26: 'Hong Kong Island', 27: 'Kowloon', 28: 'Hong Kong Island', 29: 'Kowloon', 30: 'New Territories', 31: 'New Territories', 32: 'Hong Kong Island', 33: 'Kowloon', 34: 'Hong Kong Island'}, 
            'SubDistrict': {0: 'xxx', 1: 'xxx', 2: 'Sheung Wan', 3: 'xxx', 4: 'xxx', 5: 'North Point', 6: 'xxx', 7: 'xxx', 8: 'xxx', 9: 'xxx', 10: 'xxx', 11: 'Central', 12: 'xxx', 13: 'xxx', 14: 'xxx', 15: 'xxx', 16: 'xxx', 17: 'Fortress Hill', 18: 'Sai Ying Pun', 19: 'xxx', 20: 'xxx', 21: 'xxx', 22: 'xxx', 23: 'Wan Chai', 24: 'xxx', 25: 'Sheung Wan', 26: 'Wan Chai', 27: 'xxx', 28: 'North Point', 29: 'xxx', 30: 'xxx', 31: 'xxx', 32: 'Fortress Hill', 33: 'xxx', 34: 'Ap Lei Chau'}, 
            'BaseStationX': {0: 23228.2883, 1: 33513.9487, 2: 25004.3291, 3: 35609.4251, 4: 26267.5635, 5: 30404.6946, 6: 26994.9396, 7: 27105.7749, 8: 22835.0648, 9: 27656.5554, 10: 20241.7034, 11: 25930.8383, 12: 30044.4027, 13: 26789.3231, 14: 26986.3979, 15: 27728.1815, 16: 28246.4421, 17: 29050.7956, 18: 23694.2701, 19: 32315.5486, 20: 28963.2182, 21: 28195.7069, 22: 30596.521, 23: 27558.3781, 24: 27823.0656, 25: 24760.6355, 26: 27933.0776, 27: 31735.8502, 28: 30717.4415, 29: 28812.1446, 30: 20752.4515, 31: 20475.6205, 32: 29241.4899, 33: 27125.7396, 34: 25569.1055}, 
            'BaseStationY': {0: 21664.5076, 1: 15638.9706, 2: 13214.2206, 3: 17365.5215, 4: 17223.5036, 5: 13782.7367, 6: 16518.0814, 7: 15903.3372, 8: 22553.6197, 9: 16673.4343, 10: 21636.2818, 11: 12321.4415, 12: 18884.9352, 13: 16378.9527, 14: 14434.3744, 15: 18682.9097, 16: 16911.6865, 17: 13406.3559, 18: 12984.9695, 19: 18148.8424, 20: 16139.4781, 21: 15563.85, 22: 18086.1678, 23: 12174.4229, 24: 14774.3061, 25: 13251.003, 26: 12392.8949, 27: 16437.9602, 28: 13907.6413, 29: 15789.5451, 30: 20284.7782, 31: 20671.0491, 32: 13171.5486, 33: 18150.7315, 34: 8376.27768}, 
            'OriginGPSLat': {0: 22.167615, 1: 22.167615, 2: 22.167615, 3: 22.167615, 4: 22.167615, 5: 22.167615, 6: 22.167615, 7: 22.167615, 8: 22.167615, 9: 22.167615, 10: 22.167615, 11: 22.167615, 12: 22.167615, 13: 22.167615, 14: 22.167615, 15: 22.167615, 16: 22.167615, 17: 22.167615, 18: 22.167615, 19: 22.167615, 20: 22.167615, 21: 22.167615, 22: 22.167615, 23: 22.167615, 24: 22.167615, 25: 22.167615, 26: 22.167615, 27: 22.167615, 28: 22.167615, 29: 22.167615, 30: 22.167615, 31: 22.167615, 32: 22.167615, 33: 22.167615, 34: 22.167615}, 
            'OriginGPSLng': {0: 113.908514, 1: 113.908514, 2: 113.908514, 3: 113.908514, 4: 113.908514, 5: 113.908514, 6: 113.908514, 7: 113.908514, 8: 113.908514, 9: 113.908514, 10: 113.908514, 11: 113.908514, 12: 113.908514, 13: 113.908514, 14: 113.908514, 15: 113.908514, 16: 113.908514, 17: 113.908514, 18: 113.908514, 19: 113.908514, 20: 113.908514, 21: 113.908514, 22: 113.908514, 23: 113.908514, 24: 113.908514, 25: 113.908514, 26: 113.908514, 27: 113.908514, 28: 113.908514, 29: 113.908514, 30: 113.908514, 31: 113.908514, 32: 113.908514, 33: 113.908514, 34: 113.908514}
    }

    # Testing purpose - For debugging this .py
    df = pd.DataFrame(ml_data_testdict)
    # df = df.iloc[0:len(df),:]
    print(df)
    lls_result = perform_lls(df,2.7,-20)
    print(lls_result)

# test()
#################################################
# Output:
'''

'''