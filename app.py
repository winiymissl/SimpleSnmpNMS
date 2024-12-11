from flask import Flask, render_template

from flask import Flask, request
import requests
import json
from flask_cors import *
import http.client
from flask import Flask, jsonify
from flask_cors import CORS
from pysnmp.hlapi import *
import time
import json
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/get_token')
def get_token():
    user_name = "devnetuser"
    pwd = "Cisco123!"
    url = "https://sandboxdnac2.cisco.com/dna/system/api/v1/auth/token"
    response = requests.post(url, auth=(user_name, pwd)).json()
    token = ""
    if response:
        token = response['Token']
    return token


# 获取设备表头信息
@app.route('/getDeviceFromDNAC')
def getDeviceFromDNAC():
    url = "https://sandboxdnac2.cisco.com/dna/intent/api/v1/network-device"
    token = get_token()
    my_header = {'X-Auth-Token': token}
    response = requests.get(url, headers=my_header).json()
    response = response['response']
    print(response[0]['type'])
    my_id = 1
    result = []
    for item in response:
        dic = {}
        dic['id'] = my_id
        dic['hostname'] = item['hostname']
        dic['family'] = item['family']
        dic['type'] = item['type']
        dic['ip'] = item['managementIpAddress']
        dic['time'] = item['lastUpdated']
        dic['role'] = item['role']
        dic['stat'] = item['reachabilityStatus']
        dic['uuid'] = item['id']
        dic['mac'] = item['macAddress']
        dic['hostname'] = item['hostname']
        dic['softwareType'] = item['softwareType']
        dic['softwareVersion'] = item['softwareVersion']
        dic['lastUpdated'] = item['lastUpdated']
        dic['serialNumber'] = item['serialNumber']
        dic['family'] = item['family']
        dic['memorySize'] = item['memorySize']
        my_id = my_id + 1
        result.append(dic)
    return json.dumps(result)


# 获取设备详细信息
@app.route('/get_device_detail')
def get_device_detail():
    url = "https://sandboxdnac2.cisco.com/dna/intent/api/v1/network-device"
    token = get_token()
    my_header = {'X-Auth-Token': token}
    response = requests.get(url, headers=my_header).json()
    response = response['response']
    print(response[0]['type'])
    return json.dumps(response)


# 获取设备健康信息
@app.route('/get_device_health')
def get_device_health():
    url = "https://sandboxdnac2.cisco.com/dna/intent/api/v1/network-health"
    token = get_token()
    my_header = {'X-Auth-Token': token, 'Content-Type': 'application/json'}
    response = requests.get(url, headers=my_header, verify=False).json()
    return json.dumps(response)


def get_interface_names():
    """获取接口名称"""
    try:
        interface_names = []
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData('public', mpModel=1),
                   UdpTransportTarget(('localhost', 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity('IF-MIB', 'ifNumber', 0)))
        )

        if errorIndication or errorStatus:
            return []

        # num_interfaces = int(varBinds[0][1])
        num_interfaces = min(int(varBinds[0][1]), 5)  # 限制为最多5个接口

        for i in range(num_interfaces):
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                       CommunityData('public', mpModel=1),
                       UdpTransportTarget(('localhost', 161)),
                       ContextData(),
                       ObjectType(ObjectIdentity('IF-MIB', 'ifDescr', i+1)))
            )

            if not errorIndication and not errorStatus:
                interface_names.append(str(varBinds[0][1]))

        return interface_names
    except Exception as e:
        print(f"Error in get_interface_names: {str(e)}")
        return []

def get_interface_data():
    """获取接口数据"""
    try:
        interface_names = get_interface_names()
        if not interface_names:
            return {'error': 'Failed to get interface names'}
        print(interface_names)
        oids = []
        for i in range(len(interface_names)):
            index = i + 1
            oids.extend([
                ObjectType(ObjectIdentity('IF-MIB', 'ifInOctets', index)),
                ObjectType(ObjectIdentity('IF-MIB', 'ifOutOctets', index)),
                ObjectType(ObjectIdentity('IF-MIB', 'ifOperStatus', index)),
                ObjectType(ObjectIdentity('IF-MIB', 'ifSpeed', index)),
                ObjectType(ObjectIdentity('IF-MIB', 'ifInErrors', index)),
                ObjectType(ObjectIdentity('IF-MIB', 'ifOutErrors', index)),
                ObjectType(ObjectIdentity('IF-MIB', 'ifInDiscards', index)),
                ObjectType(ObjectIdentity('IF-MIB', 'ifOutDiscards', index))
            ])

        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData('public', mpModel=1),
                   UdpTransportTarget(('localhost', 161)),
                   ContextData(),
                   *oids)
        )

        if errorIndication or errorStatus:
            return {'error': str(errorIndication or errorStatus)}

        data = {
            'interfaces': {}
        }

        metrics_per_interface = 8
        for i, name in enumerate(interface_names):
            base_index = i * metrics_per_interface
            data['interfaces'][name] = {
                'in_bytes': int(varBinds[base_index][1]),
                'out_bytes': int(varBinds[base_index + 1][1]),
                'status': 'up' if int(varBinds[base_index + 2][1]) == 1 else 'down',
                'speed': int(varBinds[base_index + 3][1]),
                'in_errors': int(varBinds[base_index + 4][1]),
                'out_errors': int(varBinds[base_index + 5][1]),
                'in_discards': int(varBinds[base_index + 6][1]),
                'out_discards': int(varBinds[base_index + 7][1])
            }

        return data

    except Exception as e:
        return {'error': str(e)}

@app.route('/get_interface_data')
def get_interface_data_route():
    """获取接口数据的API"""
    data = get_interface_data()
    if 'error' in data:
        return jsonify({
            'status': 'error',
            'error': data['error'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    else:
        return jsonify({
            'status': 'success',
            'data': data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })


from flask import jsonify
from datetime import datetime

@app.route('/get_topology')
def get_topology():
    """获取网络拓扑数据的API"""
    try:
        # 获取认证 token
        token = get_token()

        # 调用 DNA Center API
        url = "https://sandboxdnac2.cisco.com/dna/intent/api/v1/topology/physical-topology"
        headers = {'X-Auth-Token': token}
        response = requests.get(url, headers=headers).json()

        # 处理拓扑数据
        topology_data = process_topology_data(response)

        return jsonify({
            'status': 'success',
            'data': topology_data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

def process_topology_data(response):
    """处理拓扑数据的核心逻辑"""
    try:
        # 初始化数据结构
        linklist = []
        index1 = {}  # 设备标签到类型的映射
        index2 = {}  # 设备ID到标签的映射
        linklistf = []  # 最终的连接列表
        locatelist = {}  # 设备位置信息
        listfinal = {}  # 最终的拓扑关系

        # 获取链接和节点数据
        links = response['response']['links']
        nodes = response['response']['nodes']

        # 处理设备连接关系
        for link in links:
            linklist.append([link['source'], link['target']])

        # 处理设备信息
        wifi_count = 0
        for node in nodes:
            if node['deviceType'] == 'Cisco 1140 Unified Access Point':
                wifi_count += 1
            if node['deviceType'] not in ['wireless', 'wired']:
                index1[node['label']] = node['deviceType']
                index2[node['id']] = node['label']

        # 构建最终的连接列表
        for link in linklist:
            if link[0] in index2 and link[1] in index2:
                linklistf.append([index2[link[0]], index2[link[1]]])

        # 计算设备位置
        nodes_data = []
        links_data = []
        my_map = {}

        # 处理节点位置和信息
        for i, (device_name, device_type) in enumerate(index1.items()):
            node = {
                'id': i,
                'name': device_name,
                'type': device_type,
                'x': calculate_x_position(i),  # 根据需要实现位置计算
                'y': calculate_y_position(i)
            }
            nodes_data.append(node)
            my_map[device_name] = i

        # 处理连接关系
        for source_device in linklistf:
            if source_device[0] in my_map and source_device[1] in my_map:
                links_data.append({
                    'source': my_map[source_device[0]],
                    'target': my_map[source_device[1]]
                })

        # 添加无线接入点信息
        if wifi_count > 0:
            nodes_data.append({
                'id': len(nodes_data),
                'name': 'Unified AP',
                'type': 'access_point',
                'x': 140,
                'y': 860,
                'ap_count': wifi_count
            })

        return {
            'nodes': nodes_data,
            'links': links_data,
            'statistics': {
                'total_devices': len(nodes_data),
                'wireless_ap_count': wifi_count
            }
        }

    except Exception as e:
        raise Exception(f"Error processing topology data: {str(e)}")

def calculate_x_position(index):
    """计算节点X轴位置"""
    base_x = 50
    return base_x + (index * 100)  # 简单的线性分布

def calculate_y_position(index):
    """计算节点Y轴位置"""
    base_y = 50
    return base_y + (index * 80)  # 简单的线性分布

if __name__ == '__main__':
    app.run()
