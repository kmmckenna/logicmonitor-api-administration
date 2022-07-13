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
AccessId = getpass.getpass(prompt='LM API Access ID: ')
AccessKey = getpass.getpass(prompt='LM API Access Key: ')
Company = getpass.getpass(prompt='LM Instance Name: ')

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

# Get full list of datasources in repository
def getDataSources():
    
    # Get total number of datasources in repository for offset range
    total = getDataSourceTotal()

    httpVerb ='GET'
    resourcePath = '/setting/datasources'
    apiVersion = '1'

    # Create list to store datasource response
    dataList = []

    # Iterate over total number of datasources, starting at 0, and offsetting by 1000 for each query
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

# Append data to CSV file for documentation
def appendToDataSourceCsv(dataList):

    csv_columns = ["name", "displayName", "id", "description", "version", "appliesTo", "deviceCount", "status"]

    today = datetime.datetime.now()
    current_date = today.strftime("%m/%d/%Y")
    csv_filename = "DataSources - " + current_date + ".csv"

    with open(csv_filename, "w", newline="") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()

        for entry in dataList:
            writer.writerow(entry)

    print("DataSource CSV file written to local directory")

def main():

    # Build list to store CSV data
    dataList = []

    # Get DataSources
    dataSources = getDataSources()

    # Iterate over DataSources
    for dataSource in dataSources:

        # Get DataSource metadata to obtain repository status
        metadata = getDataSourceMetadata(str(dataSource['id']))
        key = 'status'

        # Check if DataSource metadata exists
        if key in metadata:
            status = metadata['status']
        else:
            # Mark the DataSource as "Unpublished" if the metadata is nonexistant
            status = 'Unpublished'

        # Get the total number of devices using the DataSource
        deviceCount = getAssignedDeviceTotal(dataSource['id'])
  
        # Build row of data for CSV file
        row = {"name": dataSource['name'], "displayName": dataSource['displayName'], "id": dataSource['id'], "description": dataSource['description'], "version": dataSource['version'], "appliesTo": dataSource['appliesTo'], "deviceCount": deviceCount, "status": status}
        
        # Append the new row to the data list
        dataList.append(row)
                
    appendToDataSourceCsv(dataList)

# Run main function
main()
