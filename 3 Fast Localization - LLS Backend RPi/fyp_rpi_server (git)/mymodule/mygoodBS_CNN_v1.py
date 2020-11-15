'''
# Originated by: Sing (2019-2020)
# Last Modified: 30 May 2020
# Modified by: Sing (2019-2020)
# Description: Using Neural Network classifier to perform classification and find out good BS/elimite bad BS. 
#              Return the result.

Functions:
1) Reshape the measured RSSI df format to keras acceptive format
2) 
3) Return (1) 
'''

import numpy as np
import pandas as pd
import tensorflow.keras as keras
# from keras.utils import np_utils
### Self libraries 1 ###
try: #For external use in the outside .py
	from mymodule.submodule import CoordinateSystem_v2 as myCoordinateSystem
except ModuleNotFoundError as err:
    err_1 = str(err)
try: #For internal testing in this module 
	from submodule import CoordinateSystem_v2 as myCoordinateSystem
except ModuleNotFoundError as err:
    err_2 = str(err)

### Self libraries 2 ###
try: #For external use in the outside .py
	from mymodule import RadioPropagation_v2 as myRadioPropagation
except ModuleNotFoundError as err:
    err_1 = str(err)
try: #For internal testing in this module 
	import RadioPropagation_v2 as myRadioPropagation
except ModuleNotFoundError as err:
    err_2 = str(err)


def MLfindGoodBS(dataframe, bs_filepath, ml_filepath, alpha=2.5, Z0=-20, distance_threshold=300, model=None):
    '''
    Find the good BS/elimilate the bad BS.  \n
    return 5 items: (1) df_good_bs, (2) df_bad_bs, (3) df_all_bs, (4) y_pred_test, (5) max_y_pred_test, (6) pred_region_gps\n
    dataframe: type`pandas DataFrame`   \n
    bs_filepath: `string`, the file path of the .xlsx/.csv of the base stations including the latitude & longitude of the BS    \n
    ml_filepath: `string`, the file path of the .h5 machine learning model  \n
    alpha: type `float` \n
    Z0: type `float`    \n
    distance_threshold: `float`, identify that BS as the bad BS if its distance calculated by the received RSSI is smaller/greater than the sum of real distance and distance_threshold
    '''

    df = dataframe.copy()
    #1.
    #Import BS list to define the column names of the ML data list
    #=>BS ID as column names, location as labels,
    bs_df = pd.read_excel(bs_filepath, index_col=0)
    #Drop that rows if the ['Latitude', 'Longitude'] columns contained NaN
    bs_df = bs_df.dropna(subset=['Latitude', 'Longitude'])
    bs_id_list = bs_df['Id'].unique().tolist()
    #Add two rows for storing GPS of that location
    column_name = np.append(np.array(['device','seqNumber']), bs_df['Id'].unique())
    column_name_df = pd.DataFrame(columns=column_name)
    print("> Number of BS in HK: {}".format(bs_df['Id'].count()))
    
    #2.
    #Make the content of the ML data set
    data_df_allinone = df.pivot_table(
        values='rssi',
        index=['device','seqNumber'],
        columns='bsId'
    )
    #Makes the index columns i.e. ['location','gps','file','seqNumber'] back to normal columns
    data_df_allinone.reset_index(inplace=True)
    #Concatenate the ML data set: column names df (from BS list) and the RSSI content df
    ml_data_df = pd.concat([column_name_df,data_df_allinone], axis=1, sort=False)
    ml_data_df = column_name_df.append(data_df_allinone,ignore_index=True, sort=False)
    
    #3.
    #Normalize the RSSI values of all BS
    ##Prepare, find the min RSSI and insert it to NaN cell
    insert_rssi_val = ml_data_df[bs_id_list].min().min()
    ml_data_df = ml_data_df.fillna(insert_rssi_val)
    ##Normalize the RSSI values of all BS
    df1 = normalizing_MinMax(ml_data_df,bs_id_list)
    ml_data_df.update(df1)
    
    #4.
    #Reshape the ML dataframe to fit to the CNN classifier
    df2 = ml_data_df.drop(['device','seqNumber'],axis=1).copy()
    x_test = reshapeDataToCNN(df2)
    
    #5.
    #CNN classifier performs classification
    ##Get CNN model
    if model == None:
        print("> Importing CNN model ......")
        model = getCNN(ml_filepath)
    else:
        print('> CNN model globally imported.')
    ##Test the trained CNN model, get the probability of each classk label
    y_pred_test = model.predict(x_test)
    print('> Prob. of predicted label:', y_pred_test) #[0].tolist())
    ##Take the class with the highest probability from the test predictions
    max_y_pred_test = np.argmax(y_pred_test, axis=1)
    pred_region_gps = classLabel2gps(max_y_pred_test[0]) #type: tuple
    print("> Predicted label: {},  region: {}".format(max_y_pred_test,pred_region_gps))
    
    #6.
    #Find good basestations df / remove bad basestations
    df_good_bs,df_bad_bs,df_all_bs = removeBadBS(dataframe=df, region_gps=pred_region_gps, alpha=alpha, Z0=Z0, distance_threshold=distance_threshold)
    
    return df_good_bs, df_bad_bs, df_all_bs, y_pred_test, max_y_pred_test, pred_region_gps

# Normalize features for training data set (values between 0 and 1)
def normalizing_MinMax(dataframe,bs_id_list):
    df = dataframe[bs_id_list].copy()
    min_rssi = df.min().min() #First .min() finds the minimum RSSI on every col
                              #Second .min() finds the minimum RSSI along row
    max_rssi = df.max().max()
    df = (df-min_rssi) / (max_rssi-min_rssi)
    # print("max RSSI: ",max_rssi)
    # print("min RSSI: ",min_rssi)
    return df

def reshapeDataToCNN(dataframe):
    """ Change the shape of the dataset,
    so that the shape of the data can be accepted by cnn"""
    df = dataframe.copy()
    df.insert(loc=len(df.columns),column="EXTRA", value=0.0)
    l1=[]
    l2=[]
    l3=[]
    for a,b in dataframe.iterrows():
        l1.append(b.tolist())

    for a in l1:
        for b in a:
            l2.append([b])
        l3.append(l2)
        l2 = []
    return np.array(l3)

#Load CNN model
def getCNN(filepath=None):
    #Import the trained CNN model
    model = keras.models.load_model(filepath)
    return model

def classLabel2gps(max_y_pred_test):
    labels_gps = [(22.29321,114.172877), (22.293025,114.173606), (22.293381,114.175046), (22.29373,114.175408)]
    return labels_gps[max_y_pred_test]

def removeBadBS(dataframe=None, region_gps=tuple(), alpha=2.5, Z0=-20.0, distance_threshold=300):
    """
    Return 3 dataframes. 1st: df_good_bs, 2nd: df_bad_bs, 3rd: df_all_bs
    1. Calculate the high/low expected RSSI thresholds between ML predicted target GPS and BS GPS
    2. Keep good base stations (i.e. rows in DF) if the value of the measured RSSI is in between the high AND low thresholds
    """
#     print("> Removing bad BS/Finding good BS ......")
    df = dataframe.copy()
    # df = df.sort_values(['dnnPredLoc','station'])
    #Insert a column to store the dnn expected RSSI
    col_numb = df.columns.get_loc("rssi")
    df.insert(loc=col_numb+1, column='nnRSSIThresholdHigh', value=None, allow_duplicates = False)
    df.insert(loc=col_numb+2, column='nnRSSIThresholdLow', value=None, allow_duplicates = False)
    #Set the origin of the x-y coord system
    origin_lat = df['OriginGPSLat'].values[0]
    origin_lng = df['OriginGPSLng'].values[0]
    coordsys = myCoordinateSystem.Location(origin_lat, origin_lng)
    #Calculate the high/low expected RSSI thresholds
    bs_list = df['bsId'].unique()
    # print("> Number of BS in measurement: {},  ".format(len(bs_list)), end='')
    for bsid in bs_list: #loop each BS in this measurement
        # print(bsid)
        condition = (df['bsId']==bsid)
        df1 = df.loc[condition,:]
        #Calculate the high and low expected RSSI threshold
        ##Distance between this BS and the device GPS location
        bsgpslat = df1['BaseStationLat'].iloc[0]
        bsgpslng = df1['BaseStationLng'].iloc[0]
        devicegps = region_gps
        devicegpslat = devicegps[0]
        devicegpslng = devicegps[1]
        distance = coordsys.distance_btw2gps(lat1=bsgpslat, lng1=bsgpslng, lat2=devicegpslat, lng2=devicegpslng)
        #The expected RSSI of this distance
        rssi_high_threshold = myRadioPropagation.log_Normal_RSSI_With_Distance(alpha=alpha,z0=Z0,distance=distance-distance_threshold)
        rssi_low_threshold = myRadioPropagation.log_Normal_RSSI_With_Distance(alpha=alpha,z0=Z0,distance=distance+distance_threshold)
        df.loc[condition,'nnRSSIThresholdHigh'] = rssi_high_threshold
        df.loc[condition,'nnRSSIThresholdLow'] = rssi_low_threshold            
    # print("GPS:",devicegpslat,devicegpslng)

    #Compare the measured RSSI with the high & low thresholds
    condition_gd_bs = (df['rssi'] <= df['nnRSSIThresholdHigh']) & (df['rssi'] >= df['nnRSSIThresholdLow'])
    df_good_bs = df[condition_gd_bs]
    df_good_bs = df_good_bs.groupby('seqNumber').filter(lambda x : len(x)>=3) #keep that measurement (i.e. unique device id and seqNumber) if number of BS >= 3
    df_bad_bs = df[~condition_gd_bs]
    df_all_bs = df

    #Show the performance
    # print("> After removing bad BS")
    df = df_good_bs
    bs_list = df['bsId'].unique().tolist()
    # print("Good BS no.: {},  ".format(len(bs_list)) ,end='')
    df = df_bad_bs
    bs_list = df['bsId'].unique().tolist()
    # print("Bad BS no.:",len(bs_list))
    
    #Return a new df without bad BS
    return df_good_bs,df_bad_bs,df_all_bs

def test():
    test_dict = {
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
    df = pd.DataFrame(test_dict)
    alpha = 2.7
    z0 = -20.0
    df_good_bs, df_bad_bs, df_all_bs, y_pred_test, max_y_pred_test, pred_region_gps = MLfindGoodBS(dataframe=df, 
                                            bs_filepath='mymodule/BS_list_2020.xlsx', 
                                            ml_filepath=r'mymodule/rssi_cnn_1d_1convlayer_10filtersize_v0 89 acc 50batch.h5',
                                            alpha=alpha, Z0=z0
                                            )
    print(df_all_bs.shape)
    print(df_all_bs['seqNumber'].unique())
    print(df_good_bs)

# test()



