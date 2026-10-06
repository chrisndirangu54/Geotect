from __future__ import annotations
from datetime import datetime,timezone
from typing import Any

def normalized_reading(sensor_id:str,sensor_type:str,value:float,unit:str,source:str,quality:float=1.0,observed_at:datetime|None=None)->dict:
    return {"sensor_id":sensor_id,"sensor_type":sensor_type,"value":float(value),"unit":unit,
            "observed_at":(observed_at or datetime.now(timezone.utc)).isoformat(),
            "provenance":{"source":source,"method":"iot","confidence":max(0,min(float(quality),1))}}

def parse_mqtt(topic:str,payload:dict[str,Any])->dict:
    return normalized_reading(
      str(payload.get("sensor_id") or topic.rsplit("/",1)[-1]),str(payload.get("sensor_type","other")),
      float(payload["value"]),str(payload.get("unit","")),f"mqtt:{topic}",float(payload.get("quality",1.0)))

def parse_lorawan(payload:dict[str,Any])->dict:
    decoded=payload.get("decoded_payload") or payload.get("object") or payload
    device=payload.get("deviceInfo",{}).get("deviceName") or payload.get("device_id") or decoded.get("sensor_id","lorawan-device")
    return normalized_reading(str(device),str(decoded.get("sensor_type","other")),float(decoded["value"]),str(decoded.get("unit","")), "lorawan",float(decoded.get("quality",1.0)))

def parse_modbus(sensor_id:str,register_value:float,scale:float,unit:str,sensor_type:str="other")->dict:
    return normalized_reading(sensor_id,sensor_type,float(register_value)*float(scale),unit,"modbus")

def parse_opcua(node_id:str,value:float,unit:str,sensor_type:str="other")->dict:
    return normalized_reading(node_id,sensor_type,value,unit,f"opcua:{node_id}")

SUPPORTED_PROTOCOLS={
 "mqtt":{"transport":"broker","parser":"parse_mqtt"},
 "lorawan":{"transport":"network-server webhook/MQTT","parser":"parse_lorawan"},
 "modbus":{"transport":"TCP/RTU gateway","parser":"parse_modbus"},
 "opcua":{"transport":"OPC-UA client","parser":"parse_opcua"}
}
