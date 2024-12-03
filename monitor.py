from pysnmp.hlapi import *

def monitor_mac_snmp():
    # 监控系统信息
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData('public'),
               UdpTransportTarget(('localhost', 161)),
               ContextData(),
               ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0)),
               ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysUpTime', 0)))
    )

    if errorIndication:
        print(f"错误: {errorIndication}")
    else:
        for varBind in varBinds:
            print(' = '.join([x.prettyPrint() for x in varBind]))

# 运行监控
monitor_mac_snmp()