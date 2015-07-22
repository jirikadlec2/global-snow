import datetime
import urllib2
import os
import codecs
import re
from bs4 import BeautifulSoup


def parse_city(city_url):
    city = urllib2.urlopen(city_url)
    soup2 = BeautifulSoup(city.read())
    f2 = soup2.find_all("img")
    for el in f2:
        src = el['src']
        if 'mapka' in src:
            items = src.split('-')
            return {'lat': items[-1], 'lon': items[-2]}
    return {'lat': None, 'lon': None}


def parse_observation(obs_url):
    data = urllib2.urlopen(obs_url)
    soup = BeautifulSoup(data.read())
    obs_list = []

    f = soup.find_all(id='snihuvas')
    for line in f:
        sno = line.b.text
        if sno.endswith(" cm"):
            sno = sno[:-3]
        else:
            sno = '0.5'
        name = line.strong.text
        t = line.find(text=re.compile('\d{2}:\d{2}'))
        hm = re.findall('\d+', t)
        hour = hm[0]
        minute = hm[1]
        time = '{0}:{1}'.format(hour, minute)
        city_url = line['href']
        coord = parse_city(city_url)
        obs_list.append({'loc': coord, 'name': name, 'time': time, 'snow': sno})
    return obs_list


import pandas as pd


def get_observations(begin=datetime.date(2013, 1, 1), end=datetime.date(2015, 4, 1)):
    datelist = pd.date_range(begin, end).tolist()
    complete_list = []
    for date in datelist:
        dat2 = date.strftime("%m-%d-%Y")
        print dat2
        obs_url = 'http://www.in-pocasi.cz/pocasi-u-vas/seznam.php?historie={0}'.format(dat2)
        try:
            observations = parse_observation(obs_url)
            for o in observations:
                o['date'] = date
                complete_list.append(o)
        except urllib2.HTTPError:
            print "Error downloading data..."
            next

    return complete_list




if __name__ == "__main__":

    my_list = get_observations()

    base_path = os.path.dirname(os.path.basename(__file__))
    file_path = os.path.join(base_path, 'snowdata.csv')
    with codecs.open(file_path, "w", "utf-8-sig") as my_file:
        my_file.write('"DATE","TIME","LONGITUDE","LATITUDE","SNOW_DEPTH_CM"')
        for item in my_list:
            my_file.write(unicode(item['date'].strftime("%Y-%m-%d")))
            my_file.write(',')
            my_file.write(unicode(item['time']))
            my_file.write(',')
            my_file.write(unicode(item['loc']['lon']))
            my_file.write(',')
            my_file.write(unicode(item['loc']['lat']))
            my_file.write(',')
            my_file.write(u'"' + item['name'] + u'"')
            my_file.write(',')
            my_file.write(item['snow'])
            my_file.write('\n')