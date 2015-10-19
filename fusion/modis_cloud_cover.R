#########################################################
# MODIS CLOUD COVER ANALYSIS - CZECHIA                  #
#########################################################

library(sp)
library(rgdal)
library(rworldmap)
library(raster)
library(httr)
library(XML)

#study area
lat.min <- 48.2
lat.max <- 51.5
lon.min <- 11.5
lon.max <- 19.8

#time period
begin_date <- "2012-11-01"
end_date <- "2015-04-30"

all_dates <- seq(as.Date(begin_date), as.Date(end_date), by=1)
months <- as.numeric(strftime(all_dates, "%m"))
winter_months <- months %in% c(1, 2, 3, 4, 11, 12)
winter_dates <- all_dates[winter_months]
winter_dates

#for each timestep get the MODIS raster
getCZE <- function() {
  countries <- getMap(resolution="low")
  cze <- countries[countries$SOVEREIGNT == "Czech Republic",]
  cze_utm <- spTransform(cze, CRS("+proj=utm +zone=33"))
  plot(cze_utm)
  scalebar(100000, label="100 km")
  return(cze_utm)
}

#######################################################
# FUNCTION: GET MODIS                                 #
#######################################################
#start date, end date
getModis <- function(selected.date, lon.min, lat.min, lon.max, lat.max) {
  base_uri <- "http://neso.cryoland.enveo.at/cryoland/ows?Service=WCS"
  #start date, end date
  start_date_t <- strptime(selected.date, "%Y-%m-%d")
  start_date <- strftime(start_date_t, "%Y-%m-%d")
  end_date_t <- as.Date(start_date_t) + 1
  end_date <- strftime(end_date_t, "%Y-%m-%d")
  
  metadata_uri <- paste(base_uri, 
  '&Request=DescribeEOCoverageSet',
  '&EOID=daily_FSC_PanEuropean_Optical',
  '&subset=phenomenonTime("', start_date,'","', end_date, '")', sep="")
  coverage_resp <- GET(metadata_uri)
  doc <- content(coverage_resp)
  ns <- c(xsd="http://www.w3.org/2001/XMLSchema",
          xsi="http://www.w3.org/2001/XMLSchema-instance",
          wcs="http://www.opengis.net/wcs/2.0")
  coverage_ids <- xpathSApply(doc, "//wcs:CoverageId", xmlValue, namespaces=ns)
  coverage_id <- coverage_ids[1]
  
  # Get Coverage
  data_uri <- paste(base_uri, '&version=2.0.1&request=GetCoverage&CoverageID=', coverage_id, '&Format=image/tiff&subset=lat(',
                    lat.min, ',', lat.max, ')&subset=lon(', lon.min, ',', lon.max, ')', 
                    '&subsettingCRS=http://www.opengis.net/def/crs/EPSG/0/4326',
                    '&OutputCRS=http://www.opengis.net/def/crs/EPSG/0/32633', sep="")
  
  ras_file <- paste("modis", start_date, ".tif", sep="")
  GET(data_uri, write_disk(ras_file, overwrite=TRUE))
  
  modis <- raster(ras_file)
  return(modis)
}

calcModisCloudCover <- function(modis, studyArea) {
  #assign 201 to snowy pixels
  modis[modis > 100] <- 201
  
  #assign 200 to bare pixels
  modis[modis == 100] <- 200
  modis[modis == 0] <- 200
  
  #assign 202 to cloudy pixels
  modis[modis < 200] <- 202
  
  #reclass to 0, 1, 2
  modis <- modis - 200
  modisStudy <- mask(modis, studyArea)
  modisStudyCloud <- modisStudy == 2
  modisStudyAll <- !is.na(modisStudy)
  cellStats(modisStudyAll, sum)
  cellStats(modisStudyCloud, sum)
  cloudPercent <- cellStats(modisStudyCloud, sum) / cellStats(modisStudyAll, sum)
  return(cloudPercent * 100)
}

cze <- getCZE()
clouds <- c()
d <- winter_dates[1]
winter_date_names <- as.character(winter_dates)
for(d in winter_date_names) {
  if (!is.na(clouds[winter_dates == d])) {
    next
  }
  r <- getModis(d, lon.min, lat.min, lon.max, lat.max)
  cloud <- calcModisCloudCover(r, cze)
  plot(r)
  plot(cze, add=TRUE)
  title(main=paste("modis - cloud", round(cloud, digits=2), "%", d))
  clouds[winter_dates == d] <- cloud
}
h <- hist(clouds)
h$density = h$counts/sum(h$counts)*100
plot(h, xlab="Cloud cover (%)", ylab="Frequency (%)", 
     main="Cloud cover (November - April)", freq=FALSE)
