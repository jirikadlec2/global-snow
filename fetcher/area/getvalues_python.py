##################HIS to CIWATER################
## Version 0.2
## Developed by : Rohit Khattar
## BYU
## Note : 
##############################################


#Import Required Libraries (These are included by default with python, hence no additional setups required)

import urllib2,urllib, json
from xml.dom import minidom
import xml.etree.ElementTree as ET

#Conversion factors? Each service might result in a different Unit
#TODO : This issue needs to be resolved by having a units library that
#will be able to provide conversion factors for any unit to any unit? 

def getVariablefromXML(xml,keyword):
    #XML Parsing is not working due to some namespace issues.
    #Doing a simple string search and then from there will extract the code
    pos1 = xml.find('<variableName>'+keyword)
    if pos1==-1:
        pos1= xml.find('&lt;variableName&gt;'+keyword)
    if not pos1 ==-1:
        pos2 = xml.rfind('variableCode vocabulary="', 0, pos1)
        pos3 = xml.find('"', pos2+26)
        pos4 = xml.find('&gt;', pos2)
        pos5 = xml.find('&lt;/variableCode&gt;',pos4)
        return xml[pos2+25:pos3]+":"+xml[pos4+4:pos5]
    else:
        return ""
    
    #To ADD Support for multiple precipitation values
    #TODO : Also change this to mindom module instead, use the object url to get the data

def getVarCode(services,keyword):
    #This function queries the server for the Variable code for our keyword
    varCodes={}
    for service in services:
        service1=service.replace("?WSDL",'/GetVariables?authToken=""')
        service2=service1.replace("?wsdl", '/GetVariables?authToken=""')
        req = urllib2.Request(service2)
        print service2
        try:
            response = urllib2.urlopen(req)
            the_page = response.read()
            var = getVariablefromXML(the_page,keyword)
            if not (var == "" or var is None):
                varCodes[service]=var
                print var
        except urllib2.HTTPError, error:
            print error.read() 
    return varCodes
    

def getSitesinBBOX(xmin,ymin,xmax,ymax,keyword):

    #Sending out a POST request to get data from HIS Central
    #Keyword: We are looking for Precip Data only now.



    url = 'http://hiscentral.cuahsi.org/webservices/hiscentral.asmx/GetSitesInBox2'
    values = {'xmin' : xmin,
          'xmax' : xmax,
          'ymin' : ymin,
          'ymax' : ymax,
          'conceptKeyword' : keyword,
            'networkIDs':""}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)

    try:
        response = urllib2.urlopen(req)
        the_page = response.read()
    except urllib2.HTTPError, error:
        print error.read()
    
    xmldoc = minidom.parseString(the_page)
    sitelist = xmldoc.getElementsByTagName('Site') 
    #Preapare List of sites

    sites=[]
    services = set()
    for site in sitelist:
        serviceURL = site.getElementsByTagName('servURL')[0].firstChild.nodeValue
        services.add(serviceURL);
        newSite = {'sitename': site.getElementsByTagName('SiteName')[0].firstChild.nodeValue,
                   'SiteCode': site.getElementsByTagName('SiteCode')[0].firstChild.nodeValue,
                   'servURL': serviceURL,
                   'Latitude': site.getElementsByTagName('Latitude')[0].firstChild.nodeValue,
                   'Longitude': site.getElementsByTagName('Longitude')[0].firstChild.nodeValue
                                 }
        sites.append(newSite)

    
    return sites,services

def getTSJSON(values,ts):
    return json.dumps(zip(values,ts))
    

def sendReq(site,varCode,startDate,endDate):
    #Define Parameters for data retrieval

    url =  site['servURL']#Service URL
    url=url.replace("?WSDL",'/GetValuesObject')
    url=url.replace("?wsdl", '/GetValuesObject')
    
    siteCode = site['SiteCode']
    variableCode = varCode
    
    threhold = "0.01" #rainfall below this will not be considered. $@TODO

    values = {'location' : siteCode,
          'variable' : variableCode,
          'startDate' : startDate,
          'endDate' : endDate,
          'authToken':""}

    print url,values
    
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)

    try:
        response = urllib2.urlopen(req)
        the_page = response.read()
    except urllib2.HTTPError, error:
        print error.read()
        return False
    
    values,ts = parseData(the_page)
    output = zip(values,ts)
    return output
    
def parseData(getvalues_data):

    #Data Parsing
    
    xmldoc = minidom.parseString(getvalues_data)
    valuelist = xmldoc.getElementsByTagName('value') 
    unit = xmldoc.getElementsByTagName('unitAbbreviation')[0].firstChild.nodeValue ##Need to check why is the Unit not being recognised. 
    if (unit!="mm"):
        print "Unit is not mm, please change the conversion factor in the script according to the unit"
        
    ##########CONVERSION FACTOR###########

    cFactor = 1

    values = []
    timeStamps = []

    for value in valuelist:
        values.append("%.2f" % (float(value.firstChild.nodeValue)*cFactor))
        timeStamps.append(str(value.attributes['dateTime'].value))
    
##    for i in range(len(values)):
##        temp = dataType + " "
##        time = timeStamps[i]
##        temp += time[:4] + " " + time[5:7] + " " + time[8:10] + " " + time[11:13] + " " + time[14:16]
##        temp += " " + values[i]
##        dataLines.append(temp)
##
##    #Write Data to the output file. 
##
##    thefile = open(opFile, 'w')
##    
##    for item in dataLines:
##        thefile.write("%s\n" % item)
##
##    thefile.close()
##    #Calculate duration as we are going to use that

    return values, timeStamps




#Function To process each site and display the list of sites to fetch data from

def userMenu(sites,varCodes):
    print "\nSites with data:\n"
    i=1
    for site in sites:
        if site['servURL'] in varCodes.keys():
            print str(i)+".)"+site['sitename']
            i+=1
    selection = input("\nPlease Select one: ")

    site = sites[selection-1]
    vcSite = varCodes[str(site['servURL'])]
    valuesJSON = sendReq(site,vcSite)
    return valuesJSON

def getJSON(sites):

    outputJSON = {'type': "FeatureCollection",'features' :[]}
    #Build Feature from site data

    for site in sites:
        feature = {
             "type": "Feature",
             "geometry": {"type": "Point", "coordinates": [site['Latitude'], site['Longitude']]},
             "properties": {"name": site['sitename'],"code": site['SiteCode'],"service": site['servURL'], }
            }
        outputJSON['features'].append(feature)
    
    return json.dumps(outputJSON)

##
##keyword = "Precipitation"
##startDate = "2000-06-13T00:00:00"
##endDate = "2000-07-14T00:00:00"
##sites,services = getSitesinBBOX(-113.466796875, 39.73253798438117, -112.05029296875, 40.23665188032004,keyword)
##geoJSON = getJSON (sites)
##varCodes = getVarCode(services,keyword)
##print userMenu(sites,varCodes) # This is the final values result. 


