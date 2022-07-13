#!/bin/env python

import requests
import json
import hashlib
import base64
import time
import hmac
import getpass
import csv
import datetime

#Account Info
AccessId = getpass.getpass(prompt='Enter LM API Access ID: ')
AccessKey = getpass.getpass(prompt='Enter LM API Access Key: ')
Company = getpass.getpass(prompt='Enter LM Instance Name: ')

# Set LogicMonitor API connection with request params
def connection(httpVerb, resourcePath, queryParams, apiVersion):
  
    #Construct URL 
    url = 'https://'+ Company +'.logicmonitor.com/santaba/rest' + resourcePath + queryParams

    #Get current time in milliseconds
    epoch = str(int(time.time() * 1000))

    #Concatenate Request details
    requestVars = httpVerb + epoch + resourcePath

    #Construct signature
    hmac1 = hmac.new(AccessKey.encode(),msg=requestVars.encode(),digestmod=hashlib.sha256).hexdigest()
    signature = base64.b64encode(hmac1.encode())

    #Construct headers
    auth = 'LMv1 ' + AccessId + ':' + signature.decode() + ':' + epoch
    headers = {'Content-Type':'application/json','Authorization':auth, 'X-Version':apiVersion}

    # Check value of the httpVerb to use the proper request method
    # Send delete method for removing datasources
    if(httpVerb == 'DELETE'):
        response = requests.delete(url, headers=headers)

        if response:
            return json.loads(response.content)
        else:
            return 'DataSource Not Found'
    # Send get request method for all other API calls
    else:
        response = requests.get(url, headers=headers)
        return json.loads(response.content)

# Obtain the total number of DataSources in the instance
def getDataSourceTotal():

    httpVerb ='GET'
    resourcePath = '/setting/datasources'
    queryParams = "?size=1"
    apiVersion = '1'

    response = connection(httpVerb, resourcePath, queryParams, apiVersion)

    return response['data']['total']

# Get DataSoures in instance
def getDataSources():

    total = getDataSourceTotal()

    httpVerb ='GET'
    resourcePath = '/setting/datasources'
    apiVersion = '1'

    dataList = []

    for x in range(0, total, 1000):
        queryParams = "?size=1000&offset=" + str(x) + "&fields=id,displayName,name,description,appliesTo,version&sort=-id"
        response = connection(httpVerb, resourcePath, queryParams, apiVersion)
        for item in response['data']['items']:
            dataList.append(item)
        
    return dataList

# Get DataSource regitry details to obtain the DataSource repositoy status
def getDataSourceMetadata(id):

    httpVerb ='GET'
    queryParams = ''
    apiVersion = '3'

    resourcePath = '/setting/registry/metadata/datasource/' + str(id)
    data = connection(httpVerb, resourcePath, queryParams, apiVersion)
    return data

# Obtain the total number of assigned devices for the datasource
def getAssignedDeviceTotal(id):

    httpVerb ='GET'
    resourcePath = '/setting/datasources/' + str(id) + '/devices'
    queryParams = "?size=1"
    apiVersion = '1'

    response = connection(httpVerb, resourcePath, queryParams, apiVersion)

    return response['data']['total']


# Get the devices that are using the DataSource
def getAssignedDevices(id, deviceCount):

    httpVerb ='GET'
    apiVersion = '1'

    dataList = []
    resourcePath = '/setting/datasources/' + str(id) + '/devices'

    for x in range(0, deviceCount, 1000):
        queryParams = "?size=1000&offset=" + str(x) + "&fields=id,displayName,name,hasActiveInstance&sort=-id"
        response = connection(httpVerb, resourcePath, queryParams, apiVersion)
        for item in response['data']['items']:
            dataList.append(item)

    return dataList


# Get details of the device using the DataSource
def getAssignedDeviceDetails(id):

    httpVerb ='GET'
    #queryParams = '?size=1&fields=id,name,displayName,preferredCollectorGroupName,hostGroupIds'
    queryParams = '?size=1'
    apiVersion = '1'

    resourcePath = '/device/devices/' + str(id)
    data = connection(httpVerb, resourcePath, queryParams, apiVersion)
    return data['data']

# Get the device groups that contain the devices
def getDeviceGroups(id):
    groups = id.split(',')
    groupList = []

    httpVerb ='GET'
    queryParams = '?size=1&fields=id,name,fullPath'
    apiVersion = '1'

    for group in groups:
        resourcePath = '/device/groups/' + str(group)
        data = connection(httpVerb, resourcePath, queryParams, apiVersion)
        groupList.append(data['data'])
        print(data['data'])

# Append data to CSV file for documentation
def appendToDataSourceCsv(dataList):

    csv_columns = ["name", "displayName", "id", "description", "version", "appliesTo", "deviceCount", "status"]
    csv_filename = "RemovedDatasources.csv"

    with open(csv_filename, "w", newline="") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()

        for entry in dataList:
            writer.writerow(entry)

    print("DataSource CSV file written to local directory")

# Perform DELETE request using the DataSource ID
def removeDataSource(id):
    httpVerb = 'DELETE'
    queryParams = ''
    apiVersion = '1'

    resourcePath = '/setting/datasources/' + str(id)
    data = connection(httpVerb, resourcePath, queryParams, apiVersion)
    print(data)

def main():

    # Get timestamp when script begins
    start_datetime = print(str(datetime.datetime.now()))

    # Build list to store CSV data
    dataList = []

    # Get DataSources
    dataSources = getDataSources()

    # Iterate over DataSources
    for dataSource in dataSources:

        # Get DataSource Metadata
        metadata = getDataSourceMetadata(str(dataSource['id']))
        key = 'status'
        if key in metadata:
            status = metadata['status']
        else:
            status = 'Unpublished'
        deviceCount = getAssignedDeviceTotal(dataSource['id'])
        if deviceCount == 0:
            print('Removing DataSource: ' + dataSource['name'] + ' ' + str(dataSource['id']))

            row = {"name": dataSource['name'], "displayName": dataSource['displayName'], "id": dataSource['id'], "description": dataSource['description'], "version": dataSource['version'], "appliesTo": dataSource['appliesTo'], "deviceCount": deviceCount, "status": status}
            dataList.append(row)
                
    appendToDataSourceCsv(dataList)

    end_datetime = str(datetime.datetime.now())

    print("Starting: " + start_datetime)
    print("Completed " + end_datetime)

# Run main function
main()
