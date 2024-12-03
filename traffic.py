from pysnmp.hlapi import *

def get_traffic_data(ip, community, interface_index):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(community),
               UdpTransportTarget((ip, 161)),
               ContextData(),
               ObjectType(ObjectIdentity('IF-MIB', 'ifInOctets', interface_index)),
               ObjectType(ObjectIdentity('IF-MIB', 'ifOutOctets', interface_index)))
    )

    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        for varBind in varBinds:
            print(' = '.join([x.prettyPrint() for x in varBind]))

# 示例调用
get_traffic_data('192.168.1.1', 'public', 1)