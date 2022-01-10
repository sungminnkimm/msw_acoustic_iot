import sys
import paho.mqtt.client as mqtt
import time
argv = sys.argv

def on_connect(client,userdata,flags, rc):
    if rc == 0:
        print('[test.py] connect to ', broker_ip)
    else:
        print("Bad connection Returned code=", rc)


def on_disconnect(client, userdata, flags, rc=0):
	print(str(rc))


def on_message(client, userdata, msg):
    global mqtt_received
    global mqtt_msg

    print("[test.py]: mqtt msg received")
    mqtt_msg = str(msg.payload.decode("utf-8"))
    print(mqtt_msg)

    mqtt_received = True
    

def msw_mqtt_connect(broker_ip, port):
    global lib_mqtt_client

    lib_mqtt_client = mqtt.Client()
    lib_mqtt_client.on_connect = on_connect
    lib_mqtt_client.on_disconnect = on_disconnect
    lib_mqtt_client.on_message = on_message
    lib_mqtt_client.connect(broker_ip, port)
    lib_mqtt_client.subscribe('test', 0)

    lib_mqtt_client.loop_start()

if __name__ == '__main__':
    global mqtt_msg
    global mqtt_received

    mqtt_received = False
    broker_ip = 'localhost'
    port = 1883

    mymsg = argv[1]

    msw_mqtt_connect(broker_ip, port)
    while 1:
        if mqtt_received == False:
            print('=================' + mymsg)
            time.sleep(1)
        else: 
            with open(mqtt_msg + '.txt', 'w') as f:
                f.write(mqtt_msg)
            f.close()
            mqtt_received = False
