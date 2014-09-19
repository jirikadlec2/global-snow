####
#
#   Date fetcher to read WaterML and extract data from each site.
#   To begin with the search will be limited to only a specific day.
#   All values obatined on that day will be averaged.
#   
#
####

import getvalues_python as dp
import numpy

##Config Settings : Will need to come from a UI or a web request? 

keyword = "Precipitation"
startDate = "2014-09-01T00:00:00"
endDate = "2014-09-20T00:00:00"

def generateResults(tlx,tly,brx,bry):

    sites,services = dp.getSitesinBBOX(tlx, tly, brx, bry,keyword)
    varCodes = dp.getVarCode(services,keyword)

    result=[]

    for site in sites:
        if site['servURL'] in varCodes.keys():
            vcSite = varCodes[str(site['servURL'])]
            values = dp.sendReq(site,vcSite,startDate,endDate)
            if values!= False and len(values)>0:
                datapoints = [float(i[0]) for i in values]
                avgVal = numpy.mean(datapoints)
                resultLine = {'Latitude': site['Latitude'],'Longitude': site['Longitude'], 'val' : avgVal}
                result.append(resultLine)
        
    return result


def generateResults2(tlx,tly,brx,bry):

    sites,services = getSitesinBBOX(tlx, tly, brx, bry,keyword)
    varCodes = getVarCode(services,keyword)

    result=[]

    for site in sites:
        if site['servURL'] in varCodes.keys():
            vcSite = varCodes[str(site['servURL'])]
            values = sendReq(site,vcSite,startDate,endDate)
            if values!= False and len(values)>0:
                datapoints = [float(i[0]) for i in values]
                avgVal = numpy.mean(datapoints)
                resultLine = {'Latitude': site['Latitude'],'Longitude': site['Longitude'], 'val' : avgVal}
                result.append(resultLine)
        
    return result           



#result is now ready to be sent to one of the interpolation alogrithm.
topLeftX = 12.5
topLeftY = 48.5
bottomRightX = 18.5
bottomRightY = 51.0


print generateResults2(topLeftX,topLeftY,bottomRightX,bottomRightY)
