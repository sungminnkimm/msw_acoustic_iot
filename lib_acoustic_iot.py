#!/usr/bin/python3
import json, sys, serial, threading
import paho.mqtt.client as mqtt
import os, signal
import time, datetime, base64, requests
import sched


scheduler = sched.scheduler(time.time, time.sleep())
i_pid = os.getpid()
argv = sys.argv

cellQ = {}

# url_Mobius = 'http://[64:FF9B::CBFD:80AC]:7579'

# headers = {
#    'Accept': 'application/json',
#    'X-M2M-RI': '123sdfg45',
#    'X-M2M-Origin': 'S20170717074825768bp21',
#    'Content-Type': 'application/json; ty=4'
# }

#open OP0101\r\n close CL0101\r\n
def cartridge_init():
    global cellQ

    print("[lib_acoustic_iot]: initializing cartridge")
    cellQ['0101'] = "CL"
    cellQ['0202'] = "CL"
    cellQ['0303'] = "CL"
    cellQ['0404'] = "CL"
    cellQ['0505'] = "CL"
    cellQ['0606'] = "CL"
    cellQ['0707'] = "CL"
    cellQ['0808'] = "CL"
    cellQ['0909'] = "CL"
    
    
#---MQTT----------------------------------------------------------------
def on_connect(client,userdata,flags, rc):
    if rc == 0:
        print('[lib_mqtt_connect] connect to', broker_ip)
    else:
        print("Bad connection Returned code=", rc)


def on_disconnect(client, userdata, flags, rc=0):
	print(str(rc))


def on_message(client, userdata, msg):
    global mqtt_received
    global missisonCmd
    global cellStatus
    global cellNum
    
    print("[lib_acoustic_iot]: mqtt msg received")
    #print(str(msg.payload.decode("utf-8")))
    missionCmd = str(msg.payload.decode("utf-8"))
    cellStatus = missionCmd[:2]
    cellNum = missionCmd[3]
    print(missionCmd)
    mqtt_received = True
    
    
def on_subscribe(client, userdata, mid, granted_qos):
    print("subscribed: " + str(mid) + " " + str(granted_qos))
    

def msw_mqtt_connect(broker_ip, port):
    global lib_mqtt_client
    global control_topic
    
    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    # topic is supposed to be lib["name"] = lib_lgu_lte
    control_topic = '/MUV/control/' + lib["name"] + '/' + lib["control"][0]
    lib_mqtt_client.subscribe(control_topic, 0)
    lib_mqtt_client.loop_start()
    # lib_mqtt_client.loop_forever()
#-----------------------------------------------------------------------

def missionPortOpening(missionPortNum, missionBaudrate):
    global missionPort
    global lib

    if (missionPort == None):
        try:
            missionPort = serial.Serial(missionPortNum, missionBaudrate, timeout = 2) #/dev/ttyUSB3, 115200
            print ('missionPort open. ' + missionPortNum + ' Data rate: ' + missionBaudrate)

        except TypeError as e:
            missionPortClose()
    else:
        if (missionPort.is_open == False):
            missionPortOpen()

            # data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
            # send_data_to_msw(data_topic, lteQ)

def missionPortOpen():
    global missionPort
    print('missionPort open!')
    missionPort.open()

def missionPortClose():
    global missionPort
    print('missionPort closed!')
    missionPort.close()


def missionPortError(err):
    print('[missionPort error]: ', err)
    os.kill(i_pid, signal.SIGKILL)

# def send_data_to_msw (data_topic, obj_data):
#     global lib_mqtt_client

#     lib_mqtt_client.publish(data_topic, obj_data)

def cellCmd(status, num):
    global missionPort
    global cellQ
    
    num_int = int(num)
    num_str = '0%d' % num_int
    cellid = num_str + num_str
    
    #missionPort.write(missionCmd)
    cellQ[cellid] = status
    serialCmd = cellQ[cellid] + cellid + '\r\n'
    missionPort.write(serialCmd.encode())
    print(cellQ)

def usbCam(filepath):
    print("[lib_acoustic_iot]: USB Camera activated")

    os.system('pkill gpicview')
    directory = '~/Pictures/'
    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    filepath = directory + now + '.jpg'
    cmd = "fswebcam -r 1280x720 --no-banner " + filepath
    os.system(cmd)
    os.system('gpicview ' + filepath + ' &')

# def wavTobase64(filepath):
#     #print(">> wavTobase64() is called")
#     if filepath:
#         f = open(filepath, "rb")
#         enc = base64.b64encode(f.read())
#         f.close()
#         #print("file exists")
#         return str(enc)[2:-1]

# def send_image_data_to_Mobius(url, con_image, timestamp):
#     t = datetime.datetime.fromtimestamp(timestamp)
#     #print("timestamp: ", timestamp, "t: ", t)
#     now = t.strftime('%Y%m%dT%H%M%S')
#     filename = '/home/pi/offline_acousticIoT/images/' + now + '.jpg'
#     encoded_data = wavTobase64(filename)
#     post_to_Mobius(url, con_image, encoded_data)

# def post_to_Mobius(url, con, encoded_data):
#     print(">> post_to_Mobius(",url,",",con,") is called")
#     url = url_Mobius + '/Mobius/raspberryPi/'+ con
#     payload = """{
#         "m2m:cin":{
#             "con":{
#                 "data": "%s"
#              }
#          }
#     }"""%(encoded_data)
#     #print("payload: ", payload)
#     #response = requests.request("POST", url, headers=headers, data=str(payload))
#     #print(response.text)
#     requests.request("POST", url, headers=headers, data=str(payload))

if __name__ == '__main__':
    global missionPort
    global mqtt_received
    global cellStatus
    global cellNum

    
    mqtt_received = False

    my_lib_name = 'lib_acoustic_iot'

    try:
        lib = dict()
        with open(my_lib_name + '.json', 'r') as f:
            lib = json.load(f)
            
            lib = json.loads(lib)
    except:
        lib = dict()
        lib["name"] = my_lib_name
        lib["target"] = 'armv6'
        lib["description"] = "[name] [portnum] [baudrate]"
        lib["scripts"] = './' + my_lib_name + ' /dev/ttyUSB3 115200'
        lib["data"] = ['LTE']
        lib["control"] = ['test']
        lib = json.dumps(lib, indent=4)
        lib = json.loads(lib)

        with open('./' + my_lib_name + '.json', 'w', encoding='utf-8') as json_file:
            json.dump(lib, json_file, indent=4)


    lib['serialPortNum'] = argv[1]
    lib['serialBaudrate'] = argv[2]
    
    control_topic = ''
    missionCmd = ''
    broker_ip = 'localhost'
    port = 1883
    
    msw_mqtt_connect(broker_ip, port)

    cartridge_init()
    
    missionPort = None
    missionPortNum = lib["serialPortNum"]
    missionBaudrate = lib["serialBaudrate"]
    
    missionPortOpening(missionPortNum, missionBaudrate)
    
    while 1:
        if mqtt_received:
            #print(cellStatus, cellNum)
            cellCmd(cellStatus, cellNum)
            scheduler.enter(0, 1, usbCam)
            scheduler.enter(5, 1, usbCam)
            scheduler.enter(10, 1, usbCam)
            scheduler.run()
            mqtt_received = False
            
    missionPortClose()
    
# python -m PyInstaller lib_acoustic_iot.py
