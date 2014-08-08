#!/usr/bin/python
#
#-------------------------------------------------------------------------------
# $Id:  scripting_wcs_download.py  1.1  2013-05-21 $
# EC FP7 CryoLand
# Authors:  Christian Schiller <christian dot schiller at eox dot at>
#
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH, Vienna/Austria
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
#
# Version History:
# 1.1  --  -Added the listing of Start-/End-Dates for each available DatasetSeries 
#           when called with the  "-i"  switch
#          -The desired Output-CRS is now configurable in the settings section
#          -Minor changes applied to work in Python 2.7
#          -Bug corrected - if only single coverage was availabel not donwload was initiated
#           (2013-05-21)
# 1.0  --  -Initial release (based Python2.6)
#           Provides the full basic functionality to download Datasets 
#           (2013-03-15)
#
#

"""
<scripting_wcs_download.py>  -  Routine to access CryoLand's WCS interface and download 
    coverages according to the user specified Area of Interest (AOI), Time of Interest (TOI), 
    and DatasetSeries. 
    
    Usage: scripting_wcs_donwload.py [options] 

    Options: 
        -h                         show this help message and exit.
        -i                         provide a listing of the DataSetSeries offered by the CryoLand GeoPortal and exit.
                                   The Output goes to the screen. Now also provides Dates (Start/End) for each DatasetSeries
        -l <logfile>               path and filename where the <logfile> shall be written to. Provide this as the 
                                   first cmd-line option to ensure that all output is written to the logfile.  [Optional]
        -o <path>                  <path> where the received datasets are to be stored.  [Mandatory]
        -a <coordinate-values>     Area of Interest  [Mandatory]
        -t <time-values>           Time of Interest  [Mandatory]
        -d <datasetseries>         Name of the DatasetSeries to be accessed [Mandatory]


    <coordinate-values>:    describe the Bounding Box of the Area of interest, given 
                in Lat/Lon in the form of: 'minX, maxX, minY, maxY'. 
                Example:  -a '10.0, 11.0, 46.0,47.0'

    <time-values>:          describe the BeginTime and the EndTime of the Time of Interest
                i.e. the Period requested, in the form of:  'YYYY-MM-DDThh:mmZ, YYYY-MM-DDThh:mmZ'
                Example:  -t '2013-03-01T00:00Z, 2013-03-08T23:00Z'
    
    <datasetseries>:        the name of an available DatasetSeries. At the time of writing the the 
                following DatasetSeries are offered by CryoLand: 'daily_FSC_PanEuropean_Optical', 
                'daily_SWE_PanEuropean_Microwave', 'daily_FSC_Baltic_Optical', 'daily_FSC_Alps_Optical' 
                'multitemp_FSC_Scandinavia_Multisensor', 'daily_SCA_CentralEurope_Optical'
                
                Example:   -d 'daily_FSC_Alps_Optical'
                

    Syntax:  scripting_wcs_donwload.py -l /otherdir/otherdir2/logfilename.log -o /somedir/somedir2  
                  -a '10.0,11.0,46.0,47.0' -t '2013-03-01T00:00Z,2013-03-08T23:00Z' -d 'daily_FSC_Alps_Optical'
             scripting_wcs_donwload.py -h
             scripting_wcs_donwload.py -i
"""


import sys, os, getopt, string  
import urllib2,  socket
from xml.dom import minidom
from time import strftime,  gmtime




#### define some Basic Settings ####
# the CryoLand Server 
server='http://neso.cryoland.enveo.at'

# the desired Output-CRS -- Please only change the EPSG number (not the textual part)
# the currently supported CRSs are listed below
# output_crs="&outputcrs=epsg:4326"     # Geographic Coordinates (Lat, Lon) / WGS84
# output_crs="&outputcrs=epsg:3034"   # Lambert Conic Conformal / ETRS89
# output_crs="&outputcrs=epsg:3035"   # Lambert Azimuthal Equal Area / ETRS89
output_crs="&outputcrs=epsg:3857" # Spherical Mercator
# output_crs="&outputcrs=epsg:32622"  # UTM 22 / WGS84
# output_crs="&outputcrs=epsg:32632"  # UTM 32 / WGS84
# output_crs="&outputcrs=epsg:32633"  # UTM33 / WGS84
# output_crs="&outputcrs=epsg:32643"  # UTM43 / WGS84
# output_crs="&outputcrs=epsg:31287"  # Lambert Conic Conformal SP2 (LCC) / Militaer Geographisches Institut (MGI)



# default timeout for all sockets (in case a requests hangs)
timeout=60
socket.setdefaulttimeout(timeout)

# search tags for the request responses
xml_ID_tag=['wcseo:DatasetSeriesId', 'wcs:CoverageId' ]
xml_date_tag=['gml:beginPosition',  'gml:endPosition']
#global is_logfile
#is_logfile=0

#### End Basic Settings





def usage():
    """ pointing the Usage and Help information """
    print __doc__




def base_getcap_dss_sum():
    """
    Send a GetCapabilties request to the CryoLand GeoPortal, asking for the DatasetSeriesSummary, providing the listing 
    of the available DatasetSeries. This is executed when the script is called with the '-i' option. It is mainly intended
    for first time users who do not know which DatasetSeries are available.
    """
        # create the basic request url 
    base_dss_sum = ('/cryoland/ows?service=wcs&version=2.0.0&request=GetCapabilities&sections=DatasetSeriesSummary')
    request_url_dss_sum = server+base_dss_sum
    
## comment out the next line if you don't want the request written to the logfile/screen    
    print "URL requested:  ",  request_url_dss_sum

    try: 
            # access and the url & read the content
        res_dss_sum = urllib2.urlopen(request_url_dss_sum)
        getcap_xml = res_dss_sum.read()

## uncomment the following lines if you want to save the request response as a file (at the your HOME-directory        
#        try:
#            output = os.path.expandvars('$HOME')
#            file_dss_sum = open(output+'GetCapabilities_DatasetSeriesSummary.xml',  'w' )
#            file_dss_sum.write(getcap_xml)
#            file_dss_sum.flush()
#            os.fsync(file_dss_sum.fileno())
#            file_dss_sum.close()
#        except IOError:
#            except IOError as (errno, strerror):
#            print "I/O error({0}): {1}".format(errno, strerror)
#        except:
#            print "Unexpected error:", sys.exc_info()[0]
#            raise

            # parse the received xml and extract the DatasetSeriesIds
        dss_ids = parse_xml(getcap_xml, xml_ID_tag[0])
        dss_date1 = parse_xml(getcap_xml, xml_date_tag[0])
        dss_date2 = parse_xml(getcap_xml, xml_date_tag[1])

            # print the available DatasetSeriesIds to the screen
        print "The following DatasetSeries are available at CryoLand:"
        for i in range(len(dss_ids)): 
            print " - ", dss_ids[i] ,": \t", dss_date1[i], " - ", dss_date2[i]        
            
            # close the acces to the url
        res_dss_sum.close()
    

    except urllib2.URLError, url_ERROR:
        if hasattr(url_ERROR, 'reason'):
            print  strftime("%Y-%m-%dT%H:%M:%S%Z"),"- ERROR:  Server not accessible -", url_ERROR.reason
        elif hasattr(url_ERROR, 'code'):
            print strftime("%Y-%m-%dT%H:%M:%S%Z"),"- ERROR:  The server couldn\'t fulfill the request - Code returned:  ", url_ERROR.code,  url_ERROR.read()
         



def base_desccover(aoi_values, toi_values, dss):
    """
    Send a DescribeEOCoverageSet request to the CryoLand GeoPortal, asking for the available Coverages, according 
    to the user defined AOI, TOI, and DatasetSeries. The function returns the available CoveragesIDs.
    """
    base_desccov=('/cryoland/ows?service=wcs&version=2.0.0&request=DescribeEOCoverageSet&eoid=',  \
    '&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326(' ,  \
    ')&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326(',  \
    ')&subset=phenomenonTime(%22',  \
    '%22,%22',  \
    '%22)'  )

        # create the basic url 
    request_url_desccov = server+base_desccov[0]+dss+base_desccov[1]+aoi_values[0]+','+aoi_values[1]+base_desccov[2]+aoi_values[2]+','+aoi_values[3]+base_desccov[3]+toi_values[0]+base_desccov[4]+toi_values[1]+base_desccov[5]
    print request_url_desccov
    try: 
            # access and the url 
        res_desccov = urllib2.urlopen(request_url_desccov)

## uncomment the next line if you want the request written to the logfile/screen
#        print "URL requested:  ",  request_url_desccov, ' - ',  res_desccov.code

            # read the content of the url 
        descov_xml = res_desccov.read()
        print "descov_xml success!"
## uncomment the following lines if you want to save the request response as a file         
#        try: 
#            file_desccov = open(output+'DescribeEOCoverageSet.xml',  'w' )
#            file_desccov.write(descov_xml)
#            file_desccov.flush()
#            os.fsync(file_desccov.fileno())
#            file_desccov.close()
#        except IOError:
#            except IOError as (errno, strerror):
#            print "I/O error({0}): {1}".format(errno, strerror)
#        except:
#            print "Unexpected error:", sys.exc_info()[0]
#            raise


            # parse the received xml and extract the CoverageIds, close the url, return  the CoverageIds
        cids = parse_xml(descov_xml,  xml_ID_tag[1])
        res_desccov.close()
        print "base_desccover success!"
        return cids
     

    except urllib2.URLError, url_ERROR:
        if hasattr(url_ERROR, 'reason'):
            print  strftime("%Y-%m-%dT%H:%M:%S%Z"),"- ERROR:  Server not accessible -", url_ERROR.reason
        elif hasattr(url_ERROR, 'code'):
            print strftime("%Y-%m-%dT%H:%M:%S%Z"),"- ERROR:  The server couldn\'t fulfill the request - Code returned:  ", url_ERROR.code,  url_ERROR.read()
 




def parse_xml(in_xml, tag):
    """
    Function to parse the request results (GetCapabilities & DescribeEOCoverageSet) for the available 
    DataSetSeries (EOIDs) and CoveragesIDs.
    """
    
        # parse the xml - receved as answer to the request
    xmldoc = minidom.parseString(in_xml)
        # find all the tags (CoverageIds or DatasetSeriesIds)
    tagid_node = xmldoc.getElementsByTagName(tag)
        # number of found tags
    n_elem = tagid_node.length
    tag_ids=[]
        # store the found items
    for n  in range(0,n_elem):
        tag_ids.append(tagid_node[n].childNodes.item(0).data)
    
        # return the found items
    return tag_ids





def base_getcover(aoi_values, toi_values, dss, cov_ids):
    """
    Function to actually requesting and saving the available coverages on the local file system.
    """
    base_getcov=('/cryoland/ows?service=wcs&version=2.0.0&request=GetCoverage&coverageid=',  \
    '&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326(',  \
    ')&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326(',  \
    ')&rangesubset=gray' )

    print "running base_getcover"
    try: 
            # get the time of downloading - to be used in the filename (to differentiate if multiple AOIs of 
            # the same coverages are downloaded to the same output directory)
        dwnld_time = strftime("%Y%m%d%H%M%S",gmtime())
        
            # perform it for all CoverageIDs
        for COVERAGEID in cov_ids: 
                # construct the url for the WCS access
            request_url_getcov = server+base_getcov[0]+COVERAGEID+base_getcov[1]+aoi_values[0]+','+aoi_values[1]+base_getcov[2]+aoi_values[2]+','+aoi_values[3]+base_getcov[3]+output_crs
            print request_url_getcov
                # open and access the url
            res_getcov = urllib2.urlopen(request_url_getcov)
            
## comment out the next line if you don't want to have the requests written to the logfile
            print request_url_getcov, ' - ',  res_getcov.code

            try: 
                    # save the received coverages in the corresponding file at the output-directory
                outfile = COVERAGEID+'_'+dwnld_time+COVERAGEID[-4:]
                file_getcov = open(output+outfile, 'w+b')
                file_getcov.write(res_getcov.read())
                file_getcov.flush()
                os.fsync(file_getcov.fileno())
                file_getcov.close()
                res_getcov.close()
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
            except:
                print "Unexpected error:", sys.exc_info()[0]
                raise


    except urllib2.URLError, url_ERROR:
        if hasattr(url_ERROR, 'reason'):
            print  strftime("%Y-%m-%dT%H:%M:%S%Z"),"- ERROR:  Server not accessible -", url_ERROR.reason
        elif hasattr(url_ERROR, 'code'):
            print strftime("%Y-%m-%dT%H:%M:%S%Z"),"- ERROR:  The server couldn\'t fulfill the request - Code returned:  ", url_ERROR.code,  url_ERROR.read()
    except TypeError:
        pass




def cleanup(saveout, fsock_log):
    """ cleanup if a logfile was used """
    fsock_log.flush()
    os.fsync(fsock_log.fileno())
    fsock_log.close()
    sys.stdout = saveout



def main(argv, dsep):
    is_logfile=0
    """ main function - processing the command-line inputs """
    try:
        opts, args = getopt.getopt(argv, "hio:a:t:d:l:")
    except  getopt.GetoptError:
       usage()
       sys.exit(2)
    for opt, arg in opts: 
        if opt == '-h':  
                # provide help
            usage()
            sys.exit(0)
        elif opt == '-i':
                # initiate the GetCapabilities Request to gather the information about the available DatasetSeries
            base_getcap_dss_sum()
            sys.exit(0)
        elif opt == '-l':
                # specify the logfile 
            logfile = arg
            is_logfile=1
            saveout = sys.stdout
            fsock_log = open(logfile, 'a+')
            sys.stdout = fsock_log
        elif opt == '-o': 
                # specify where the received coverage shall be stored
            global output
            output = arg
            if output[-1] != dsep: 
                output = output+dsep
        elif opt == '-a': 
                # extract the provided AOI values
            aoi = arg
            aoi_values = string.splitfields(aoi, ',')
            print aoi
            for i in range(len(aoi_values)): aoi_values[i]=string.strip(aoi_values[i])
            if len(aoi_values) != 4: 
                print strftime("%Y-%m-%dT%H:%M:%S%Z"),"- ERROR:  in supplied AOI values",  aoi_values,  "\n"
                if is_logfile != 1: usage()
                sys.exit(2)
        elif opt == '-t': 
                # extract the provided TOI values
            toi = arg
            toi_values = string.splitfields(toi, ',')
            for i in range(len(toi_values)):  toi_values[i]=string.strip(toi_values[i])
            if len(toi_values) != 2: 
                print strftime("%Y-%m-%dT%H:%M:%S%Z"),"- ERROR:  in supplied TOI values",  toi_values,  "\n"
                if is_logfile != 1: usage()
                sys.exit(2)
        elif opt == '-d': 
                # extract the provided DatasetSeries name
            dss = arg

            
        # initiate the DescribeEOCoverageSet request
    cov_ids=base_desccover(aoi_values, toi_values, dss)

        # initiate the GetCoverage Request
    base_getcover(aoi_values, toi_values, dss, cov_ids)

        # if a log-file was used, close it
    if is_logfile != 0:
        cleanup(saveout, fsock_log)



if __name__ == "__main__":
        # check command-line input
    if len(sys.argv) == 1:
        usage()
        sys.exit(2)

        # check for OS Platform and set the Directory-Separator to be used
    dsep = "/"
    if sys.platform.startswith('win'):
        dsep = "\\"

    main(sys.argv[1:], dsep)

