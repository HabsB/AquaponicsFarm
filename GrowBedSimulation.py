from asyncore import write
import paho.mqtt.client as mqtt
import time
from math import floor
import random
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from kafka import KafkaProducer

# InfluxDB code

# You can generate a Token from the "Tokens Tab" in the UI
token = "mQPpWg2LhJcZwEjuF0hkYsXjBQ5gmQWAtRRyh1bqxVKZAHtf3N2LMNrlRRg3AZlZ0bBw4S2d8Hx_vYFVIaOlxQ=="
org = "UnivAQ"
bucket = "APMonitoring"

client = InfluxDBClient(url="http://0.0.0.0:8086", token=token)
# InfluxEnd

def json_serializer(data):
    return json.dumps(data).encode("utf-8")

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=json_serializer
)


def on_message(client, userdata, message):  
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)

GROW_BEDS = 3
COUNT_SENSORS = 2
iterator = 2* GROW_BEDS
broker_address="172.17.0.4" 

safeTemperature = {
    "minimum": 18.0,
    "maximum": 30.0,
    "average": 20.0,
}

safePhValue = {
    "minimum": 6,
    "maximum": 9,
    "average": 7.5,
}

safeOxygenLevel = {
    "minimum": 5.0,
    "maximum": 7.0,
    "average": 6.0,
}

safeWaterLevel = {
    "minimum": 700.0,
    "maximum": 1000.0,
    "average": 850.0,
}

baseTemperature = [ # 18 - 30 (safe)
    [
        safeTemperature["average"]
        for i in range(COUNT_SENSORS)
    ]
    for j in range(GROW_BEDS)
]

basePhValue = [ # 6-9 (safe)
    [
        safePhValue["average"]
        for i in range(COUNT_SENSORS)
    ]
    for j in range(GROW_BEDS)
]

baseOxygenValue = [ # 5-7 ppm (safe)
    [
        safeOxygenLevel["average"]
        for i in range(COUNT_SENSORS)
    ]
    for j in range(GROW_BEDS)
]

baseWaterLevelValue = [ # 700-1000 cc (safe)
    [
        safeWaterLevel["average"]
        for i in range(COUNT_SENSORS)
    ]
    for j in range(GROW_BEDS)
]

while True:
    for growbed in range(GROW_BEDS):
        for sensor in range(COUNT_SENSORS):
            temperatureSensor = mqtt.Client("GB"+str(growbed+1)+'-'+"S"+str(sensor+1))
            temperatureSensor.on_message = on_message
            temperatureSensor.connect(broker_address)
            baseTemperature[growbed][sensor] += round(random.uniform(-0.5, 0.5), 2) #temperatureChangeFactor

            publishableTemperatureDataObject = {
                "component": 'Growbed',
                "type": "TemperatureSensor",
                "componentId": "GB"+str(growbed+1)+'-'+"S"+str(sensor+1),
                "value": round(baseTemperature[growbed][sensor], 2),
            }

            publishableTemperatureDataString = json.dumps(publishableTemperatureDataObject)
            temperatureSensor.publish("farm/growbed/temperature", publishableTemperatureDataString)

            # Influx write data
            write_api = client.write_api(write_options=SYNCHRONOUS)

            #measurement, field, and fieldValue
            measurement = publishableTemperatureDataObject["component"] + 'Monitor' + publishableTemperatureDataObject["componentId"]
            field = publishableTemperatureDataObject["type"] + publishableTemperatureDataObject["componentId"]
            fieldValue = str(baseTemperature[growbed][sensor])

            writableDataString = measurement + ",host=host1 " + field + '=' + fieldValue

            # Kafka Dispatch
            if(baseTemperature[growbed][sensor] >= 20.0):
                # j = json.dumps(publishableTemperatureDataObject)
                with open('anomaly_data.json', 'a') as f:
                    # f.write(j + ",\n")
                    json.dump(publishableTemperatureDataObject, f)
                    # f.close()
                producer.send("TempratureSensor", publishableTemperatureDataObject)
            # Kafka

            write_api.write(bucket, org, writableDataString)
            
            if baseTemperature[growbed][sensor] < safeTemperature["minimum"] or baseTemperature[growbed][sensor] > safeTemperature["maximum"]:
                time.sleep(0.25)
                baseTemperature[growbed][sensor] = safeTemperature["average"]

            # time.sleep(0.5)

            #Ph-Value Sensor
            phSensor = mqtt.Client("GB"+str(growbed+1)+'-'+"S"+str(sensor+1))
            phSensor.on_message = on_message
            phSensor.connect(broker_address)
            basePhValue[growbed][sensor] += round(random.uniform(-0.25, 0.25), 2) #temperatureChangeFactor

            publishablePhDataObject = {
                "component": 'Growbed',
                "type": "PhSensor",
                "componentId": "GB"+str(growbed+1)+'-'+"S"+str(sensor+1),
                "value": round(basePhValue[growbed][sensor], 2),
            }

            publishablePhDataString = json.dumps(publishablePhDataObject)
            phSensor.publish("farm/growbed/phValue", publishablePhDataString)

            # Influx write data
            write_api = client.write_api(write_options=SYNCHRONOUS)

            #measurement, field, and fieldValue
            measurement = publishablePhDataObject["component"] + 'Monitor' + publishablePhDataObject["componentId"]
            field = publishablePhDataObject["type"] + publishablePhDataObject["componentId"]
            fieldValue = str(basePhValue[growbed][sensor])

            writableDataString = measurement + ",host=host1 " + field + '=' + fieldValue

            write_api.write(bucket, org, writableDataString)
            
            if basePhValue[growbed][sensor] < safePhValue["minimum"] or basePhValue[growbed][sensor] > safePhValue["maximum"]:
                time.sleep(0.25)
                basePhValue[growbed][sensor] = safePhValue["average"]

            # time.sleep(0.5)

            #Oxygen Sensor
            oxygenSensor = mqtt.Client("GB"+str(growbed+1)+'-'+"S"+str(sensor+1))
            oxygenSensor.on_message = on_message
            oxygenSensor.connect(broker_address)
            baseOxygenValue[growbed][sensor] += round(random.uniform(-0.25, 0.25), 2) #temperatureChangeFactor

            publishableOxygenDataObject = {
                "component": 'Growbed',
                "type": "OxygenSensor",
                "componentId": "GB"+str(growbed+1)+'-'+"S"+str(sensor+1),
                "value": round(baseOxygenValue[growbed][sensor], 2),
            }

            publishableOxygenDataString = json.dumps(publishableOxygenDataObject)
            oxygenSensor.publish("farm/growbed/dissolvedOxygen", publishableOxygenDataString)

            # Influx write data
            write_api = client.write_api(write_options=SYNCHRONOUS)

            #measurement, field, and fieldValue
            measurement = publishableOxygenDataObject["component"] + 'Monitor' + publishableOxygenDataObject["componentId"]
            field = publishableOxygenDataObject["type"] + publishableOxygenDataObject["componentId"]
            fieldValue = str(baseOxygenValue[growbed][sensor])

            writableDataString = measurement + ",host=host1 " + field + '=' + fieldValue

            write_api.write(bucket, org, writableDataString)
            
            if baseOxygenValue[growbed][sensor] < safeOxygenLevel["minimum"] or baseOxygenValue[growbed][sensor] > safeOxygenLevel["maximum"]:
                time.sleep(0.25)
                baseOxygenValue[growbed][sensor] = safeOxygenLevel["average"]

            # time.sleep(0.5)


            #Water Level Sensor
            waterLevelSensor = mqtt.Client("GB"+str(growbed+1)+'-'+"S"+str(sensor+1))
            waterLevelSensor.on_message = on_message
            waterLevelSensor.connect(broker_address)
            baseWaterLevelValue[growbed][sensor] += round(random.uniform(-100.0, 100.0), 2) #temperatureChangeFactor

            publishableWaterDataObject = {
                "component": 'Growbed',
                "type": "WaterLevelSensor",
                "componentId": "GB"+str(growbed+1)+'-'+"S"+str(sensor+1),
                "value": round(baseWaterLevelValue[growbed][sensor], 2),
            }

            publishableWaterDataString = json.dumps(publishableWaterDataObject)
            waterLevelSensor.publish("farm/growbed/waterLevel", publishableWaterDataString)

            # Influx write data
            write_api = client.write_api(write_options=SYNCHRONOUS)

            #measurement, field, and fieldValue
            measurement = publishableWaterDataObject["component"] + 'Monitor' + publishableWaterDataObject["componentId"]
            field = publishableWaterDataObject["type"] + publishableWaterDataObject["componentId"]
            fieldValue = str(baseWaterLevelValue[growbed][sensor])

            writableDataString = measurement + ",host=host1 " + field + '=' + fieldValue

            write_api.write(bucket, org, writableDataString)
            
            if baseWaterLevelValue[growbed][sensor] < safeWaterLevel["minimum"] or baseWaterLevelValue[growbed][sensor] > safeWaterLevel["maximum"]:
                time.sleep(0.25)
                baseWaterLevelValue[growbed][sensor] = safeWaterLevel["average"]

            time.sleep(1)

