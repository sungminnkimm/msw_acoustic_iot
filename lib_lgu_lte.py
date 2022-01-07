#!/usr/bin/python3
import json, sys, serial, threading
import paho.mqtt.client as mqtt
import os, signal

i_pid = os.getpid()
argv = sys.argv

cellQ = {}

#open OP0101\r\n close CL0101\r\n
def cartridge_init():
    global cellQ

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
# def on_connect(client,userdata,flags, rc):
#     if rc == 0:
#         print('[msw_mqtt_connect] connect to ', broker_ip)
#     else:
#         print("Bad connection Returned code=", rc)


# def on_disconnect(client, userdata, flags, rc=0):
# 	print(str(rc))


# def on_message(client, userdata, msg):
#     print(str(msg.payload.decode("utf-8")))


# def msw_mqtt_connect(broker_ip, port):
#     global lib_mqtt_client

#     lib_mqtt_client = mqtt.Client()
#     lib_mqtt_client.on_connect = on_connect
#     lib_mqtt_client.on_disconnect = on_disconnect
#     lib_mqtt_client.on_message = on_message
#     lib_mqtt_client.connect(broker_ip, port)

#     lib_mqtt_client.loop_start()
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


# def lteReqGetRssi():
#     global missionPort

#     if missionPort is not None:
#         if missionPort.is_open:
#             atcmd = b'AT@DBG\r'
#             missionPort.write(atcmd)

# def send_data_to_msw (data_topic, obj_data):
#     global lib_mqtt_client

#     lib_mqtt_client.publish(data_topic, obj_data)

def cellAction(missionCmd):
    global missionPort
    global cellQ

    action = missionCmd[0] 
    cell_num = missionCmd[1]

    cellQ['0%d0%d' % cell_num] = action
    print(action + cellQ['0%d0%d' % cell_num])
    missionPort.write(action + cellQ['0%d0%d' % cell_num])

# def missionPortData():
#     global missionPort
#     global cellQ

#     try:
#         # lteReqGetRssi()
#         missionStr = missionPort.readlines()
#         print(missionStr)
#         # send_data_to_msw(data_topic, lteQ)

#     except (TypeError, ValueError):
#         cartridge_init()

#     except serial.SerialException as e:
#         missionPortError(e)


if __name__ == '__main__':
    global missionPort

    my_lib_name = 'lib_lgu_lte'

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
        lib["scripts"] = './' + my_lib_name + ' /dev/ttyUSB3 115200 OP 7'
        lib["data"] = ['LTE']
        lib["control"] = []
        lib = json.dumps(lib, indent=4)
        lib = json.loads(lib)

        with open('./' + my_lib_name + '.json', 'w', encoding='utf-8') as json_file:
            json.dump(lib, json_file, indent=4)


    lib['serialPortNum'] = argv[1]
    lib['serialBaudrate'] = argv[2]
    lib['serialCmd'] = tuple(argv[3], argv[4])

    broker_ip = 'localhost'
    port = 1883
    # msw_mqtt_connect(broker_ip, port)

    cartridge_init()

    missionPort = None
    missionPortNum = lib["serialPortNum"]
    missionBaudrate = lib["serialBaudrate"]
    missionCmd = lib['serialCmd']
    
    missionPortOpening(missionPortNum, missionBaudrate)

    cellAction(missionCmd)

    missionPortClose()

    # while True:
        # missionPortData()
        
        

# python -m PyInstaller lib_lgu_lte.py