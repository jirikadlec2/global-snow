from lxml import etree
from xml.etree import ElementTree
import requests


FMI_APIKEY = "1cb8a6f3-d8f4-4ae7-8fc3-0b9449683cfb"


def get_wfs_url(api_key):
    base_url = "http://data.fmi.fi/fmi-apikey/" + api_key + "/wfs?"
    req = "request=GetFeature"
    bbox = "&bbox=20,59,30,60"
    qry = "&storedquery_id=fmi::observations::weather::daily::timevaluepair"
    time = "&starttime=2014-01-01T00:00:00Z&endtime=2014-01-01T00:00:00Z"
    params="&parameters=snow"
    return base_url + req + bbox + qry + time + params


def parse_2_0(service_url):
    r = requests.get(service_url)
    if r.status_code == 200:
        pars = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(r.content, pars)

    try:
        if 'FeatureCollection' in root.tag:
            ts = etree.tostring(root)
            keys = []
            vals = []
            for_graph = []
            units, site_name, variable_url = None, None, None
            name_is_set = False
            for element in root.iter():
                if 'PointTimeSeriesObservation' in element.tag:  # Time, Value [, Point] --Good
                        for e in element:
                            if 'time' in e.tag:
                                keys.append(e.text)
                            if 'value' in e.tag:
                                vals.append(e.text)
                if 'uom' in element.tag:  # unit of measurement
                    units = element.text
                if 'MonitoringPoint' in element.tag: # location
                    for e in element.iter():
                        if 'name' in e.tag and not name_is_set:
                            site_name = e.text
                            name_is_set = True
                if 'observedProperty' in element.tag:  # variable
                    for a in element.attrib:
                        if 'href' in a:
                            variable_url = element.attrib[a]
            values = dict(zip(keys, vals))
            for k, v in values.items():
                t = time_to_int(k)
                for_graph.append({'x': t, 'y': float(v)})
            smallest_time = list(values.keys())[0]
            for t in list(values.keys()):
                if t < smallest_time:
                    smallest_time = t
            return {'time_series': ts,
                    'site_name': site_name,
                    'start_date': smallest_time,
                    'variable_name': variable_name,
                    'units': units,
                    'values': values,
                    'for_graph': for_graph,
                    'wml_version': '2.0'}
        else:
            return "Parsing error: The waterml document doesn't appear to be a WaterML 2.0 time series"
    except:
        return "Parsing error: The Data in the Url, or in the request, was not correctly formatted."