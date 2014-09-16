from bottle import run, route, template, response, TEMPLATE_PATH
import os
import fmi_stations

@route('/stations')
@route('/stations/')
def show_stations():
    return template('stations_table', rows=fmi_stations.get_snow_stations())

@route('/stations_csv')
@route('/stations.csv')
def show_stations_csv():
    response.content_type = 'text/csv; charset=UTF8'
    return template('stations_csv', rows=fmi_stations.get_snow_stations())


if __name__ == '__main__':
    TEMPLATE_PATH.insert(0, os.path.dirname(__file__))
    run(host='localhost', port=8080)