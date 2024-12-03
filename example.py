from flask import Flask, jsonify
from flask_cors import CORS
from pysnmp.hlapi import *
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 启用跨域支持

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

        num_interfaces = int(varBinds[0][1])
        num_interfaces = min(num_interfaces, 5)  # 最多获取5个接口

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

if __name__ == '__main__':
    app.run(debug=True)