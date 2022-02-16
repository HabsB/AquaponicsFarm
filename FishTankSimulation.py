from asyncore import write
import paho.mqtt.client as mqtt
import time
from math import floor
import random
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from rx import interval
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

FishTank = 4
iterator = FishTank
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

baseTemperature = []
basePhValue = []
baseOxygenValue = []
baseWaterLevelValue = []

for i in range(iterator):
    baseTemperature.append(safeTemperature["average"]),
    basePhValue.append(safePhValue["average"]),
    baseOxygenValue.append(safeOxygenLevel["average"]),
    baseWaterLevelValue.append(safeWaterLevel["average"]),
print (baseTemperature)
while True:
    # Temperature Sensor
    for i in range(iterator):
        temperatureSensor = mqtt.Client("S"+str(i+1)) #create new instance
        temperatureSensor.on_message = on_message
        temperatureSensor.connect(broker_address)

        baseTemperature[i] += round(random.uniform(-0.5, 0.5), 2) #temperatureChangeFactor

        publishableTemperatureDataObject = {
            "component": 'Tank',
            "type": "TemperatureSensor",
            "componentId": str(i+1),
            "value": round(baseTemperature[i], 2),
        }

        publishableTemperatureDataString = json.dumps(publishableTemperatureDataObject)
        temperatureSensor.publish("farm/tank/temperature", publishableTemperatureDataString)

        # Influx write data
        write_api = client.write_api(write_options=SYNCHRONOUS)

        #measurement, field, and fieldValue
        measurement = publishableTemperatureDataObject["component"] + 'Monitor' + publishableTemperatureDataObject["componentId"]
        field = publishableTemperatureDataObject["type"] + publishableTemperatureDataObject["componentId"]
        fieldValue = str(baseTemperature[i])

        writableDataString = measurement + ",host=host1 " + field + '=' + fieldValue

        # Kafka Dispatch
        if(baseTemperature[i] >= 20.0):
            j = json.dumps(publishableTemperatureDataObject)
            with open('anomaly_data.json', 'a') as f:
                f.write(j + ",\n")
                # f.write("\n")
                f.close()
            producer.send("TempratureSensor", publishableTemperatureDataObject)
        # Kafka

        write_api.write(bucket, org, writableDataString)
        
        if baseTemperature[i] < safeTemperature["minimum"] or baseTemperature[i] > safeTemperature["maximum"]:
            time.sleep(0.25)
            baseTemperature[i] = safeTemperature["average"]

        # time.sleep(0.5)

    # Ph-Value Sensor
    # for i in range(iterator):
        phSensor   = mqtt.Client("Ph"+str(i+1)) #create new instance
        phSensor.on_message = on_message
        phSensor.connect(broker_address)

        basePhValue[i] += round(random.uniform(-0.25, 0.25), 1) #phChangeFactor

        publishablePhDataObject = {
            "component": 'Tank',
            "type": "PhSensor",
            "componentId": str(i+1),
            "value": round(basePhValue[i], 2),
        }

        publishablePhDataString = json.dumps(publishablePhDataObject)
        phSensor.publish("farm/tank/phValue", publishablePhDataString)

        # Influx write data
        write_api = client.write_api(write_options=SYNCHRONOUS)

        #measurement, field, and fieldValue
        measurement = publishablePhDataObject["component"] + 'Monitor' + publishablePhDataObject["componentId"]
        field = publishablePhDataObject["type"] + publishablePhDataObject["componentId"]
        fieldValue = str(basePhValue[i])

        writableDataString = measurement + ",host=host1 " + field + '=' + fieldValue

        write_api.write(bucket, org, writableDataString)
        
        if basePhValue[i] < safePhValue["minimum"] or basePhValue[i] > safePhValue["maximum"]:
            time.sleep(0.25)
            basePhValue[i] = safePhValue["average"]

        # time.sleep(0.5)

    # Oxygen Sensor
    # for i in range(iterator):
        oxygenSensor   = mqtt.Client("Ox"+str(i+1)) #create new instance
        oxygenSensor.on_message = on_message
        oxygenSensor.connect(broker_address)

        baseOxygenValue[i] += round(random.uniform(-0.25, 0.25), 2) #oxygenLevelChangeFactor

        publishableOxygenDataObject = {
            "component": 'Tank',
            "type": "OxygenSensor",
            "componentId": str(i+1),
            "value": round(baseOxygenValue[i], 2),
        }

        publishableOxygenDataString = json.dumps(publishableOxygenDataObject)
        oxygenSensor.publish("farm/tank/dissolvedOxygen", publishableOxygenDataString)

        # Influx write data
        write_api = client.write_api(write_options=SYNCHRONOUS)

        #measurement, field, and fieldValue
        measurement = publishableOxygenDataObject["component"] + 'Monitor' + publishableOxygenDataObject["componentId"]
        field = publishableOxygenDataObject["type"] + publishableOxygenDataObject["componentId"]
        fieldValue = str(baseOxygenValue[i])

        writableDataString = measurement + ",host=host1 " + field + '=' + fieldValue

        write_api.write(bucket, org, writableDataString)

        if baseOxygenValue[i] < safeOxygenLevel["minimum"] or baseOxygenValue[i] > safeOxygenLevel["maximum"]:
            time.sleep(0.25)
            baseOxygenValue[i] = safeOxygenLevel["average"]

        # time.sleep(0.5)

    # Water-level Sensor
    # for i in range(iterator):
        waterLevelSensor = mqtt.Client("Ox"+str(i+1)) #create new instance
        waterLevelSensor.on_message = on_message
        waterLevelSensor.connect(broker_address)

        baseWaterLevelValue[i] += round(random.uniform(-100.0, 100.0), 2) #waterLevelChangeFactor

        publishableWaterDataObject = {
            "component": 'Tank',
            "type": "WaterLevelSensor",
            "componentId": str(i+1),
            "value": round(baseWaterLevelValue[i], 2),
        }

        publishableWaterDataString = json.dumps(publishableWaterDataObject)
        waterLevelSensor.publish("farm/tank/waterLevel", publishableWaterDataString)

        # Influx write data
        write_api = client.write_api(write_options=SYNCHRONOUS)

        #measurement, field, and fieldValue
        measurement = publishableWaterDataObject["component"] + 'Monitor' + publishableWaterDataObject["componentId"]
        field = publishableWaterDataObject["type"] + publishableWaterDataObject["componentId"]
        fieldValue = str(baseWaterLevelValue[i])

        writableDataString = measurement + ",host=host1 " + field + '=' + fieldValue

        write_api.write(bucket, org, writableDataString)

        if baseWaterLevelValue[i] < safeWaterLevel["minimum"] or baseWaterLevelValue[i] > safeWaterLevel["maximum"]:
            time.sleep(0.25)
            baseWaterLevelValue[i] = safeWaterLevel["average"]

        time.sleep(1)

