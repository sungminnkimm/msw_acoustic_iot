#!/usr/bin/python3
import json, sys, serial, threading
import paho.mqtt.client as mqtt
import os, signal
import time, datetime, base64, requests
import sched


scheduler = sched.scheduler(time.time, time.sleep)
i_pid = os.getpid()
argv = sys.argv

cellQ = {}
pictureQ = {}

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
    global pictureQ

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

    pictureQ['number'] = 0
    pictureQ['pid'] = ''
    pictureQ['seq'] = 0
    pictureQ['longitude'] = 0.0
    pictureQ['latitude'] = 0.0
    pictureQ['altitude'] = 0.0
    pictureQ['pic'] = ''
    
    # pictureQ['longitude'] = 127.4567
    # pictureQ['latitude'] = 37.38382
    # pictureQ['altitude'] = 32.5
    
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
    # global missisonCmd
    # global cellStatus
    global cellNum
    
    print("[lib_acoustic_iot]: mqtt msg received")
    #print(str(msg.payload.decode("utf-8")))
    missionCmd = str(msg.payload.decode("utf-8"))

    cellNum = parseControlData(missionCmd)
    # cellStatus = missionCmd[:2]
    # cellNum = missionCmd[3]
    # cellNum = missionCmd[0]

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
    position_data_topic = '/MUV/control/' + lib["name"] + '/' + lib["control"][1]
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

def parseControlData(controlMsg):
    
    controlObj = json.dumps(controlMsg)
    controlObj = json.loads(controlObj)

    # controlObj['msg']
    # controlObj['deviceId']
    cell = controlObj['value']
    return cell


def DropDevice(num):
    global missionPort
    global cellQ
    global pictureQ
    
    num_int = int(num)
    num_str = '0%d' % num_int
    cellid = num_str + num_str
    pictureQ['pid'] = 'wp%s' % num
    #missionPort.write(missionCmd)
    cellQ[cellid] = 'OP'
    serialCmd = cellQ[cellid] + cellid + '\r\n'
    missionPort.write(serialCmd.encode())
    print(cellQ)

def usbCam(count):

    print("[lib_acoustic_iot]: USB Camera activated")
    #os.system('pkill gpicview')
    directory = '/home/pi/Pictures/'
    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    filepath = directory + now + '.jpg'
    cmd = "fswebcam -r 1280x720 --no-banner " + filepath
    os.system(cmd)
    #os.system('gpicview ' + filepath + ' &')
    pub_image(filepath, count)

def pub_image(filepath, number):
    global pictureQ

    try: 
        data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
        encoded_data = Tobase64(filepath)

        pictureQ['number'] = number
        pictureQ['seq'] = 12
        pictureQ['longitude'] = 127.4567
        pictureQ['latitude'] = 37.38382
        pictureQ['altitude'] = 32.5
        pictureQ['pic'] = encoded_data

        pictureQ = json.dumps(pictureQ)
        send_data_to_msw(data_topic, pictureQ)
        pictureQ = json.loads(pictureQ)

    except (TypeError, ValueError):
        cartridge_init()
    except:
        print('[lib_acoustic.iot.pub_image]: error')

def Tobase64(filepath):
    if filepath:
        f = open(filepath, "rb")
        enc = base64.b64encode(f.read())
        f.close()
        return str(enc)[2:-1]

def send_data_to_msw(data_topic, obj_data):
    global lib_mqtt_client

    lib_mqtt_client.publish(data_topic, obj_data)

def clearPictures():
    os.system('rm -rfv /home/pi/Pictures/*')

if __name__ == '__main__':
    global missionPort
    global mqtt_received
    global cellNum

    
    mqtt_received = False

    my_lib_name = 'lib_acoustic_iot'

    try:
        lib = dict()
        with open(my_lib_name + '.json', 'r') as f:
            lib = json.dumps(f, indent=4)
            lib = json.loads(lib)
    except:
        lib = dict()
        lib["name"] = my_lib_name
        lib["target"] = 'armv6'
        lib["description"] = "[name] [portnum] [baudrate]"
        lib["scripts"] = './' + my_lib_name + ' /dev/ttyUSB3 115200'
        lib["data"] = ['']
        lib["control"] = ['']
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
            DropDevice(cellNum)
            scheduler.enter(0, 1, usbCam, argument=(1))
            scheduler.enter(5, 1, usbCam, argument=(2))
            scheduler.enter(10, 1, usbCam, argument=(3))
            scheduler.run()
            clearPictures()
            mqtt_received = False
            
    missionPortClose()
    
# python -m PyInstaller lib_acoustic_iot.py
