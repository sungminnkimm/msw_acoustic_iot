#!/usr/bin/python3
import json, sys, serial
from tkinter import E
import paho.mqtt.client as mqtt
import os, signal
import time, datetime, base64
import sched


scheduler = sched.scheduler(time.time, time.sleep)
i_pid = os.getpid()
argv = sys.argv

cellQ = {}
pictureQ = {}
position_data_count = 0
control_data_count = 0

#open OP0101\r\n close CL0101\r\n
def cartridge_init():
    global cellQ
    global pictureQ

    print("[mission library, cartridge_init]: initializing cartridge")
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
    
#---MQTT----------------------------------------------------------------
def on_connect(client,userdata,flags, rc):
    global control_topic
    global position_data_topic

    if rc == 0:
        print('[mission library, on_connect] connect to', broker_ip)

        control_topic = '/MUV/control/' + lib["name"] + '/' + lib["control"][0]
        lib_mqtt_client.subscribe(control_topic, 0)

        position_data_topic = '/MUV/control/' + lib["name"] + '/' + 'global_position_int'
        lib_mqtt_client.subscribe(position_data_topic, 0)
    else:
        print("Bad connection Returned code=", rc)


def on_disconnect(client, userdata, flags, rc=0):
	print(str(rc))


def on_message(client, userdata, msg):
    global mqtt_received
    global control_topic
    global position_data_topic
    global missionControl
    global positionData
    global control_data_count
    global position_data_count


    mqtt_msg = str(msg.payload.decode("utf-8"))

    if msg.topic == control_topic:
        control_data_count += 1
        print("[mission library, on_message, " + str(control_data_count) + "]: mqtt msg received from " + control_topic)
        missionControl = mqtt_msg
        # print(missionControl)
        mqtt_received = True

    elif msg.topic == position_data_topic:
        position_data_count += 1
        # print("[mission library, on_message, " + str(position_data_count) + "]: mqtt msg received from " + position_data_topic)
        positionData = mqtt_msg
        parsePositionData(positionData)
        # print(positionData)
    
def on_subscribe(client, userdata, mid, granted_qos):
    print("[mission library, on_subscribed]: " + str(mid) + " " + str(granted_qos))

def on_publish(client, userdata, mid):
    print('[mission library, on_publish]: ' + str(mid))

def msw_mqtt_connect(broker_ip, port):
    global lib_mqtt_client
    
    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    lib_mqtt_client.on_subscribe = on_subscribe
    lib_mqtt_client.on_publish = on_publish
    lib_mqtt_client.loop_start()
    # lib_mqtt_client.loop_forever()
#-----------------------------------------------------------------------

def missionPortOpening(missionPortNum, missionBaudrate):
    global missionPort
    global lib

    if (missionPort == None):
        try:
            missionPort = serial.Serial(missionPortNum, missionBaudrate, timeout = 2) #/dev/ttyUSB3, 115200
            print ('[mission library, missionPort] open. ' + missionPortNum + ' Data rate: ' + missionBaudrate)

        except TypeError as e:
            missionPortClose()
    else:
        if (missionPort.is_open == False):
            missionPortOpen()

            # data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
            # send_data_to_msw(data_topic, lteQ)

def missionPortOpen():
    global missionPort
    print('[mission library, missionPort] open!')
    missionPort.open()

def missionPortClose():
    global missionPort
    print('[mission library, missionPort] closed!')
    missionPort.close()


def missionPortError(err):
    print('[missionPort error]: ', err)
    os.kill(i_pid, signal.SIGKILL)

def parsePositionData(data):
    global pictureQ

    try:
        positionObj = json.loads(data)
        if (('lat' in positionObj) and ('lon' in positionObj) and ('alt' in positionObj)):
            '''
            fc.global_position_int = {};
            fc.global_position_int.time_boot_ms = 123456789;
            fc.global_position_int.lat = 0;
            fc.global_position_int.lon = 0;
            fc.global_position_int.alt = 0;
            fc.global_position_int.vx = 0;
            fc.global_position_int.vy = 0;
            fc.global_position_int.vz = 0;
            fc.global_position_int.hdg = 65535;
            '''
            toFloatNum = 0.0000001
            pictureQ['longitude'] = round(toFloatNum * positionObj['lat'], 5)
            pictureQ['latitude'] = round(toFloatNum * positionObj['lon'], 5)
            pictureQ['altitude'] = round(toFloatNum * positionObj['alt'], 5)

            # print(positionObj['lon'], positionObj['lat'], positionObj['alt'])
            # print(pictureQ['longitude'], pictureQ['latitude'], pictureQ['altitude'])
        else:
            print('[mission library, parseControlData]: positionData missing')

    except (TypeError, ValueError):
        print('[mission library, parseControlData] Error: posigionData not valid')

    # print(data)

def parseControlData(controlMsg):
    
    try:
        controlObj = json.loads(controlMsg)
        if controlObj['value']:
            cell = int(controlObj['value'])
            return cell
        else:
            print('[mission library, parseControlData]: controlMsg cell number missing')
    except (TypeError, ValueError):
        print('[mission library, parseControlData] Error: controlMsg not valid')

    ''' 
    controlData['msg']: 'drop'
    controlData['deviceId']: 'D1234'
    controlData['value']: 3
    '''

def DropDevice(num):
    global missionPort
    global cellQ
    global pictureQ
    
    try:
        num_int = num
        if type(num) == int:
            num_str = '0%d' % num_int
            pictureQ['pid'] = 'wp%d' % num
        elif type(num) == str:
            num_str = '0%s' % num_int
            pictureQ['pid'] = 'wp%s' % num

        cellid = num_str + num_str

        if cellQ[cellid] != 'OP':
            cellQ[cellid] = 'OP'
        elif cellQ[cellid] == 'OP':
            print('[mission library, DropDevice]: {} already Open').format(cellid)

        serialCmd = cellQ[cellid] + cellid + '\r\n'

        if len(serialCmd) == 8: #OP0101\r\n
            missionPort.write(serialCmd.encode())
        elif len(serialCmd) != 8:
            print('[mission library, DropDevice]: cartridge control cmd length invalid')

    except (TypeError, ValueError):
        print('[mission library, DropDevice] Error: cartridge control cmd invalid')

def usbCam(count):

    print("[mission library, usbCam]: USB Camera activated")
    #os.system('pkill gpicview')

    print('[mission library, usbCam]: check valid directory')
    if os.path.exists('/home/pi/Pictures/'):
        directory = '/home/pi/Pictures/'
    else:
        os.system('mkdir /home/pi/Pictures')
        directory = '/home/pi/Pictures/'

    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    filepath = directory + now + '.jpg'
    cmd = "fswebcam -r 1280x720 -F 10 --no-banner " + filepath
    os.system(cmd)
    #os.system('gpicview ' + filepath + ' &')
    pub_image(filepath, count)

def pub_image(filepath, number):
    global pictureQ

    try: 
        data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
        encoded_data = Tobase64(filepath)

        pictureQ['number'] = int(number)
        pictureQ['seq'] = 12
        # pictureQ['longitude'] = 127.4567
        # pictureQ['latitude'] = 37.38382
        # pictureQ['altitude'] = 32.5
        pictureQ['pic'] = encoded_data

        pictureQ = json.dumps(pictureQ)
        send_data_to_msw(data_topic, pictureQ)
        pictureQ = json.loads(pictureQ)

    except (TypeError, ValueError):
        cartridge_init()
    except:
        print('[mission library, pub_image] Error')

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
    global missionControl
    global positionData

    
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
        lib["data"] = ['toGCS']
        lib["control"] = ['toUAV']
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
    
    firstTake = 0
    secondTake = firstTake + 5
    thirdTake = secondTake + 5

    while 1:
        if mqtt_received:
            #print(cellStatus, cellNum)
            cellNum = parseControlData(missionControl)
            DropDevice(cellNum)
            scheduler.enter(firstTake, 1, usbCam, argument=('1'))
            scheduler.enter(secondTake, 1, usbCam, argument=('2'))
            scheduler.enter(thirdTake, 1, usbCam, argument=('3'))
            scheduler.run()
            clearPictures()
            mqtt_received = False
            
    missionPortClose()
    
# python -m PyInstaller mission-library.py
