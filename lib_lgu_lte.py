#!/usr/bin/python3
import json, sys, serial, threading
import paho.mqtt.client as mqtt
import os, signal

i_pid = os.getpid()
argv = sys.argv

lteQ = {}

def lteQ_init():
    global lteQ

    lteQ['frequency'] = 0
    lteQ['band'] = 0
    lteQ['bandwidth'] = 0
    lteQ['cell_id'] = ""
    lteQ['rsrp'] = 0.0
    lteQ['rssi'] = 0.0
    lteQ['rsrq'] = 0.0
    lteQ['bler'] = 0.0
    lteQ['tx_power'] = 0
    lteQ['plmn'] = ""
    lteQ['tac'] = 0
    lteQ['drx'] = 0
    lteQ['emm_state'] = ""
    lteQ['rrc_state'] = ""
    lteQ['net_op_mode'] = ""
    lteQ['emm_cause'] = 0
    lteQ['esm_cause'] = ""

#---MQTT----------------------------------------------------------------
def on_connect(client,userdata,flags, rc):
    if rc == 0:
        print('[msw_mqtt_connect] connect to ', broker_ip)
    else:
        print("Bad connection Returned code=", rc)


def on_disconnect(client, userdata, flags, rc=0):
	print(str(rc))


def on_message(client, userdata, msg):
    print(str(msg.payload.decode("utf-8")))


def msw_mqtt_connect(broker_ip, port):
    global lib_mqtt_client

    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)

    lib_mqtt_client.loop_start()
#-----------------------------------------------------------------------

def missionPortOpening(missionPortNum, missionBaudrate):
    global missionPort
    global lteQ
    global lib

    if (missionPort == None):
        try:
            missionPort = serial.Serial(missionPortNum, missionBaudrate, timeout = 2)
            print ('missionPort open. ' + missionPortNum + ' Data rate: ' + missionBaudrate)

        except TypeError as e:
            missionPortClose()
    else:
        if (missionPort.is_open == False):
            missionPortOpen()

            data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
            send_data_to_msw(data_topic, lteQ)

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


def lteReqGetRssi():
    global missionPort

    if missionPort is not None:
        if missionPort.is_open:
            atcmd = b'AT@DBG\r'
            missionPort.write(atcmd)

def send_data_to_msw (data_topic, obj_data):
    global lib_mqtt_client

    lib_mqtt_client.publish(data_topic, obj_data)


def missionPortData():
    global missionPort
    global lteQ

    try:
        lteReqGetRssi()
        missionStr = missionPort.readlines()

        end_data = (missionStr[-1].decode('utf-8'))[:-2]

        if (end_data == 'OK'):
            arrLTEQ = missionStr[1].decode("utf-8").split(", ")

            for idx in range(len(arrLTEQ)):
                arrQValue = arrLTEQ[idx].split(':')
                if (arrQValue[0] == '@DBG'):
                    lteQ['frequency'] = int(arrQValue[2])
                elif (arrQValue[0] == 'Band'):
                    lteQ['band'] = int(arrQValue[1])
                elif (arrQValue[0] == 'BW'):
                    lteQ['bandwidth'] = int(arrQValue[1][:-3])
                elif (arrQValue[0] == 'Cell ID'):
                    lteQ['cell_id'] = arrQValue[1]
                elif (arrQValue[0] == 'RSRP'):
                    lteQ['rsrp'] = float(arrQValue[1][:-3])
                elif (arrQValue[0] == 'RSSI'):
                    lteQ['rssi'] = float(arrQValue[1][:-3])
                elif (arrQValue[0] == 'RSRQ'):
                    lteQ['rsrq'] = float(arrQValue[1][:-2])
                elif (arrQValue[0] == 'BLER'):
                    lteQ['bler'] = float(arrQValue[1][:-2])
                elif (arrQValue[0] == 'Tx Power'):
                    lteQ['tx_power'] = int(arrQValue[1])
                elif (arrQValue[0] == 'PLMN'):
                    lteQ['plmn'] = arrQValue[1]
                elif (arrQValue[0] == 'TAC'):
                    lteQ['tac'] = int(arrQValue[1])
                elif (arrQValue[0] == 'DRX cycle length'):
                    lteQ['drx'] = int(arrQValue[1])
                elif (arrQValue[0] == 'EMM state'):
                    lteQ['emm_state'] = arrQValue[1]
                elif (arrQValue[0] == 'RRC state'):
                    lteQ['rrc_state'] = arrQValue[1]
                elif (arrQValue[0] == 'Net OP Mode'):
                    lteQ['net_op_mode'] = arrQValue[1]
                elif (arrQValue[0] == 'EMM Cause'):
                    lteQ['emm_cause'] = int(arrQValue[1])
                elif (arrQValue[0] == 'ESM Cause'):
                    lteQ['esm_cause'] = arrQValue[1].split(",")[0]
        else:
            pass

        data_topic = '/MUV/data/' + lib["name"] + '/' + lib["data"][0]
        lteQ = json.dumps(lteQ)

        send_data_to_msw(data_topic, lteQ)

        lteQ = json.loads(lteQ)

    except (TypeError, ValueError):
        lteQ_init()

    except serial.SerialException as e:
        missionPortError(e)


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
        lib["scripts"] = './' + my_lib_name + ' /dev/ttyUSB1 115200'
        lib["data"] = ['LTE']
        lib["control"] = []
        lib = json.dumps(lib, indent=4)
        lib = json.loads(lib)

        with open('./' + my_lib_name + '.json', 'w', encoding='utf-8') as json_file:
            json.dump(lib, json_file, indent=4)


    lib['serialPortNum'] = argv[1]
    lib['serialBaudrate'] = argv[2]

    broker_ip = 'localhost'
    port = 1883
    msw_mqtt_connect(broker_ip, port)

    lteQ_init()

    missionPort = None
    missionPortNum = lib["serialPortNum"]
    missionBaudrate = lib["serialBaudrate"]
    missionPortOpening(missionPortNum, missionBaudrate)

    while True:
        missionPortData()

# python -m PyInstaller lib_lgu_lte.py
