#4b will work on a watershed just outside the snotel station, so it fixes its ele, slope and aspect values.
#4c changes station to Lookout Peak
#5 JSON instead of XML. Source 7timer. Uses lookup tables.
#6 Write the files to a Postgress database
#7 reads the MODIS current image

import math
import urllib
import json
import datetime
import Image
import sys
import os
import uuid
import subprocess

scriptpath = "../"

path = "Z:/Desktop/Files/SkyDrive/Pendrive/BYU/Snow/Files/"
#path = "C:/models/GSSHA/instances/LittleDellTest2/"
base = "LittleDellTest2"

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(scriptpath))

# Do the import
from UTMLL import *
from interpolator import *

class Snow:
    path = None
    base = None
    lat = None
    lon = None
    northing = None
    easting = None
    header = None
    codes = None
    surrcodes = None
    elemap = None
    mskmap = None
    slpmap = None
    aspmap = None
    elestat = None
    slpstat = None
    aspstat = None
    snwmap = None
    weights = None
    snowdepth = None
    HMET = None
    GAGES = None
    last_date = None
    last_time = None
    path_psql = "C:/Program Files/PostgreSQL/9.2/bin/"
    db_host = 'ci-water.byu.edu'
    db_port = '5432'
    db_user = 'postgres'
    db_name = 'gssha_files_manager'
    file_path = 'C:/Users/Public/'
    file_base = 'ppp'

    def __init__(self, path, base, coords = [40.835, -111.715], code = "LOPU1", surrcodes = [['MLDU1', [2734.935, 0.110113577727726, -0.0454076609186499]], ['THCU1', [2815.15, 0.327299556981063, -0.824932372320998]], ['PSUU1', [2326.67, 0.3084677328970708, -0.27679024706447986]], ['HARU1', [2211.25, 0.297741498619188, 0.654930538417842]]], weights = [0.01, -1, 0.1]):
        self.path = path
        self.base = base
        self.lat = coords[0]
        self.lon = coords[1]
        self.code = code
        self.surrcodes = surrcodes
        self.weights = weights
        self.elemap = self.loadMap("ele")
        self.mskmap = self.loadMap("msk")
        self.createSA()

    def processSnow(self):
        self.snowdepth = self.retrieveSnow(self.code)
        self.retrieveStation()
        self.calculateWeights()
        self.createSnowmap()
        self.drawMap(self.snwmap, "snow")
        self.getMODIS()
        #self.saveMap(self.snwmap, "swe")
        self.retrieveTemps()
        #self.saveHMET("hmt")
        #self.saveGAGES("gag")       
        self.drawMap(self.slpmap, "slope")
        self.drawMap(self.aspmap, "aspect")
        #self.loadDB()
        
    ##READ SNOW PACK FROM SNOTEL
    def retrieveSnow(self, code): ###UNIT IN INCHES!!!!
        #code = self.code
        f = urllib.urlopen("http://www.wcc.nrcs.usda.gov/ftpref/data/snow/snotel/shef/daily/utsnotel.txt")
        text = "enter"
        while text != '':
            text = f.readline()
            text_ar = text.split(" / ")
            cap = text_ar[0].split(" ")
            if len(cap) > 1 and cap[1] == code:
                snow = float(text_ar[1:][3])
                snow = snow * 0.0254 #Snow into meters
                break
        return snow

    def getMODIS(self):
        td = datetime.date.today()
        year = td.year
        ny = datetime.date(year, 1, 1)
        days = str((td - ny).days + 1)
        yr = str(year)[2:]
        url = "http://ge.ssec.wisc.edu/modis/modis-google-earth/t1." + yr + days + "/t1." + yr + days + ".USA2.143.250m/6.jpg"
        file = self.path + self.base + "MODIS" + ".jpg"
        urllib.urlretrieve(url, file)
        #return url

    def calculateWeights(self):
        stations = []
        surr = self.surrcodes
        for elem in surr:
            code = elem[0]
            sdi = self.retrieveSnow(code)
            hi = elem[1][0]
            si = elem[1][1]
            ai = elem[1][2]
            dsd = sdi - self.snowdepth
            dh = hi - self.elestat
            ds = si - self.slpstat
            da = ai - self.aspstat
            
            stations.append([dsd, dh, ds, da])
        #print str(stations)
        self.weights = solve3stations(stations)

    ##READ TEMPERATURE FORECAST FROM OPENWEATHERMAP
    #http://www.wcc.nrcs.usda.gov/nwcc/yearcount?network=sntl&state=UT&counttype=statelist
    #SNTL	UT	PARLEY'S SUMMIT (684)	1978-October	40.76	-111.63	7500	Summit	Big Dutch Hollow-East Canyon Creek (160201020103)
    ##http://www.7timer.com/bin/meteo.php?lon=-111.7&lat=40.8&ac=0&unit=metric&output=xml&tzshift=0


    def retrieveTemps(self):
        HMET = []
        GAGES = []
        #Tables for transformation
        #http://www.7timer.com/doc.php?lang=en#meteo
        # -9999 is no data
        cloudcover_i = [0, 3, 12.5, 25, 32.5, 50, 62.5, 75, 87.5, 97] # in %
        relativehumidity_i = [22.5, 27.5, 32.5, 37.5, 42.5, 47.5, 52.5, 57.5, 62.5, 67.5, 72.5, 77.5, 82.5, 87.5, 92.5, 97, 100, 2.5, 7.5, 12.5, 17.5] # in %
        windspeed_i = [0.0, 0.0771666, 0.9517214, 2.9323308, 4.8357736, 7.202216, 10.7261574, 14.6873762, 17.8254846, 20.0890382, 22.5326472, 24.9762562, 27.4713096, 28.808864]# in knots
        #GAGES is mm for time period
        precipitation_i = [0, 0.125, 0.625, 2.5, 7.0, 13.0, 23.0, 40.0, 62.5, 76] # in mm/h
        #http://gsshawiki.com/gssha/Long-term_Simulations:Hydrometeorological_data
        f = urllib.urlopen("http://www.7timer.com/bin/meteo.php?lon=-111.7&lat=40.8&ac=0&unit=metric&output=json&tzshift=0")
        text = f.read()
        jobj = json.loads(text)
        init = jobj["init"]
        year = int(init[0:4])
        month = int(init[4:6])
        day = int(init[6:8])
        hour = int(init[8:10])
        date = datetime.datetime(year, month, day, hour)
        dataseries = jobj["dataseries"]
        for data in dataseries:
            timepoint = data["timepoint"]
            raw_pressure = data["msl_pressure"] # in hPa
            raw_relativehumidity = data["rh2m"]
            raw_cloudcover = data["cloudcover"]
            raw_windspeed =data["wind10m"]["speed"]
            raw_temperature = data["temp2m"]
            raw_precipitation = data["prec_amount"]
            delta = datetime.timedelta(timepoint / 24.0)
            time = date + delta
            year = str(time.year)
            month = str(time.month)
            day = str(time.day)
            hour = str(time.hour)
            if raw_pressure == -9999:
                pressure = "99.999"
            else:
                pressure = str(raw_pressure * 0.750061561303) # in mmHg
            if raw_relativehumidity == -9999:
                relativehumidity = "999"
            else:
                relativehumidity = str(int(relativehumidity_i[int(raw_relativehumidity)]))
            if raw_cloudcover == -9999:
                cloudcover = "999"
            else:
                cloudcover = str(int(cloudcover_i[int(raw_cloudcover)]))
            if raw_windspeed == -9999:
                windspeed = "999"
            else:
                windspeed = str(int(windspeed_i[int(raw_windspeed)]))        
            if raw_temperature == -9999:
                temperarure = "999"
            else:
                temperature = str(int(raw_temperature * 1.8 + 32)) # in F
            if raw_precipitation == -9999:
                precipitation = "999"
            else:
                precipitation = str(precipitation_i[int(raw_precipitation)])        
            #For HMET must be one record per hour
            for i in range(0, 3):
                #print year + " " + month + " " + day + " " + hour + " " + pressure + " " + relativehumidity + " " + cloudcover + " " + windspeed + " " + temperature + "9999.99 9999.99" + "|" + precipitation
                HMET.append([year, month, day, hour, pressure, relativehumidity, cloudcover, windspeed, temperature, "9999.99", "9999.99"])
                if precipitation != "0":
                    GAGES.append([year, month, day, hour, precipitation])                  
                hour = str(int(hour) + 1)
        self.GAGES = GAGES
        self.HMET = HMET  
            
    ##LOAD MAPS
    def loadMap(self, ext):
        file = path + base + "." + ext
        f = open(file, "r")
        n = f.readline().split(" ")[1]
        s = f.readline().split(" ")[1]
        e = f.readline().split(" ")[1]
        w = f.readline().split(" ")[1]
        r = f.readline().split(" ")[1]
        c = f.readline().split(" ")[1]
        self.header = [n, s, e, w, r, c]
        north = float(n)
        south = float(s)
        east = float(e)
        west = float(w)
        rows = int(r)
        cols = int(c)
        array = []
        for i in range(0, rows):
            array_row = []
            row = f.readline().split(" ")
            for value in row:
                if value != "\n":
                    array_row.append(float(value))
            array.append(array_row)
        cell_height = (north - south) / float(rows)
        cell_width = (east - west) / float(cols)
        return [north, east, cell_height, cell_width, array]

    def findCoor(self):
        lat = self.lat
        lon = self.lon
        map = self.elemap
        UTM = LLtoUTM(23, lat, lon)
        north_map = map[0]
        east_map = map[1]
        cell_height = map[2]
        cell_width = map[3]
        array = map[4]
        rows = len(array)
        cols = len(array[0])
        easting = UTM[1]
        northing = UTM[2]
        delta_north = north_map - northing
        delta_east = east_map - easting    
        row = int(delta_north / float(cell_height))
        col = cols - int(delta_east / float(cell_width))
        self.northing = northing
        self.easting = easting
        #value = array[row][col]
        return [row, col]#, value]

    def retrieveStation(self):
        coords = self.findCoor()
        mskmap = self.mskmap[4]
        elemap = self.elemap[4]
        slpmap = self.slpmap[4]
        aspmap = self.aspmap[4]
        rowstat = coords[0]
        colstat = coords[1]
        self.elestat = elemap[rowstat][colstat]
        self.slpstat = slpmap[rowstat][colstat]
        self.aspstat = aspmap[rowstat][colstat]

    def createSnowmap(self):
       # coords = self.findCoor()
        weights = self.weights
        heightw = weights[0]
        slopew = weights[1]
        aspectw = weights[2]
        mskmap = self.mskmap[4]
        elemap = self.elemap[4]
        slpmap = self.slpmap[4]
        aspmap = self.aspmap[4]
        north = self.elemap[0]
        east = self.elemap[1]
        cell_height = self.elemap[2]
        cell_width = self.elemap[3] 
        #rowstat = coords[0]
        #colstat = coords[1]
        snowdepth = self.snowdepth
        elestat = self.elestat #elemap[rowstat][colstat]
        slpstat = self.slpstat #slpmap[rowstat][colstat]
        aspstat = self.aspstat #aspmap[rowstat][colstat]
        rows = len(elemap)
        cols = len(elemap[0])
        wghmap = []
        for row in range(0, rows):
            wghmaprow = []
            for col in range(0, cols):
                valid = mskmap[row][col]
                if valid == 1:
                    ele = elemap[row][col]
                    deltah = ele - elestat
                    slp = slpmap[row][col]
                    deltas = slp - slpstat
                    asp = aspmap[row][col]
                    deltaa = asp - aspstat
                    depth = max(0, snowdepth + deltah * heightw + deltas * slopew + deltaa * aspectw)
                    wghmaprow.append(depth)
                else:
                    wghmaprow.append(0)
            wghmap.append(wghmaprow)
        self.snwmap = [north, east, cell_height, cell_width, wghmap]
        return [north, east, cell_height, cell_width, wghmap]

    def calculateSA(self, row, col):
        mask = self.mskmap[4]
        ele = self.elemap[4]
        cell_height = self.elemap[2]
        cell_width = self.elemap[3]
        rows = len(ele)
        cols = len(ele[0])
        if mask[row][col] == 0:
            return None
        else:
            center = ele[row][col]
            #Top
            if col == 0 or mask[row][col - 1] == 0:
                top = None
            else:
                top = ele[row][col - 1]
            #Bottom
            if col == (cols - 1) or mask[row][col + 1] == 0:
                bottom = None
            else:
                bottom = ele[row][col + 1]
            #Left
            if row == 0 or mask[row - 1][col] == 0:
                left = None
            else:
                left = ele[row - 1][col ]
            #Right
            if row == (rows - 1) or mask[row + 1][col] == 0:
                right = None
            else:
                right = ele[row + 1][col]
            #SlopeX
            if right != None and left != None:
                slopex = (left - right) / float(2 * cell_width)
            elif right == None and left != None:
                slopex = (left - center) / float(cell_width)
            elif left == None and right != None:
                slopex = (center - right) / float(cell_width)
            else:
                slopex = 0.0
            #SlopeY
            if bottom != None and top != None:
                slopey = (top - bottom) / float(2 * cell_height)
            elif bottom == None and top != None:
                slopey = (top - center) / float(cell_height)
            elif top == None and bottom != None:
                slopey = (center - bottom) / float(cell_height)
            else:
                slopey = 0.0
            aspect = math.atan2(-slopey, slopex) 
            slope = (slopex ** 2 + slopey ** 2) ** 0.5
            aspectnorth =  -math.sin(aspect) #find out why - ...
        return [slope, aspectnorth]
        
    def createSA(self):
        elemap = self.elemap[4]
        north = self.elemap[0]
        east = self.elemap[1]
        cell_height = self.elemap[2]
        cell_width = self.elemap[3] 
        rows = len(elemap)
        cols = len(elemap[0])
        slpmap = []
        aspmap = []
        for row in range(0, rows):
            slpmaprow = []
            aspmaprow = []
            for col in range(0, cols):
                sa = self.calculateSA(row, col)
                if sa == None:
                    slope = 0.0
                    aspect = 0.0
                else:
                    slope = sa[0]
                    aspect = sa[1]

                slpmaprow.append(slope)
                aspmaprow.append(aspect)
            slpmap.append(slpmaprow)
            aspmap.append(aspmaprow)
        self.slpmap = [north, east, cell_height, cell_width, slpmap]
        self.aspmap = [north, east, cell_height, cell_width, aspmap]

    def drawMap(self, map, type):
        mask = self.mskmap
        file = path + base + type + ".png"
        north_map = map[0]
        east_map = map[1]
        cell_height = map[2]
        cell_width = map[3]
        array = map[4]
        mskmap = mask[4]
        rows = len(array)
        cols = len(array[0])
        min = None
        max = None
        for row in range(0, rows):
            for col in range(0, cols):
                valid = mskmap[row][col]
                if valid == 1:
                    value = array[row][col]
                    if min == None:
                        min = value
                    if max == None:
                        max = value
                    if value < min:
                        min = value
                    if value > max:
                        max = value
        im = Image.new("L" , (cols , rows), 128)
        for rw in range(0, rows):
            for cl in range(0, cols):
                rawval = array[rw][cl]
                adjval = (rawval - min) / (max-min) * 255
                val = int(adjval)
                im.putpixel((cl, rw), val)
        im.putpixel((col, row), 0)    
        im.save(file)

    def saveMap(self, map, ext, prec = 2):
        file = path + base + "." + ext
        north_map = map[0]
        east_map = map[1]
        cell_height = map[2]
        cell_width = map[3]
        array = map[4]
        rows = len(array)
        cols = len(array[0])
        f = open(file, "w")
        f.write("north: " + self.header[0])
        f.write("south: " + self.header[1])
        f.write("east: " + self.header[2])            
        f.write("west: " + self.header[3])
        f.write("rows: " + self.header[4])
        f.write("cols: " + self.header[5])
        for row in array:
            line = ""       
            for value in row:
                precision = "%0." + str(prec) + "f"
                formatval = precision % value
                line = line + formatval + " "
            line = line + "\n"
            f.write(line)
        #f.write('This is a test\n')
        f.close()
        
    def createMap(self, map, prec = 2):
        north_map = map[0]
        east_map = map[1]
        cell_height = map[2]
        cell_width = map[3]
        array = map[4]
        rows = len(array)
        cols = len(array[0])
        string = ""
        string = string + "north: " + self.header[0] + "\n"
        string = string + "south: " + self.header[1] + "\n"
        string = string + "east: " + self.header[2] + "\n"            
        string = string + "west: " + self.header[3] + "\n"
        string = string + "rows: " + self.header[4] + "\n"
        string = string + "cols: " + self.header[5] + "\n"
        for row in array:
            line = ""       
            for value in row:
                precision = "%0." + str(prec) + "f"
                formatval = precision % value
                line = line + formatval + " "
            line = line + "\n"
            string = string + line 
        return string

    def saveHMET(self, ext):
        file = path + base + "." + ext
        f = open(file, "w")        
        HMET = self.HMET
        for data in HMET:
            hour = data[3]
            line = data[0] + " " + data[1] + " " + data[2] + " " + data[3] + " " + data[4] + " " + data[5] + " " + data[6] + " " + data[7] + " " + data[8]  + " " + data[9] + " " + data[10] + "\n"
            f.write(line)
        f.close()

    def createHMET(self):
        string = ""
        HMET = self.HMET
        for data in HMET:
            string = string + data[0] + " " + data[1] + " " + data[2] + " " + data[3] + " " + data[4] + " " + data[5] + " " + data[6] + " " + data[7] + " " + data[8]  + " " + data[9] + " " + data[10] + "\n"
        return string

    def saveGAGES(self, ext):
        file = path + base + "." + ext
        f = open(file, "w")          
        GAGES = self.GAGES
        events = len(GAGES)
        for data in GAGES:
            f.write("EVENT\n")
            f.write("NRGAG 1\n")
            f.write("NRPDS 2\n")            
            f.write("COORD " + str(self.northing) + " " + str(self.easting) + "\n")
            hour = data[3]
            line = "GAGES " + data[0] + " " + data[1] + " " + data[2] + " " + data[3] + " 00 " +  "0.0" + "\n"            
            f.write(line)
            line = "GAGES " + data[0] + " " + data[1] + " " + data[2] + " " + str(int(data[3]) + 1) + " 00 " +  data[4] + "\n"            
            f.write(line)
            f.write("\n")
        f.close()

    def createGAGES(self):
        string = ""         
        GAGES = self.GAGES
        events = len(GAGES)
        for data in GAGES:
            string = string + "EVENT\n"
            string = string + "NRGAG 1\n"
            string = string + "NRPDS 2\n"       
            string = string + "COORD " + str(self.northing) + " " + str(self.easting) + "\n"
            hour = data[3]
            string = string + "GAGES " + data[0] + " " + data[1] + " " + data[2] + " " + data[3] + " 00 " +  "0.0" + "\n"            
            string = string + "GAGES " + data[0] + " " + data[1] + " " + data[2] + " " + str(int(data[3]) + 1) + " 00 " +  data[4] + "\n"            
            string = string + "\n"
        return string

    def loadDB(self):
        unique = str(uuid.uuid1())
        date_raw = datetime.datetime.today()
        date = str(date_raw)[0:10]
        time = str(date_raw)[11:26]
        path_psql = self.path_psql
        db_host = self.db_host
        db_port = self.db_port
        db_user = self.db_user
        db_name = self.db_name        
        file = self.createMap(self.snwmap)
        ext = "swe"
        self.loadFile2DB(unique, date, time, ext, file, path_psql, db_host, db_port, db_user, db_name)
        file = self.createHMET()
        ext = "hmet"
        self.loadFile2DB(unique, date, time, ext, file, path_psql, db_host, db_port, db_user, db_name)
        file = self.createGAGES()
        ext = "gag"
        self.loadFile2DB(unique, date, time, ext, file, path_psql, db_host, db_port, db_user, db_name)
        self.last_date = date
        self.last_time = time

    def readDB(self, date = None, time = None):
        if date == None or time == None:
            #date_raw = datetime.datetime.today()
            #date = str(date_raw)[0:10]
            date = self.last_date
            time = self.last_time
        path_psql = self.path_psql
        db_host = self.db_host
        db_port = self.db_port
        db_user = self.db_user
        db_name = self.db_name
        file_path = self.file_path
        file_base = self.file_base
        file = self.createMap(self.snwmap)
        ext = "swe"
        self.readFilefromDB(date, time,  ext, file_path, file_base, path_psql, db_host, db_port, db_user, db_name)
        ext = "hmet"
        self.readFilefromDB(date, time, ext, file_path, file_base, path_psql, db_host, db_port, db_user, db_name)
        ext = "gag"
        self.readFilefromDB(date, time, ext, file_path, file_base, path_psql, db_host, db_port, db_user, db_name)

    def loadFile2DB(self, unique, date, time, ext, file, path_psql, db_host, db_port, db_user, db_name):
        paramfile = path + ext + ".tmp"
        f = open(paramfile, "w")
        line = 'INSERT INTO ' + 'gssha_files' + ' (uuid, date, time, ext, file) VALUES (\'' + unique + '\', \'' + date + '\', \'' + time + '\', \'' + ext + '\', \'' + file + '\');'
        f.write(line)
        f.close()
        params = [path_psql + 'psql.exe', '-h', db_host, '-p', db_port, '-U', db_user, '-d', db_name, '-f', paramfile]
        pp = subprocess.Popen(params)#, stdout = subprocess.PIPE, shell = False)
        pp.wait()

    def readFilefromDB(self, date, time, ext, file_path, file_base, path_psql, db_host, db_port, db_user, db_name):
        params = [path_psql + "psql.exe", '-h', db_host, '-p', db_port, '-U', db_user, '-d', db_name, '-c', 'select file from ' + 'gssha_files' + ' where date = \'' + date + '\'' + ' and time = \'' + time + '\'' + ' and ext = \'' + ext + '\';', '-t', '-o', file_path + ext + '.tmp']
        #print str(params)
        pp = subprocess.Popen(params)#, stdout = subprocess.PIPE)
        pp.wait()
        prefile = open(file_path + ext + '.tmp', "r")
        newfile = open(file_path + file_base + "." + ext, "w")
        for line in prefile:
            newline = line.replace('+\n','\n').replace('\\r','')[1:]            
            newfile.write(newline)
        prefile.close()
        newfile.close()

'''#How to use
ppp = Snow(path, base)
ppp.processSnow()
ppp.loadDB()
ppp.readDB() #Without date and time parameters it would use the last date and time used to load the DB
'''