#########################################################
# SNOW DATA FUSION using INVERSE DISTANCE               #
#########################################################

#########################################################
# the script will try to install the required packages: #
# httr                                                  #
# raster                                                #
# rgdal                                                 #
# rworldmap                                             #
# sp                                                    #
# XML                                                   #
#########################################################
list.of.packages <- c("httr", "rgdal", "raster", "rworldmap", "sp", "XML")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages) > 0) {install.packages(new.packages)}

library(httr)
library(XML)
library(raster)
library(rgdal)
library(rworldmap)

# (optional: you can set the working directory to save outputs)
# setwd("C:/jiri/Dropbox/PHD/crowdsourcing/data/modis")

# parameters: selected.date
selected.date <- "2015-02-17"

# parameters: bounding box (valid in Europe only!)
lat.min <- 48.2
lat.max <- 51.5
lon.min <- 11.5
lon.max <- 19.8

# parameters: inverse distance exponent (default value = 3)
dist.exp <- 3



#setting margins for plotting
par(mar=c(1.1,1.1,1.1,1.1))

#######################################################
# STEP 1 Get Coverage Description !                   #
#######################################################
#start date, end date
start_date_t <- strptime(selected.date, "%Y-%m-%d")
start_date <- strftime(start_date_t, "%Y-%m-%d")
end_date_t <- as.Date(start_date_t) + 1
end_date <- strftime(end_date_t, "%Y-%m-%d")

base_uri <- "http://neso.cryoland.enveo.at/cryoland/ows?Service=WCS"

metadata_uri <- paste(base_uri, '&Request=DescribeEOCoverageSet&EOID=daily_FSC_PanEuropean_Optical&subset=phenomenonTime("', start_date,'","', end_date, '")', sep="")
coverage_resp <- GET(metadata_uri)
doc <- content(coverage_resp)
ns <- c(xsd="http://www.w3.org/2001/XMLSchema",
        xsi="http://www.w3.org/2001/XMLSchema-instance",
        wcs="http://www.opengis.net/wcs/2.0")
coverage_id <- xpathSApply(doc, "//wcs:CoverageId", xmlValue, namespaces=ns)

#######################################################
# STEP 2 Get Coverage !                               #
#######################################################
data_uri <- paste(base_uri, '&version=2.0.1&request=GetCoverage&CoverageID=', coverage_id, '&Format=image/tiff&subset=lat(',
lat.min, ',', lat.max, ')&subset=lon(', lon.min, ',', lon.max, ')', 
'&subsettingCRS=http://www.opengis.net/def/crs/EPSG/0/4326',
'&OutputCRS=http://www.opengis.net/def/crs/EPSG/0/32633', sep="")

ras_file <- paste("modis", start_date, ".tif", sep="")
GET(data_uri, write_disk(ras_file, overwrite=TRUE))

modis <- raster(ras_file)
plot(modis, axes=FALSE, box=FALSE)

#######################################################
# STEP 3 Plot CZECHIA border! (for orientation )      #
#######################################################
plotCountries <- function() {
  countries <- getMap(resolution="low")
  cze <- countries[countries$SOVEREIGNT == "Czech Republic" | 
                     countries$SOVEREIGNT == "Germany" |
                     countries$SOVEREIGNT == "Slovakia",]
  cze_utm <- spTransform(cze, CRS("+proj=utm +zone=33"))
  plot(cze_utm, add=TRUE)
  scalebar(100000, label="100 km")
}
plotCountries()

#######################################################
# STEP 4 RECLASSIFY MODIS to PRESENT / ABSENT         #
#######################################################
modis.present <- modis > 100
modis.present[modis.present == 0] <- NA

modis.absent <- modis == 0 | modis == 100
modis.absent[modis.absent == 0] <- NA

brk <- c(0, 1)
plot(modis.present, legend=FALSE, axes=FALSE, box=FALSE, breaks=brk, col=c("lightblue"))
plot(modis.absent, legend=FALSE, axes=FALSE, box=FALSE, breaks=brk, col=c("green"), add=TRUE)
legend("topright", legend = c("snow", "bare ground", "cloud"), fill=c("lightblue", "green", "white"))
plotCountries()

#######################################################
# STEP 5 ADD CHMI official stations                   #
#######################################################
getStations <- function(selected_date) {
  st_uri <- "http://hydrodata.info/api/sites?var=snih"
  vals_uri <- "http://hydrodata.info/api/values"
  stations <- read.table(st_uri, sep="\t", header=TRUE, stringsAsFactors = FALSE)
  #distinguish SYNOP stations
  synop.ids <- c(2,3,9,10,20,22,23,24,30,33,34,41,42,45,47,48,49,51,
                 52,53,60,63,76,80,81,82,223,231,232,233,253)
  stations$synop <- stations$id %in% synop.ids
  
  #download data values from each station
  d <- data.frame()
  i <- 1
  for (i in 1:nrow(stations)) {
    id <- stations$id[i]
    uri <- paste(vals_uri, "?var=snih&st=", id, sep="")
    vals <- read.table(uri, sep="\t", header=TRUE, stringsAsFactors = FALSE)
    selected.vals <- vals[vals$datum == selected_date, ]
    if (nrow(selected.vals) == 0) {
      next
    }
    #check for NA values
    val <- vals[vals$datum == selected_date, 2]
    
    if (is.na(val)) {
      if (stations$synop[i] == TRUE) {
        val <- 0
      } else {
        val <- NA
      }
    }
    #assign value
    if (!is.na(val)) {
      d <- rbind(d, c(lat=stations$lat[i], lon=stations$lon[i], snodep=val))
    }
  }
  #assign presence / absence
  names(d) <- c("lat", "lon", "snodep")
  d$present <- d$snodep > 0
  
  coordinates(d) <- ~lon+lat
  projection(d) <- CRS("+proj=longlat")
  return(d)
}

stations <- getStations(start_date)
stations_utm <- spTransform(stations, CRS("+proj=utm +zone=33"))
stations.prez <- stations_utm[stations_utm$present == TRUE,]
stations.abs <- stations_utm[stations_utm$present == FALSE,]
plot(stations.prez, pch=16, col="blue", add=TRUE)
plot(stations.abs, pch=21, col="blue", bg="yellow", add=TRUE)

#######################################################
# STEP 6 ADD VOLUNTEER POINT OBSERVATIONS             #
#######################################################
getVolunteer <- function(selected_date) {
  resource_id <- "d2d47cfe84be4bc9ba3352eec7ceb57e"
  zip_file <- "volunteer.zip"
  resource_uri <- paste("http://hydroshare.org/hsapi/resource/", resource_id, sep="")
  GET(resource_uri, write_disk(zip_file, overwrite=TRUE))
  res <- unzip(zip_file)
  res.csv <- grepl("*.csv", res)
  csvfile <- res[res.csv]
  
  # get data from hydroshare unzipped file
  volunteer.data <- read.csv(csvfile, header=TRUE, stringsAsFactors = FALSE)
  names(volunteer.data) <- c("date", "time", "latitude", "longitude", "site", "snow_depth_cm")
  
  # extract values for spedific date
  snow.selected <- volunteer.data[volunteer.data$date == selected_date, ]
  
  #presence field
  presence <- snow.selected$snow_depth_cm >= 1
  absence <- snow.selected$snow_depth_cm <= 0
  unknown <- snow.selected$snow_depth_cm > 0 & snow.selected$snow_depth_cm < 1
  snow.selected$present[presence] <- 1
  snow.selected$present[absence] <- 0
  snow.selected$present[unknown] <- 2
  coordinates(snow.selected) <- ~longitude+latitude
  projection(snow.selected) <- CRS("+proj=longlat")
  return(snow.selected)
}

reports <- getVolunteer(start_date)
reports_utm <- spTransform(reports, CRS("+proj=utm +zone=33"))
reports.prez <- reports_utm[reports_utm$present == 1,]
reports.abs <- reports_utm[reports_utm$present == 0,]
plot(reports.prez, pch=17, col="blue", add=TRUE)
plot(reports.abs, pch=24, col="blue", bg="yellow", add=TRUE)

#######################################################
# STEP 8 ADD SKI TRACKS (from STRAVA)                 #
#######################################################
resource_id <- "7d8751fef6234ae794b4b1ca31156b8f"
resource_uri <- paste("http://hydroshare.org/hsapi/resource/", resource_id, sep="")
track_file <- "strava.zip"
GET(resource_uri, write_disk(track_file, overwrite=TRUE))
res <- unzip(track_file)
res.shp <- grepl("*.shp", res)
shpfile <- res[res.shp]
shpfolder <- substr(shpfile, 1, nchar(shpfile) - nchar(basename(shpfile)) - 1)
shpname <- substr(basename(shpfile), 1, nchar(basename(shpfile)) - 4)
tracks <- readOGR(shpfolder, shpname)
sel.tracks <- tracks[tracks$begdate == start_date,]
projection(sel.tracks) <- CRS("+proj=longlat")
sel.tracks.utm <- spTransform(sel.tracks, CRS("+proj=utm +zone=33"))

####################################################
# GARMIN CONNECT SKI TRACKS...
####################################################
resource_id <- "ab4fce9c3ee84675b4179c995a60a811"
resource_uri <- paste("http://hydroshare.org/hsapi/resource/", resource_id, sep="")
track_file <- "garmin.zip"
GET(resource_uri, write_disk(track_file, overwrite=TRUE))
res <- unzip(track_file)
res.shp <- grepl("*.shp", res)
shpfile <- res[res.shp]
shpfolder <- substr(shpfile, 1, nchar(shpfile) - nchar(basename(shpfile)) - 1)
shpname <- substr(basename(shpfile), 1, nchar(basename(shpfile)) - 4)
tracks <- readOGR(shpfolder, shpname)
seltracks <- length(which(tracks$begdate == start_date))
if (seltracks > 0) {
  garmin.tracks <- tracks[tracks$begdate == start_date, ]
  if (nrow(garmin.tracks) > 0) {
    projection(garmin.tracks) <- CRS("+proj=longlat")
    garmin.tracks.utm <- spTransform(garmin.tracks, CRS("+proj=utm +zone=33"))
  }
}

legend("bottomright", legend = c("stations", "volunteer", "tracks"), 
       pch=c(16, 17, NA), lty=c(NA, NA, 1),
       col=c("darkblue","darkblue", "red"))

#union with strava
if (seltracks > 0) {
  all.tracks <- rbind(sel.tracks.utm, garmin.tracks.utm)
} else {
  all.tracks <- sel.tracks.utm
}
lines(all.tracks, col="red")
title(main=paste("snow", selected.date))

##############################################################
# STEP 9 RASTER DISTANCE to MODIS, stations, reports, tracks #
##############################################################
d.modis.abs <- distance(modis.absent)
d.modis.prez <- distance(modis.present)
d.station.abs <- distanceFromPoints(modis, stations.abs)
d.station.prez <- distanceFromPoints(modis, stations.prez)
d.report.abs <- distanceFromPoints(modis, reports.abs)
d.report.prez <- distanceFromPoints(modis, reports.prez)
track.ras <- rasterize(all.tracks, modis)
d.track.prez <- distance(track.ras)

inv.d.modis.abs <- 1/(d.modis.abs^dist.exp)
inv.d.modis.prez <- 1/(d.modis.prez^dist.exp)
inv.d.station.abs <- 1 /(d.station.abs^dist.exp)
inv.d.station.prez <- 1 / (d.station.prez^dist.exp)
inv.d.report.abs <- 1 / (d.report.abs^dist.exp)
inv.d.report.prez <- 1 / (d.report.prez^dist.exp)
inv.d.track.prez <- 1 / (d.track.prez^dist.exp)

prez.conf <- inv.d.modis.prez + inv.d.station.prez + inv.d.report.prez + inv.d.track.prez
prez.abs.conf <- inv.d.modis.abs + inv.d.station.abs + inv.d.report.abs + inv.d.modis.prez + inv.d.station.prez + inv.d.report.prez + inv.d.track.prez
conf <- prez.conf / prez.abs.conf
plot(conf)

################################################################
# STEP 10 COMBINE WITH MODIS PREZ, ABS                         #
################################################################
summary(conf)
cnan <- is.na(conf)
conf[is.na(conf)] <- 1
plot(conf)
plotCountries()
snow.likely <- conf > 0.7
snow.likely[snow.likely < 1] <- NA
snow.unlikely <- conf < 0.7
snow.unlikely[snow.unlikely < 1] <- NA

brk1 <- c(0, 1)
plot(snow.likely, legend=FALSE, axes=FALSE, box=FALSE, breaks=brk, col=c("lightblue"))
plot(snow.unlikely, legend=FALSE, axes=FALSE, box=FALSE, breaks=brk, col=c("green"), add=TRUE)
legend("topright", legend = c("p > 0.7", "p < 0.7"), fill=c("lightblue", "green"))
plotCountries()
title(main=paste("snow probability", selected.date))
