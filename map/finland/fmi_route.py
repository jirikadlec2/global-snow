from bottle import run, route, template, request, response, TEMPLATE_PATH
import os
import fmi_stations, fmi_values

@route('/stations')
@route('/stations/')
def show_stations():
    return template('stations_table', rows=fmi_stations.get_snow_stations())

@route('/stations_csv')
@route('/stations.csv')
def show_stations_csv():
    response.content_type = 'text/csv; charset=UTF8'
    return template('stations_csv', rows=fmi_stations.get_snow_stations())
    
    
@route('/values/<fmisid>/<year>')
def show_values(fmisid, year):
    response.content_type = 'application/json; charset=UTF8'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
    return fmi_values.get_values(fmisid, int(year))


if __name__ == '__main__':
    TEMPLATE_PATH.insert(0, os.path.dirname(__file__))
    run(host='localhost', port=8080)