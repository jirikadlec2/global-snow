import re
import datetime
import urllib2

line = "Cats are smarter than dogs"

year = 2014
mon = 1
day = 28
dat = datetime.date(year, mon, day)
dat2 = dat.strftime("%m-%d-%Y")
url = 'http://www.in-pocasi.cz/pocasi-u-vas/seznam.php?historie={0}'.format(dat2)

data = urllib2.urlopen(url)
line = data.read()

searchObj = re.findall(r'<strong>[^<]+</strong>', line, re.M|re.I)

if searchObj:
    for (val) in searchObj:
        print val
else:
    print "Nothing found!!"

