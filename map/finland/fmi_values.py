from lxml import etree
from datetime import date
import requests, json


FMI_APIKEY = "1cb8a6f3-d8f4-4ae7-8fc3-0b9449683cfb"


def get_url(api_key, fmisid, year):
    base_url = "http://data.fmi.fi/fmi-apikey/" + api_key + "/wfs?"
    req = "request=GetFeature"
    stid = "&fmisid=" + str(fmisid)
    qry = "&storedquery_id=fmi::observations::weather::daily::timevaluepair"
    tstart = date(year - 1, 10, 1)
    tend = date(year, 9, 30)       
    time = "&starttime=" + tstart.isoformat() + "&endtime=" + tend.isoformat()
    params="&parameters=snow"
    return base_url + req + stid + qry + time + params


def parse_fmi_values(service_url):
    r = requests.get(service_url)
    if r.status_code == 200:
        pars = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(r.content, pars)
        begin = ''
        series = []
    try:
        for element in root.iter():
            if 'beginPosition' in element.tag:
                begin = element.text
            if 'MeasurementTVP' in element.tag:
                dat = element[0].text[:10]
                raw_val = element[1].text
                #it is necessary to convert NaN to null for json
                if raw_val == "NaN":
                    val = None
                else:
                    val = float(raw_val)
                    
                series.append([dat, val]) 
                
                #series.append( [element[0].text[:10], float(element[1].text)] )
                #series = [float(v) for v in element.text.split()]
                
        return {"start": begin, "values": series}
    except:
        return "Parsing error: The Data or the url is not correctly formatted."
        
        
def get_values(fmisid, theYear):
    url = get_url(FMI_APIKEY, fmisid, year=theYear)
    #return url
    output = parse_fmi_values(url)
    return json.dumps(output, allow_nan=False)