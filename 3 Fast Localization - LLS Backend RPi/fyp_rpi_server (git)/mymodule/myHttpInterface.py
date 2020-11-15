"""
# Originated by: Sing (2019-2020)
# Last Modified: 27th Feburary 2020
# Modified by: Sing (2019-2020)
# Description:
    (1) Convert the received HTTP JSON data (class <dict>) into pandas dataframe and
    (2) Check the BS list to add the BS lat & lng into the dataframe.
    (3) Return the dataframe after processing.
"""
import pandas as pd
import json
import requests  #for HTTP POST request
from datetime import datetime
import pytz

testlist = [
    [{'bsId': '6E23', 'rssi': -113.0, 'nbRep': 2, 'snr': 8.57},{'bsId': '790C', 'rssi': -113.0, 'nbRep': 2, 'snr': 8.57}, {'bsId': '80C7', 'rssi': -97.0, 'nbRep': 3, 'snr': 27.41}, {'bsId': '7C6B', 'rssi': -129.0, 'nbRep': 2, 'snr': 6.0}, {'bsId': '6C6B', 'rssi': -126.0, 'nbRep': 1, 'snr': 10.0}],
    {'lat': 22.292783054956907, 'lng': 114.20696752212505, 'radius': 5979, 'source': 2, 'status': 1},
    {'device': '3E81CB', 'time': '1590387742', 'data': 'd80baa82ed01ffff0300ff00', 'seqNumber': '2017', 'lqi': 'Good', 'linkQuality': '2', 'fixedLat': '0.0', 'fixedLng': '0.0', 'operatorName': 'SIGFOX_HongKong_Thinxtra', 'countryCode': '344', 'deviceTypeId': '5b0e41de3c8789741699c804'}
    ]
    
def json2dataframe(request,dict_ls=None):
    if dict_ls != None:
        rssi_dict_list, computedLocation_dict, args_dict = dict_ls
        pass
    else:
        json = request.get_json()
        args = request.args
        # Extract needed variables
        rssi_dict_list = json['rssi']
        computedLocation_dict = json['computedLocation']
        args_dict = args.to_dict()

##    print(rssi_dict_list,end='\n\n')
##    print(computedLocation_dict,end='\n\n')
##    print(args_dict,end='\n\n')
    # Get current date and time
    timezone = pytz.timezone('Asia/Hong_Kong')
    now = datetime.now(timezone)
    current_date = now.strftime("%Y%m%d")
    current_time = now.strftime("%H:%M:%S")

    # Combine 3 dict and store each dict values into a list
    sheets_ary = []
    combined_rssi_dict_list = []
    for item_dict in rssi_dict_list:
        item_dict.update(args_dict)
        item_dict.update(computedLocation_dict)
        # For posting on Google Sheets
        item_list = [current_date,current_time]
        values_in_an_item = list(item_dict.values())
        item_list.extend(values_in_an_item)
        sheets_ary.append(item_list)
        # For LLS positioning
        item_dict.update([('DateRecorded',current_date),('TimeRecorded',current_time)])
        combined_rssi_dict_list.append(item_dict)
    
    col = [key for key,val in item_dict.items()]
    col = col[-2:] + col[:-2]
    df = pd.DataFrame(combined_rssi_dict_list, columns=col)
    
    df = checkBS(df)
    col_name = ['PathLossExponent','ReferenceRSSI','DeviceLLSLat','DeviceLLSLng',
                'DeviceLLSX','DeviceLLSY','DeviceGPSLat','DeviceGPSLng',
                'LocalizationError']
    df_1 = pd.DataFrame(None, columns=col_name)
    df = pd.concat([df, df_1], sort=False)
    
    return df

def checkBS(dataframe):
    final_df = dataframe.copy()
    col_name = ['BaseStationLat','BaseStationLng','BaseStationHeight',
                'BaseStationRegion','SubDistrict','BaseStationX','BaseStationY',
                'OriginGPSLat','OriginGPSLng']
    df = pd.DataFrame(None, columns=col_name)
    final_df = pd.concat([final_df, df], sort=False)
    bs_df = pd.read_excel('/home/pi/Desktop/fyp_rpi_server/fyp base station lat+lng+xy+region 20200102.xlsx')
    #Start comparison between BS list and the extracted data
    #Assign the GPS and (x,y) etc. information into the extracted data
    for index,bs_row_df in bs_df.iterrows():
        bs_row_col_name = ['Latitude','Longitude','Elevation',
                           'Region','SubDistrict','CoorX','CoorY',
                           'OriginGPSLat','OriginGPSLng']
        final_df.loc[final_df['bsId']==bs_row_df['Id'],col_name] = bs_row_df[bs_row_col_name].tolist()
    return final_df

def dataframe2json(parameter_list):
    pass

""" Test """
##dataframe = json2dataframe(None, testlist)
##print(dataframe.to_dict(),end='\n\n')
##print(dataframe)
