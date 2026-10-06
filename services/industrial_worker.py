"""Optional Modbus/OPC-UA polling worker for GeoTect.

Configure one protocol at a time with environment variables. This service is
disabled by default in docker-compose because field endpoints are deployment-specific.
"""
import os,time
import httpx

API=os.getenv("GEOTECT_API","http://localhost:8000")
INTERVAL=float(os.getenv("POLL_INTERVAL_SECONDS","10"))

def post(protocol,payload):
    r=httpx.post(f"{API}/api/v1/iot/normalize/{protocol}",json=payload,timeout=10)
    r.raise_for_status()
    print(r.json(),flush=True)

def run_modbus():
    from pymodbus.client import ModbusTcpClient
    host=os.environ["MODBUS_HOST"];port=int(os.getenv("MODBUS_PORT","502"))
    address=int(os.getenv("MODBUS_REGISTER","0"));scale=float(os.getenv("MODBUS_SCALE","1"))
    client=ModbusTcpClient(host,port=port)
    while True:
        if client.connect():
            result=client.read_holding_registers(address,count=1)
            if not result.isError():
                post("modbus",{"sensor_id":os.getenv("SENSOR_ID","modbus-1"),"sensor_type":os.getenv("SENSOR_TYPE","other"),"register_value":result.registers[0],"scale":scale,"unit":os.getenv("SENSOR_UNIT","")})
        time.sleep(INTERVAL)

def run_opcua():
    from opcua import Client
    url=os.environ["OPCUA_URL"];node_id=os.environ["OPCUA_NODE_ID"]
    client=Client(url);client.connect()
    try:
        node=client.get_node(node_id)
        while True:
            post("opcua",{"node_id":node_id,"sensor_type":os.getenv("SENSOR_TYPE","other"),"value":float(node.get_value()),"unit":os.getenv("SENSOR_UNIT","")})
            time.sleep(INTERVAL)
    finally: client.disconnect()

if __name__=="__main__":
    protocol=os.getenv("INDUSTRIAL_PROTOCOL","modbus").lower()
    (run_modbus if protocol=="modbus" else run_opcua)()
