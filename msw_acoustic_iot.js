/**
 * Created by Il Yeup, Ahn in KETI on 2020-09-04.
 */

/**
 * Copyright (c) 2020, OCEAN
 * All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

// for TAS of mission

var mqtt = require('mqtt');
var fs = require('fs');
var spawn = require('child_process').spawn;

var my_msw_name = 'msw_acoustic_iot';

var fc = {};
var config = {};

try {                                   // for nCube-MUV (NodeJs)
    sortie_name = my_sortie_name
}
catch (e) {                             // for nCube-MUV-Python
    var sortie_name = process.argv[2]
}

config.name = my_msw_name;

try {
    try {           // for nCube-MUV (NodeJs)
        config.directory_name = msw_directory[my_msw_name];
        config.sortie_name = '/' + sortie_name;
        config.gcs = drone_info.gcs;
        config.drone = drone_info.drone;
        config.lib = [];
    }
    catch (e) {     // for nCube-MUV-Python
        config.directory_name = process.argv[3];
        config.sortie_name = '/' + sortie_name;
        config.gcs = process.argv[4];
        config.drone = process.argv[5];
        config.lib = [];
    }
}
catch (e) {
    config.sortie_name = '';
    config.directory_name = '';
    config.gcs = 'UTM_UVARC';
    config.drone = 'ACOU_IOT_TESTNAME';
    config.lib = [];
}

// library 추가
var add_lib = {};
try {
    add_lib = JSON.parse(fs.readFileSync('./' + config.directory_name + '/lib_acoustic_iot.json', 'utf8'));
    config.lib.push(add_lib);
}
catch (e) {
    add_lib = {
        name: 'lib_acoustic_iot',
        target: 'armv6',
        description: "[name] [portnum] [baudrate]",
        scripts: './lib_acoustic_iot /dev/ttyUSB3 115200',
        data: ['toGCS'],
        control: ['toUAV']
    };
    config.lib.push(add_lib);
}
// msw가 muv로 부터 트리거를 받는 용도
// 명세에 sub_container 로 표기
var msw_sub_muv_topic = [];

var msw_sub_fc_topic = [];
msw_sub_fc_topic.push('/Mobius/' + config.gcs + '/Drone_Data/' + config.drone + '/heartbeat');
msw_sub_fc_topic.push('/Mobius/' + config.gcs + '/Drone_Data/' + config.drone + '/global_position_int');
msw_sub_fc_topic.push('/Mobius/' + config.gcs + '/Drone_Data/' + config.drone + '/attitude');
msw_sub_fc_topic.push('/Mobius/' + config.gcs + '/Drone_Data/' + config.drone + '/battery_status');

var msw_sub_lib_topic = [];

function init() {
    if(config.lib.length > 0) {
        for(var idx in config.lib) {
            if(config.lib.hasOwnProperty(idx)) {
                if (msw_mqtt_client != null) {
                    for (var i = 0; i < config.lib[idx].control.length; i++) {
                        var sub_container_name = config.lib[idx].control[i];
                        //config.name missing in the original code
                        _topic = '/Mobius/' + config.gcs + '/Mission_Data/' + config.drone + '/' + config.name + '/' + sub_container_name;
                        msw_mqtt_client.subscribe(_topic);
                        msw_sub_muv_topic.push(_topic);
                        console.log('[msw_mqtt] msw_sub_muv_topic[' + i + ']: ' + _topic);
                    }

                    for (var i = 0; i < config.lib[idx].data.length; i++) {
                        var container_name = config.lib[idx].data[i];
                        var _topic = '/MUV/data/' + config.lib[idx].name + '/' + container_name;
                        msw_mqtt_client.subscribe(_topic);
                        msw_sub_lib_topic.push(_topic);
                        console.log('[lib_mqtt] lib_topic[' + i + ']: ' + _topic);
                    }
                }

                var obj_lib = config.lib[idx];
                setTimeout(runLib, 1000 + parseInt(Math.random()*10), JSON.parse(JSON.stringify(obj_lib)));
            }
        }
    }
}

function runLib(obj_lib) {
    try {
        var scripts_arr = obj_lib.scripts.split(' ');
        if(config.directory_name == '') {

        }
        else {
            scripts_arr[0] = scripts_arr[0].replace('./', '');
            scripts_arr[0] = './' + config.directory_name + '/' + scripts_arr[0];
        }

//         var run_lib = spawn('sudo', scripts_arr.slice(0));
//        var run_lib = spawn(scripts_arr[0], scripts_arr.slice(1));
        console.log('python3', [scripts_arr[0]+'.py', '/dev/ttyUSB3', '115200']);
        var run_lib = spawn('python3', [scripts_arr[0]+'.py', '/dev/ttyUSB3', '115200']);
//         var run_lib = spawn('python3', [scripts_arr[0]+'.py']);
        
        run_lib.stdout.on('data', function(data) {
            console.log('stdout: ' + data);
        });

        run_lib.stderr.on('data', function(data) {
            console.log('stderr: ' + data);
        });

        run_lib.on('exit', function(code) {
            console.log('exit: ' + code);

            setTimeout(runLib, 3000, obj_lib)
        });

        run_lib.on('error', function(code) {
            console.log('error: ' + code);
        });
    }
    catch (e) {
        console.log(e.message);
    }
}

var msw_mqtt_client = null;

msw_mqtt_connect('localhost', 1883);

function msw_mqtt_connect(broker_ip, port) {
    if(msw_mqtt_client == null) {
        var connectOptions = {
            host: broker_ip,
            port: port,
//              username: 'keti',
//              password: 'keti123',
            protocol: "mqtt",
            keepalive: 10,
//              clientId: serverUID,
            protocolId: "MQTT",
            protocolVersion: 4,
            clean: true,
            reconnectPeriod: 2000,
            connectTimeout: 2000,
            rejectUnauthorized: false
        };

        msw_mqtt_client = mqtt.connect(connectOptions);

        msw_mqtt_client.on('connect', function () {
            console.log('[msw_mqtt_connect] connected to ' + broker_ip);
            for(idx in msw_sub_fc_topic) {
                if(msw_sub_fc_topic.hasOwnProperty(idx)) {
                    msw_mqtt_client.subscribe(msw_sub_fc_topic[idx]);
                    console.log('[msw_mqtt] msw_sub_fc_topic[' + idx + ']: ' + msw_sub_fc_topic[idx]);
                }
            }
            
            for(idx in msw_sub_muv_topic) {
                if(msw_sub_muv_topic.hasOwnProperty(idx)) {
                    msw_mqtt_client.subscribe(msw_sub_muv_topic[idx]);
                    console.log('[msw_mqtt] msw_sub_muv_topic[' + idx + ']: ' + msw_sub_muv_topic[idx]);
                }
            }
        });

        msw_mqtt_client.on('message', function (topic, message) {
            for(var idx in msw_sub_muv_topic) {
                if (msw_sub_muv_topic.hasOwnProperty(idx)) {
                    if(topic == msw_sub_muv_topic[idx]) {
                        setTimeout(on_receive_from_muv, parseInt(Math.random() * 5), topic, message.toString());
                        break;
                    }
                }
            }

            for(idx in msw_sub_lib_topic) {
                if (msw_sub_lib_topic.hasOwnProperty(idx)) {
                    if(topic == msw_sub_lib_topic[idx]) {
                        setTimeout(on_receive_from_lib, parseInt(Math.random() * 5), topic, message.toString());
                        break;
                    }
                }
            }

            for(idx in msw_sub_fc_topic) {
                if (msw_sub_fc_topic.hasOwnProperty(idx)) {
                    if(topic == msw_sub_fc_topic[idx]) {
                        setTimeout(on_process_fc_data, parseInt(Math.random() * 5), topic, message.toString());
                        break;
                    }
                }
            }
        });

        msw_mqtt_client.on('error', function (err) {
            console.log(err.message);
        });
    }
}

function on_receive_from_muv(topic, str_message) {
    // console.log('[' + topic + '] ' + str_message);

    parseControlMission(topic, str_message);
}

function on_receive_from_lib(topic, str_message) {
    // console.log('[' + topic + '] ' + str_message);

    parseDataMission(topic, str_message);
}

function on_process_fc_data(topic, str_message) {
    // console.log('[' + topic + '] ' + str_message);

    var topic_arr = topic.split('/');
    fc[topic_arr[topic_arr.length-1]] = JSON.parse(str_message);

    parseFcData(topic, str_message);
}

setTimeout(init, 1000);

// 유저 디파인 미션 소프트웨어 기능
///////////////////////////////////////////////////////////////////////////////
function parseDataMission(topic, str_message) {
    try {
        // User define Code
        var obj_lib_data = JSON.parse(str_message);

        // if(fc.hasOwnProperty('global_position_int')) {
        //     Object.assign(obj_lib_data, JSON.parse(JSON.stringify(fc['global_position_int'])));
        // }
        str_message = JSON.stringify(obj_lib_data);
        

        ///////////////////////////////////////////////////////////////////////

        var topic_arr = topic.split('/');
        var data_topic = '/Mobius/' + config.gcs + '/Mission_Data/' + config.drone + '/' + config.name + '/' + topic_arr[topic_arr.length-1];
        // msw_mqtt_client.publish(data_topic + '/' + sortie_name, str_message);
        msw_mqtt_client.publish(data_topic, str_message);
    }
    catch (e) {
        console.log('[parseDataMission] data format of lib is not json');
    }
}
///////////////////////////////////////////////////////////////////////////////

function parseControlMission(topic, str_message) {
    try {
        // User define Code
        ///////////////////////////////////////////////////////////////////////

        var topic_arr = topic.split('/');
        var _topic = '/MUV/control/' + config.lib[0].name + '/' + topic_arr[topic_arr.length - 1];
        msw_mqtt_client.publish(_topic, str_message);
        console.log("[msw_acoustic_iot]: published to topic " + _topic, str_message)
    }
    catch (e) {
        console.log('[parseControlMission] data format of lib is not json');
    }
}

function parseFcData(topic, str_message) {
    // User define Code --> send FcData to mission library
    var topic_arr = topic.split('/');
    if(topic_arr[topic_arr.length-1] == 'global_position_int') {
        var _topic = '/MUV/control/' + config.lib[0].name + '/' + 'global_position_int'; // 'Req_enc'
        msw_mqtt_client.publish(_topic, str_message);
    }
    ///////////////////////////////////////////////////////////////////////
}
