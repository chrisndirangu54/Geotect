"""GeoTect MQTT/LoRaWAN telemetry worker.

Consumes JSON telemetry and forwards normalized readings to the GeoTect API.
LoRaWAN network servers such as ChirpStack can publish uplinks to the same
broker; device payloads are normalized by the API's protocol adapter.
"""
import json,os,time
import paho.mqtt.client as mqtt
import httpx

BROKER=os.getenv("MQTT_BROKER","localhost")
PORT=int(os.getenv("MQTT_PORT","1883"))
TOPIC=os.getenv("MQTT_TOPIC","geotect/#")
API=os.getenv("GEOTECT_API","http://localhost:8000")

def on_connect(client,userdata,flags,reason_code,properties=None):
    client.subscribe(TOPIC)

def on_message(client,userdata,msg):
    try:
        payload=json.loads(msg.payload.decode("utf-8"))
        protocol="lorawan" if "lorawan" in msg.topic.lower() or "deviceInfo" in payload else "mqtt"
        if protocol=="mqtt": payload["topic"]=msg.topic
        r=httpx.post(f"{API}/api/v1/iot/normalize/{protocol}",json=payload,timeout=10)
        r.raise_for_status()
        normalized=r.json()
        # Persistence/event-bus handoff belongs here; keep stdout useful for container logs.
        print(json.dumps({"event":"telemetry_normalized","reading":normalized}),flush=True)
    except Exception as exc:
        print(json.dumps({"event":"telemetry_error","topic":msg.topic,"error":str(exc)}),flush=True)

def main():
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    username=os.getenv("MQTT_USERNAME");password=os.getenv("MQTT_PASSWORD")
    if username: client.username_pw_set(username,password)
    client.on_connect=on_connect;client.on_message=on_message
    client.connect(BROKER,PORT,60)
    client.loop_forever()

if __name__=="__main__": main()
