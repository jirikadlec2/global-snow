from lxml import etree
import requests


FMI_APIKEY = "1cb8a6f3-d8f4-4ae7-8fc3-0b9449683cfb"


def get_wfs_url(api_key):
    base_url = "http://data.fmi.fi/fmi-apikey/" + api_key + "/wfs?"
    req = "request=GetFeature"
    bbox = "&bbox=20,59,30,70"
    qry = "&storedquery_id=fmi::observations::weather::daily::timevaluepair"
    time = "&starttime=2014-01-01T00:00:00Z&endtime=2014-01-01T00:00:00Z"
    params="&parameters=snow"
    return base_url + req + bbox + qry + time + params


def parse_feature(observation_element):
    for e in observation_element.iter():
        if 'featureOfInterest' in e.tag:
            location = e[0][0][0][0][0]
            attr = location.attrib.itervalues().next()
            fmisid = attr.split('-')[2]
            name = e[0][1][0][0].text
            pos = e[0][1][0][1].text
            latlon = pos.split(' ')
            return (name, fmisid, latlon[0], latlon[1])
    return (None, None)
    
    
def parse_measurement(observation_element):
    for e in observation_element.iter():
        if 'MeasurementTVP' in e.tag:
            time = e[0].text
            val = e[1].text
            return (time, val)
    return (None, None)


def parse_fmi_stations(service_url):
    r = requests.get(service_url)
    if r.status_code == 200:
        pars = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(r.content, pars)
        series = []
    try:
        for element in root.iter():
            if 'PointTimeSeriesObservation' in element.tag:
                series.append(parse_feature(element))
        return series
    except:
        return "Parsing error: The Data in the Url, or in the request, was not correctly formatted."
        
        
def get_stations():
    return parse_fmi_stations(get_wfs_url(FMI_APIKEY))
