'''
Functions:
1. Receive POST HTTP request (contains RSSI) from Sigfox backend
2. Perform LLS localization
3. Send the results back to the Google Sheets through Google Cloud Functions
'''
from flask import Flask, request, jsonify
import json
import requests  #for HTTP POST request
import pandas as pd
import tensorflow.keras as keras
# pd.set_option('display.max_columns', 100) #show more columns when printing a df
#Self python script
from mymodule import myHttpInterface
from mymodule.submodule import CoordinateSystem_v2 as myCoordinateSystem
import performLocalization

#Global variables
cnn = keras.models.load_model(r'mymodule/rssi_cnn_1d_1convlayer_10filtersize_v0 89 acc 50batch.h5')
last_seqNumber = int()

app = Flask(__name__)

@app.route("/helloworld")
def hello():
    return "Hello World!"

@app.route("/post", methods=['POST'])
def test_post():
    print('@@@@@@@@@')
    json_list = request.get_json()['0']
    print(json_list)
    print(type(json_list))
    
    return "Data received.", 200

@app.route("/lls", methods=['POST'])
def performLLS():
    global last_seqNumber
    device = request.args['device']
    new_seqNumber = request.args['seqNumber']
    print('####### START ###########')
    print('> device:',device)
    print('> new_seqNumber:',new_seqNumber)
    print('> last_seqNumber:',last_seqNumber)
    if (device != '3E81CB') & (device != '4171F4') & (device != '4190FE'): # Just allow my devices to use the lls API service
        msg = "> Unregistered device: {}".format(device)
        print(msg)
        return msg, 200
    if int(new_seqNumber) <= int(last_seqNumber): #prevent dupliucate http requests
        print('>>> new seqNumber:',new_seqNumber,'<= (last)',last_seqNumber)
        return '', 200
    else: #if new seqNumber did not see before, save it
        last_seqNumber = new_seqNumber
    dataframe = myHttpInterface.json2dataframe(request)
##    print(dataframe)
    print()
    
    #Perform LLS localization
    if dataframe['data'].values[0] == '0152441606ca219800000000':
        dataframe['data'] = '015450A506CE3CA100000000'
    llsResultDict = performLocalization.perform_lls(dataframe=dataframe,alpha=2.7,z0=-20,cnn=cnn)
    print('>',llsResultDict)
    print('============================================')
    
    alpha = llsResultDict.get('pathLossExponentAlpha')
    z0 = llsResultDict.get('referenceRSSIZ0')
    llsLat = llsResultDict.get('LLSLat')
    llsLng = llsResultDict.get('LLSLng')
    llsX = llsResultDict.get('LLSX')
    llsY = llsResultDict.get('LLSY')
    gpsLat = llsResultDict.get('GPSLat')
    gpsLng = llsResultDict.get('GPSLng')
    gpsIndicator = '1'
    #if SIM5320e cannot receive GPS signal, i.e. indoor
    if (gpsLat == '22.168598') & (gpsLng == '113.910168'):
        gpsLat = '22.302885'  #assume in PolyU
        gpsLng = '114.179233' #
        gpsIndicator = '0' #show that GPS signal is absent
        print('gpsIndicator:', gpsIndicator)
    localizationError = llsResultDict.get('LLSlocalizationError')
    mlRegion = llsResultDict['mlRegion']
    mlRegionGPSLat = llsResultDict['mlRegionGPSLat']
    mlRegionGPSLng = llsResultDict['mlRegionGPSLng']
    mlllsLat = llsResultDict['mlLLSLat']
    mlllsLng = llsResultDict['mlLLSLng']
    mllocalizationError = llsResultDict['mlLLSlocalizationError']
    if (not mlllsLat) & (not mlllsLat) & (not mllocalizationError): #if no good bs presents OR all bs are bad bs and are eliminated
        mlllsLat = mlRegionGPSLat #take the ML predicted region as LLS-ML location
        mlllsLng = mlRegionGPSLng #
        origin_gps_lat = 22.167615
        origin_gps_lng = 113.908514
        coordsys = myCoordinateSystem.Location(float(origin_gps_lat), float(origin_gps_lng))
        mllocalizationError = coordsys.distance_btw2gps(lat1=float(mlllsLat), lng1=float(mlllsLng), lat2=float(gpsLat), lng2=float(gpsLng))
    bs_numb = dataframe.shape[0]
    print('> bs_numb:',bs_numb)
    
    ##Insert the lls result into the original dataframe
    lls_list = ['None']*31
    lls_list.extend([alpha,z0,llsLat,llsLng,llsX,llsY,gpsLat,gpsLng,localizationError])
    dataframe.loc[-1] = lls_list  # adding a row
    dataframe.index = dataframe.index + 1  # shifting index
    dataframe.sort_index(inplace=True)
    dataframe = dataframe.replace(pd.np.nan,'')
    dataframe['seqNumber'] = new_seqNumber
    print(dataframe)
    
    #Send the LLS result
    data = {'0': dataframe.values.tolist()}
    ###Send http request to Google Cloud Functions and save data to Google Sheets
    URL = 'https://xxxxxxxxxxxxxxxx' #URL, use Google Cloud Functions under Google Cloud Platform, modify it by yourselves if you need
    r = requests.post(url=URL, json = data)
    print('>',r)
    ###Send the LLS result to ThingsBoard cloud (dashboard)
    access_token_gps = 'xxxxxxxxxxxxxxxx' #self API token, modify it by yourselves if you need
    access_token_lls_only = 'yyyyyyyyyyyyyyyyy' #self API token, modify it by yourselves if you need
    access_token_lls_ml = 'zzzzzzzzzzzzzzzzzzzzzz' #self API token, modify it by yourselves if you need
    data_gps = {'latitude': gpsLat,
                'longitude': gpsLng,
                'gps': gpsIndicator
                }
    data_lls_only = {'latitude': llsLat,
                     'longitude': llsLng,
                     'LE': localizationError,
                     'sigfox': '1',
                     'bs-numb': bs_numb
                     }
    data_lls_ml = {'latitude': mlllsLat,
                   'longitude': mlllsLng,
                   'LE': mllocalizationError,
                   'mlclass': 'region {}'.format(mlRegion)
                   }
    token_list = [access_token_gps,access_token_lls_only,access_token_lls_ml]
    data_list = [data_gps,data_lls_only,data_lls_ml]
##    print(data_list)
    ###Send lls results to ubidots (dashboard)
    ubidots_token = "xxxx-xxxxxxxxxxxxxxxxxxxxxxx"  # Put your TOKEN here
    device_label_gps = "gps"      # Put your device label here
    device_label_lls_only = "lls-only"  #
    device_label_lls_ml = "lls-ml"      #
    payload_gps = {
        "position": {"lat": gpsLat, "lng": gpsLng},
        "gps-just": gpsIndicator
        }
    payload_lls_only = {
            "position":{"lat": llsLat, "lng": llsLng},
            "LE": localizationError,
            "sigfox": '1',
            "bs-numb": bs_numb
            }
    payload_lls_ml = {
            "position":{"lat":mlllsLat, "lng":mlllsLng},
            "LE": mllocalizationError,
            'mlclass': mlRegion
            }
    device_label_list = [device_label_gps, device_label_lls_only, device_label_lls_ml]
    payload_list = [payload_gps, payload_lls_only, payload_lls_ml]
    print('>',payload_list)
    # ThingsBoard
    for token,data in zip(token_list,data_list):
        URL = 'http://demo.thingsboard.io:80/api/v1/{access_token}/telemetry'.format(access_token=token)
        try:
            r = requests.post(url=URL, json = data)
            print('> ThingsBoard:',r)
        except:
            pass
    # ubidots
    for device_label,payload in zip(device_label_list,payload_list):
        url = "https://things.ubidots.com"
        url = "{}/api/v1.6/devices/{}".format(url, device_label)
        headers = {"X-Auth-Token": ubidots_token, "Content-Type": "application/json"}
        try:
            r = requests.post(url=url, headers=headers, json=payload)
        except:
            pass
        print('> ubidots:',r)
    print('####### END ###########')
    return "Data received.", 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=52836, debug=True)
