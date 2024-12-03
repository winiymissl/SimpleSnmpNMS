from pysnmp.hlapi import *

def get_snmp_data(ip, port, community):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(community, mpModel=1),
               UdpTransportTarget((ip, port)),
               ContextData(),
               ObjectType(ObjectIdentity('.1.3.6.1.2.1.1.5.0')))  # 获取系统名称
    )

    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        for varBind in varBinds:
            print(' = '.join([x.prettyPrint() for x in varBind]))

# 使用示例
get_snmp_data('180.201.131.215', 8090, 'campus')

