#!/usr/bin/env python
# encoding: utf-8

import argparse
import codecs
import urllib
import datetime
import logging
import time
import copy
import json
import re
import os
import sys

try:
    import requests
except:
    print "I need the 'requests' module! Please install:"
    print "pip install requests"
    sys.exit()

try:
    from bs4 import BeautifulSoup
except:
    print "I need the 'BeautifulSoup4' module! Please install:"
    print "pip install beautifulsoup4"
    sys.exit()

try:
    import pymysql as mysql
except:
    print "I need the 'MySQLdb' module! Please install:"
    print "pip install mysql-python"
    sys.exit()

DB_HOST = 'localhost'
DB_NAME = 'ogimetarctic'
DB_USER = 'ogimet'
DB_PASS = '2c506bbe'

conn, cursor = None, None

def fetch_and_parse_page(country, start_date, end_date, check=False, testfile=None):
    """
    Make HTTP calls to http://ogimet.com using the supplied parameters.
    Each of the returned HTML page will be passed to HTML parser function.

    Input:
        country: The country code (e.g: 'Spa')
        start_date: The start date of the report (e.g: '2013-04-10')
        end_date: The end date of the report (e.g: '2013-04-15')
        check: If true, check for duplication before inserting to `datavalues` table
        testfile: Get data from local HTML file rather than remote site. Used for debugging only.
    """
    try:
        y1, m1, d1 = start_date.split('-')
        y2, m2, d2 = end_date.split('-')
        start_date = datetime.date(year=int(y1), month=int(m1), day=int(d1))
        end_date = datetime.date(year=int(y2), month=int(m2), day=int(d2))

        if start_date > end_date:
            print 'Start date should be less than end date'
            sys.exit()

        site_vars = []

        for i in range(0, (end_date - start_date).days + 1):
            date = start_date + datetime.timedelta(days=i)
            year, month, day = date.isoformat().split('-')
            url = 'http://ogimet.com/cgi-bin/gsodres'
            query = {
                'lang': 'en',
                'mode': '1',
                'state': country,
                'ord': 'REV',
                'ano': year,
                'mes': month,
                'day': day,
                'ind': '',
                'ndays': '',
            }

            if testfile:
                content = open(testfile).read()
            else:
                print "\nCountry = %s, date = %s" % (country, date.isoformat())
                print "Fetching %s?%s..." % (url, urllib.urlencode(query)),
                t = time.time()
                r = requests.get(url, params=query)
                content = r.content
                print "%2.3f sec." % (time.time() - t)

            print "Parsing HTML page...",
            t = time.time()
            header, rows = parse_html(content)
            print "%2.3f sec." % (time.time() - t)

            if header is None or rows is None:
                continue

            if testfile:
                outfile = "%s_%s%s%s.csv" % (country, year, month, day)
                print "Saving to %s..." % outfile
                save_to_csv(outfile, header, rows)

            print "Saving to database...",
            t = time.time()
            save_to_database(copy.deepcopy(rows), header, date, check)
            print "%2.3f sec." % (time.time() - t)

            del header['Site']
            for row in rows:
                site_var = row['site']['code'] + ',' + ','.join(header)
                if site_var not in site_vars:
                    site_vars.append(site_var)

        print "\nUpdate series_catalog...",
        t = time.time()
        update_seriescatalog_table(site_vars)
        print "%2.3f sec." % (time.time() - t)

        print "Committing...",
        t = time.time()
        conn.commit()
        print "%2.3f sec." % (time.time() - t)

    except (IOError, ValueError, IndexError) as e:
        exit_nicely(e)

    except KeyError as e:
        exit_nicely("KeyError: undefined key: %s" % e)


def parse_html(html):
    """
    Parse the GSOD data in the given raw HTML string.

    Input:
        html: The HTML string

    Output:
        table_header: The column names. eg: Temp (max), Vis (km), etc.
        rows: The data
    """
    table_header, rows = None, []

    soup = BeautifulSoup(html)
    table_header = parse_table_header(html)

    if table_header is None:
        return None, None

    table = soup.find_all('table')[4]
    for i, row in enumerate(table.find_all('tr')):
        if i < 3: 
            continue
        cell = row.find_all('td')
        match = re.findall(r"'(.+?)'", cell[0].find('a').attrs.get('onmouseover', ''))
        name, code = match[1].split(',') if match else ('', '')

        match2 = re.match('(.+?)\s+\((.+?)\)', name)
        name, state = (match2.group(1), match2.group(2)) if match2 else (name, '')

        for j in range(1, len(cell)):
            m = re.findall(r"'(.+?)'", cell[j].attrs.get('onmouseover', ''))
            cell[j] = {
                'value': float(cell[j].text) if re.match(r"^-?[0-9.]+$", cell[j].text.strip()) else float(-9999),
                'desc': m[0] if len(m) else ''
            }

        def get_val(cell, idx):
            default = { 'value': float(-9999), 'desc': u'' }
            return cell[idx] if (type(idx) == int and idx < len(cell)) else default

        row = {
            'site': { 
                'name':  name.strip(), 
                'state': state.strip(), 
                'code':  code.strip() 
            },
            'Temp (max)':   get_val(cell, table_header.get('Temp (max)')),    
            'Temp (min)':   get_val(cell, table_header.get('Temp (min)')),
            'Temp (mean)':  get_val(cell, table_header.get('Temp (mean)')),
            'Hr (med)':     get_val(cell, table_header.get('Hr (med)')),
            'Wind (gust)':  get_val(cell, table_header.get('Wind (gust)')),
            'Wind (max)':   get_val(cell, table_header.get('Wind (max)')),
            'Wind (mean)':  get_val(cell, table_header.get('Wind (mean)')),
            'Vis (km)':     get_val(cell, table_header.get('Vis (km)')),
            'Prec (mm)':    get_val(cell, table_header.get('Prec (mm)')),
            'Snow (cm)':    get_val(cell, table_header.get('Snow (cm)')),
        }

        atts = re.split(r'\<br\>', match[0])
        atts = re.split(r' ', atts[0], 2)
        for att in atts:
            key, val = att.split('=')
            row['site'][key] = val
        rows.append(row)

    return table_header, rows


def parse_table_header(html):
    """
    Parse the header of the GSOD table and returns a dict of column names and the n-th indexes.

    The result of this function is needed since the table format is not always the same for each 
    country. For example, there are countries which don't have the 'snow' column. 
    """
    try:
        soup = BeautifulSoup(html)
        thead = soup.find_all('table')
        thead = thead[4] if thead and len(thead) > 4 else None
        thead = thead.find('thead') if thead else None

        if thead is None:
            raise Exception("Warning: unrecognized HTML structure!")

        thead = thead.find_all('tr')
        thead_r1 = thead[0] if thead else None
        thead_r2 = thead[1] if (thead and len(thead) >= 2) else None

        if thead_r1 is None or thead_r2 is None:
            raise Exception("Warning: unrecognized HTML structure!")

        thead_c1 = thead_r1.find_all('th')
        thead_c2 = thead_r2.find_all('th')
        idx, col_idx = 0, {}

        def map_key(key):
            key = key.lower().strip()
            if key == 'station':
                return 'Site'
            elif re.match('temperature.+\((min|mean|max)\)', key):
                return 'Temp (%s)' % re.sub('.+\((min|mean|max)\)', r'\1', key)
            elif re.match('hr.+med.*\(%\)', key):
                return 'Hr (med)' 
            elif re.match('wind.+\((max|mean|gust)\)', key):
                return 'Wind (%s)' % re.sub('.+\((max|mean|gust)\)', r'\1', key)
            elif re.match('(vis|prec|snow)\s*\((.+)\)', key):
                return re.sub('(vis|prec|snow)\s*\((.+)\)', r'\1 (\2)', key).capitalize()
            else:
                return key.capitalize()

        for c1 in thead_c1:
            span = int(c1.attrs.get('colspan', 0))
            if span > 0 and len(thead_c2) < span:
                raise Exception("unrecognized HTML structure!")
            elif span > 0:
                for c2 in thead_c2[0:span]:
                    col_idx[map_key("%s (%s)" % (c1.text, c2.text))] = idx
                    idx += 1
                del thead_c2[0:span]
            else:
                col_idx[map_key(c1.text)] = idx
                idx += 1

        # Remove unused columns
        for key in ['Pressure(mb) (slp)', 'Pressure(mb) (stn)', 'Diary']:
            if key in col_idx:
                del col_idx[key]

        return col_idx

    except Exception as e:
        print e


def save_to_database(values, header, date, check):
    """
    Given the list contains extracted data from HTML page, loop the 
    values and save each item to the right tables.
    """
    
    # Get the foreign keys we need for saving the values
    fkeys = get_foreign_keys()
    datetime_utc = '%s 00:00:00' % date

    try:
        for row in values:
            # Check if the site is already exists in the `sites` table
            # Site is something like: 'LA CORUNA', 'CIUDAD REAL'
            cursor.execute('SELECT SiteID FROM sites WHERE SiteCode=%s', row['site']['code'])

            if int(cursor.rowcount) == 0:
                # Site doesn't exist, add the new site with its attributes: 
                # latitude, longitude, and elevation
                a, b, c = row['site']['lat'][:-1].split('-')
                x, y, z = row['site']['lon'][:-1].split('-')
                lat = float(a) + float(b)/60 + float(c)/3600
                lon = float(x) + float(y)/60 + float(z)/3600
                alt = float(re.sub('\s+m.?$', '', row['site']['alt']))

                # If the site is in the south and west hemisphere then the latitude and 
                # longitude should be saved as negative numbers
                lat = -lat if row['site']['lat'][-1] == 'S' else lat
                lon = -lon if row['site']['lon'][-1] == 'W' else lon

                cursor.execute("""
                    INSERT INTO sites 
                      (
                        SiteCode, 
                        SiteName, 
                        State,
                        Latitude, 
                        Longitude, 
                        Elevation_m,
                        LatLongDatumID,
                        SiteType
                      ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                      (
                        row['site']['code'], 
                        row['site']['name'], 
                        row['site']['state'], 
                        lat, 
                        lon, 
                        alt,
                        3,
                        'Atmosphere'
                      ))
                # Get the new site's ID
                fkeys['SiteID'] = int(conn.insert_id())
            else:
                fkeys['SiteID'] = int(cursor.fetchone()['SiteID'])

            # Remove the site from the dictionary, so we can easily loop the dict 
            # to get the GSOD values
            del row['site']

            for var in row:
                if check == True:
                    # Check for duplication in the `datavalues` table
                    cursor.execute("""SELECT ValueID 
                                      FROM   datavalues
                                      WHERE  DateTimeUTC='%s' AND
                                             SiteID=%s AND 
                                             VariableID=%s AND 
                                             MethodID=%s AND
                                             SourceID=%s AND
                                             QualityControlLevelID=%s""" % (
                                             datetime_utc,
                                             fkeys['SiteID'], 
                                             fkeys['variables'][var], 
                                             fkeys['MethodID'], 
                                             fkeys['SourceID'],
                                             fkeys['QualityControlLevelID']))

                    if int(cursor.rowcount) > 0:
                        continue

                value, desc = row[var]['value'], row[var]['desc']

                # Check if desc already exists in the `qualifiers` table
                # desc is something like "Max. temperature taken from explicit Tmax. report"
                cursor.execute("""SELECT QualifierID 
                                  FROM qualifiers 
                                  WHERE QualifierDescription=%s""", desc)

                if int(cursor.rowcount) == 0:
                    # Qualifier doesn't exist, add new
                    cursor.execute("""INSERT INTO qualifiers (QualifierDescription) VALUES (%s)""", desc)
                    # Get the new qualifier's ID
                    fkeys['QualifierID'] = int(conn.insert_id())
                else:
                    fkeys['QualifierID'] = int(cursor.fetchone()['QualifierID'])

                # Save one GSOD value to the `datavalues` table
                cursor.execute("""
                    INSERT INTO datavalues 
                      (
                        DataValue, 
                        DateTimeUTC, 
                        LocalDateTime, 
                        UTCOffset, 
                        SiteID, 
                        VariableID, 
                        MethodID, 
                        QualityControlLevelID, 
                        SourceID, 
                        QualifierID
                      )
                    VALUES ( %s, %s, %s, 0, %s, %s, %s, %s, %s, %s)""", 
                      ( 
                        value, 
                        datetime_utc, 
                        datetime_utc,
                        fkeys['SiteID'], 
                        fkeys['variables'][var], 
                        fkeys['MethodID'], 
                        fkeys['QualityControlLevelID'], 
                        fkeys['SourceID'], 
                        fkeys['QualifierID']
                      ))

    except mysql.Error, e:
        exit_nicely("Error %d: %s" % (e.args[0], e.args[1]))


def update_seriescatalog_table(site_vars):
    """Update the `seriescatalog` table."""
    fkeys = get_foreign_keys()
    done = []

    cursor.execute("""SELECT MethodID, MethodDescription 
                      FROM methods 
                      WHERE MethodID=%s""", fkeys['MethodID'])
    method = cursor.fetchone()

    cursor.execute("""SELECT SourceID, Organization, SourceDescription, Citation 
                      FROM sources 
                      WHERE SourceID=%s""", fkeys['SourceID'])
    source = cursor.fetchone()

    cursor.execute("""SELECT QualityControlLevelID, QualityControlLevelCode 
                      FROM qualitycontrollevels 
                      WHERE QualityControlLevelID=%s""", fkeys['QualityControlLevelID'])
    quality = cursor.fetchone()

    for row in site_vars:
        vars = row.split(',')
        site_code = vars[0]
        del vars[0]

        cursor.execute("""SELECT SiteID, SiteCode, SiteName, SiteType 
                          FROM sites 
                          WHERE SiteCode=%s""", site_code)
        site = cursor.fetchone()

        for var in vars:
            if ("%s_%s" % (site_code, var)) in done:
                continue

            cursor.execute("""SELECT MAX(LocalDateTime) AS EndDateTime, 
                                     MAX(DateTimeUTC) AS EndDateTimeUTC,
                                     MIN(LocalDateTime) AS BeginDateTime,
                                     MIN(DateTimeUTC) AS BeginDateTimeUTC,
                                     COUNT(ValueID) AS ValueCount
                               FROM  datavalues
                               WHERE SiteID=%s AND 
                                     VariableID=%s AND 
                                     MethodID=%s AND
                                     SourceID=%s AND
                                     QualityControlLevelID=%s
                               GROUP BY SiteID, VariableID, MethodID, SourceID, QualityControlLevelID""", (
                                     site['SiteID'],
                                     fkeys['variables'][var],
                                     fkeys['MethodID'],
                                     fkeys['SourceID'],
                                     fkeys['QualityControlLevelID']))
            datavalues = cursor.fetchone()

            cursor.execute("""SELECT SeriesID 
                              FROM seriescatalog
                              WHERE SiteID=%s AND VariableID=%s""", 
                              (site['SiteID'], fkeys['variables'][var]))

            if int(cursor.rowcount):
                cursor.execute("""
                  UPDATE seriescatalog
                    SET
                      BeginDateTime=%s,
                      EndDateTime=%s,
                      BeginDateTimeUTC=%s,
                      EndDateTimeUTC=%s,
                      ValueCount=%s
                    WHERE
                      SiteID=%s AND
                      VariableID=%s""",
                    (
                      datavalues['BeginDateTime'],
                      datavalues['EndDateTime'],
                      datavalues['BeginDateTimeUTC'],
                      datavalues['EndDateTimeUTC'],
                      datavalues['ValueCount'],
                      site['SiteID'],
                      fkeys['variables'][var]
                    ))

                done.append("%s_%s" % (site_code, var)) 
                continue

            cursor.execute("""SELECT v.VariableID, v.VariableCode, v.VariableName, v.Speciation,
                                     v.VariableUnitsID, v.SampleMedium, v.ValueType, v.TimeSupport,
                                     v.TimeUnitsID, v.DataType, v.GeneralCategory,
                                     u1.UnitsName AS VariableUnitsName, u2.UnitsName AS TimeUnitsName
                              FROM   variables v, units u1, units u2
                              WHERE  v.VariableUnitsID=u1.UnitsID AND
                                     v.TimeUnitsID=u2.UnitsID AND
                                     v.VariableID=%s""", fkeys['variables'][var])
            variable = cursor.fetchone()

            cursor.execute("""
                INSERT INTO seriescatalog 
                  (
                    SiteID, 
                    SiteCode, 
                    SiteName, 
                    SiteType, 
                    VariableID,           
                    VariableCode, 
                    VariableName, 
                    Speciation,
                    VariableUnitsID,
                    VariableUnitsName,
                    SampleMedium,
                    ValueType,
                    TimeSupport,
                    TimeUnitsID,
                    TimeUnitsName,
                    DataType,
                    GeneralCategory,
                    MethodID, 
                    MethodDescription,   
                    SourceID, 
                    Organization,
                    SourceDescription, 
                    Citation,
                    QualityControlLevelID,         
                    QualityControlLevelCode,
                    BeginDateTime,
                    EndDateTime,
                    BeginDateTimeUTC,
                    EndDateTimeUTC,
                    ValueCount
                  )                                    
                VALUES 
                  (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                  )""", 
                  (
                    site['SiteID'],
                    site['SiteCode'],
                    site['SiteName'],
                    site['SiteType'],
                    variable['VariableID'],
                    variable['VariableCode'],
                    variable['VariableName'],
                    variable['Speciation'],
                    variable['VariableUnitsID'],
                    variable['VariableUnitsName'],
                    variable['SampleMedium'],
                    variable['ValueType'],
                    variable['TimeSupport'],
                    variable['TimeUnitsID'],
                    variable['TimeUnitsName'],
                    variable['DataType'],
                    variable['GeneralCategory'],
                    method['MethodID'], 
                    method['MethodDescription'],   
                    source['SourceID'], 
                    source['Organization'],
                    source['SourceDescription'], 
                    source['Citation'],
                    quality['QualityControlLevelID'],
                    quality['QualityControlLevelCode'],
                    datavalues['BeginDateTime'],
                    datavalues['EndDateTime'],
                    datavalues['BeginDateTimeUTC'],
                    datavalues['EndDateTimeUTC'],
                    datavalues['ValueCount']
                  ))

            done.append("%s_%s" % (site_code, var)) 


def get_foreign_keys():
    """Function to retrieve primary IDs that will be used as foreign keys later."""
    fkeys = {}
    try:
        cursor.execute("""SELECT SourceID 
                          FROM sources 
                          WHERE Organization=%s""", ('Ogimet'))

        if int(cursor.rowcount) == 0:
            cursor.execute("""
                INSERT INTO sources 
                  (
                    Organization, 
                    SourceLink, 
                    SourceDescription, 
                    Citation
                  ) 
                  VALUES ( %s, %s, %s, %s )""", 
                  (
                    'Ogimet', 
                    'http://www.ogimet.com', 
                    '', 
                    ''
                  ))
            fkeys['SourceID'] = int(conn.insert_id())
        else:
            fkeys['SourceID'] = int(cursor.fetchone()['SourceID'])

        desc = 'Data downloaded from Ogimet using custom script'
        cursor.execute("""SELECT MethodID 
                          FROM methods 
                          WHERE MethodDescription=%s""", desc)

        if int(cursor.rowcount) == 0:
            cursor.execute('INSERT INTO methods (MethodDescription) VALUES (%s)', desc)
            fkeys['MethodID'] = int(conn.insert_id())
        else:
            fkeys['MethodID'] = int(cursor.fetchone()['MethodID'])

        units = {}
        variables = {
            'Temp (max)':  'Temperature,deg,Maximum',
            'Temp (min)':  'Temperature,deg,Minimum',
            'Temp (mean)': 'Temperature,deg,Average',
            'Hr (med)':    'Relative humidity,%,Median',
            'Wind (max)':  'Wind speed,km/h,Maximum',
            'Wind (mean)': 'Wind speed,km/h,Average',
            'Wind (gust)': 'Wind gust speed,km/h,Maximum',
            'Vis (km)':    'Visibility,km,Average',
            'Prec (mm)':   'Precipitation,mm,Incremental',
            'Snow (cm)':   'Snow depth,cm,Average'
        }

        cursor.execute("""SELECT UnitsID, UnitsName, UnitsType, UnitsAbbreviation 
                          FROM units""")
        for row in cursor.fetchall():
            units[row['UnitsAbbreviation']] = int(row['UnitsID'])

        for var in variables:
            fk = variables[var].split(',')
            cursor.execute("""SELECT VariableID 
                              FROM variables 
                              WHERE VariableCode=%s""", var)

            if int(cursor.rowcount) == 0:
                cursor.execute("""
                    INSERT INTO variables 
                      (
                        VariableCode, 
                        VariableName, 
                        VariableUnitsID, 
                        TimeUnitsID,
                        SampleMedium,
                        ValueType,
                        IsRegular,
                        TimeSupport,
                        DataType,
                        GeneralCategory,
                        NoDataValue
                      ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                      (
                        var, 
                        fk[0], 
                        units[fk[1]], 
                        104,
                        'Air',
                        'Derived Value',
                        0,
                        1,
                        fk[2],
                        'Climate',
                        -9999
                      ))
                variables[var] = int(conn.insert_id()) 
            else:
                variables[var] = int(cursor.fetchone()['VariableID'])

        fkeys['variables'] = variables;
        fkeys['QualityControlLevelID'] = 0;
        return fkeys

    except mysql.Error as e:
        exit_nicely("MySQL error %d: %s" % (e.args[0], e.args[1]))

    except Exception as e:
        exit_nicely("Unexpected error: %s" % e)


def save_to_csv(filename, _header, _rows):
    """
    Utility function to save the parsed GSOD data to CSV file.

    This function is needed for visualizing the parsed GSOD data, used for debugging purpose.
    Normally you wouldn't need to call this function in production.
    """
    header = []
    for k, v in sorted(_header.iteritems(), key=lambda x: x[1]):
        header.append(k)

    with codecs.open(filename, mode='w', encoding='utf-8') as f:
        f.write('"%s"\n' % '","'.join(header))
        for row in _rows:
            r = [unicode(row.get(key, {}).get('value', u'')) for key in header[1:]]
            r.insert(0, row.get('site', {}).get('name', u''))
            f.write('"%s"\n' % '","'.join(r))


def init():
    """Initialize database connection and other stuffs."""
    try:
        global conn, cursor, logger
        logging.basicConfig(filename='errors.log', format='%(asctime)s %(message)s', 
                            datefmt='[%Y-%m-%d %I:%M:%S %p]', filemode='a', level=logging.ERROR)
        logger = logging.getLogger()
        conn = mysql.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
        cursor = conn.cursor(mysql.cursors.DictCursor)

    except mysql.Error as e:
        exit_nicely("MySQL error %d: %s" % (e.args[0], e.args[1]))


def exit_nicely(error=None):
    """Close any open connection and exit."""
    if conn and conn.open:
        conn.close()

    if error:
        logger.error(error)
        print error

    sys.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--country', required=True)
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    parser.add_argument('--check', action="store_true")
    args = parser.parse_args()

    start_date, end_date = args.start_date, args.end_date
    country, check = args.country, args.check

    init()
    fetch_and_parse_page(country, start_date, end_date, check)
    exit_nicely()
