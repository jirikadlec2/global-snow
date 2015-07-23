#READ the IMS data from a sample file
library(R.utils)
library(sp)
library(raster)
library(rgdal)
library(lubridate)

ims_file <- "ims2015001_4km_v1.3.asc"
ims_lines <- readLines(ims_file)
#exclude lines 1 to 30
data_lines <- ims_lines[-(1:30)]

lst <- list()

for (i in 1: length(data_lines)) {
  lst[[i]] <- as.numeric(unlist(strsplit(data_lines[i], split="")))
}
lst <- rev(lst)
data <- do.call(rbind, lst)
r <- raster(data)
projection(r) <- "+proj=stere +lat_0=90 +lat_ts=60 +lon_0=-80 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6356257 +units=m +no_defs"
plot(r)

#READ the latitudes and longitudes of the grid-points
imslat <- readBin("imslat_4km.bin", "numeric", 
                  n = 6144*6144, endian = "little", size = 4)
imslon <- readBin("imslon_4km.bin", "numeric", 
                  n = 6144*6144, endian = "little", size = 4)

z <- rep(0, 6144*6144)
nrows <- length(data_lines)
for (i in 1: nrows) {
  index_start <- (i - 1) * 6144 + 1
  index_end <- i * 6144
  
  #lats <- imslat[index_start : index_end]
  #lons <- imslat[index_start : index_end]
  vals <- as.numeric(unlist(strsplit(data_lines[i], split="")))
  z[index_start : index_end] <- vals
}
xyz <- cbind(imslon, imslat, z)
snowras <- rasterFromXYZ(xyz, res = c(4000, 4000))

#read the snow raster from the *.tiff file
snowrastif2 <- raster("ims2015001_4km_GIS_v1.3.tif.gz")
snowrastif <- raster("ims2015001_4km_GIS_v1.3.tif")
plot(snowrastif)

####################################################################
# Initialize Study Area
####################################################################
#re-project the snow raster
projection(snowrastif)
#output raster for: CZECHIA
ymn <- 48.5
ymx <- 51.2
xmn <- 12.0
xmx <- 19.0
cellsize <- 0.05
e <- extent(xmn, xmx, ymn, ymx)
ras <- raster(e)
res(ras)=cellsize
projection(ras) <- CRS("+proj=longlat")

snowras2 <- projectRaster(snowrastif, ras, method="ngb")
plot(snowras2)

#add country boundary
czechia <- readOGR("czechia", "czechia")
plot(czechia, add=TRUE)
czechras <- rasterize(czechia, ras)
plot(czechras)
czech_area <- cellStats(czechras, sum)

snowrascz <- mask(snowras2, mask = czechras)
plot(snowrascz)
aa <- snowrascz == 4
snow_area <- cellStats(aa, sum)
area_percent <- snow_area / czech_area

#read the observation point reports
reports <- read.csv("../user_reports/snowdata.csv", header = TRUE)
max(reports$LONGITUDE)
coordinates(reports) <- ~LONGITUDE+LATITUDE
plot(reports, add=TRUE)

########################################################
# FUNCTION to get snow area                            #
########################################################
get_snow_raster <- function(date, study_area_raster) {
  dat <- as.Date(date)
  year <- year(dat)
  jd <- yday(dat)
  version <- "1.2"
  ext <- "zip"
  if (year > 2014 | (year == 2014 & jd > 335)) {
    version <- "1.3"
    ext <- "tif.gz"
  }
  base_uri <- "ftp://sidads.colorado.edu/DATASETS/NOAA/G02156/GIS/4km"
  url <- sprintf("%s/%d/ims%d%03d_4km_GIS_v%s.%s",
                 base_uri, year, year, jd, version, ext)
  gzfile <- sprintf("ims%d%03d_4km_GIS_v%s.%s", year, jd, version, ext)
  rasterfile <- sprintf("ims%d%03d_4km_GIS_v%s.tif", year, jd, version)
  
  if (!file.exists(rasterfile)) {
    #if the file doesn't exist, download and unzip a new *.tif file
    err <- try(download.file(url, gzfile))
    if (class(err) == "try-error") return (NULL)
    
    #unzip the gz file
    if (ext == "tif.gz") {
      gunzip(gzfile, overwrite=TRUE)
    } else {
      unzip(gzfile, overwrite=TRUE)
      print(rasterfile)
    }
  } 
  #read raster from geotiff file
  ims_r <- raster(rasterfile)
  
  #project and clip raster to study area
  snowras <- projectRaster(ims_r, study_area_raster, method="ngb")
  snowras <- (snowras == 4)
  return (snowras)
}

get_snow_area <- function(study_area_raster, snow_raster) {
  #calculation of the area
  study_area_cells <- cellStats(study_area_raster, sum)
  snowmasked <- mask(snow_raster, study_area_raster)
  snow_area <- cellStats(snowmasked > 0, sum)
  area_percent <- snow_area / study_area_cells
  return (area_percent * 100)
}

plot_snow <- function(snow_raster, date, area_percent, country) {
  plot(snow_raster, col=c("lightgreen", "white"), legend=FALSE, 
       main=paste(date, "snow cover: ", sprintf("%.2f", area_percent), "%")
       )
  plot(country, add=TRUE)
}

###############################################
# TEST: GET snow-covered area of CZECHIA      #
###############################################
czechia <- readOGR("czechia", "czechia")
ymn <- 48.5
ymx <- 51.2
xmn <- 12.0
xmx <- 19.0
cellsize <- 0.05
e <- extent(xmn, xmx, ymn, ymx)
framework <- raster(e)
res(framework)=cellsize
projection(framework) <- CRS("+proj=longlat")
czechras <- rasterize(czechia, framework)
czech_area <- cellStats(czechras, sum)

start <- "2013-01-01"
end <- "2015-03-31"
dates <- seq(as.Date(start), as.Date(end), by = 1)

reports <- read.csv("../user_reports/snowdata.csv", header = TRUE,
                    stringsAsFactors = FALSE)
names(reports) <- c("date", "time", "latitude", "longitude", "site", "snow")
reports$date <- as.Date(reports$date)

N <- length(dates)
ims_snow_area <- rep(0, N)
for (i in 1: N) {
  #fetch snow raster
  snow_raster <- get_snow_raster(dates[i], czechras)
  if (is.null(snow_raster)) next #skip if download failed
  
  #calc area covered by snow
  ims_snow_area[i] <- get_snow_area(czechras, snow_raster)
  
  #plot snow raster
  plot_snow(snow_raster, dates[i], ims_snow_area[i], czechia)
  
  #also plot the active sites and export the raster
  active_reports <- reports[reports$date == dates[i],]
  if (nrow(active_reports) == 0) {
    next
  }
  coordinates(active_reports) <- ~longitude+latitude
  nonzero_reports <- active_reports[active_reports$snow > 0.5,]
  points(nonzero_reports)
  if (nrow(nonzero_reports) == 0) {
    next
  }
  text(nonzero_reports, labels = nonzero_reports$snow, pos=4)
}

#################################################################
# TEST: compare with number of ground volunteer reports from CZ #
#################################################################

reports2 <- reports[reports$date >= start,]
reports3 <- reports2[reports2$snow > 0,]
reports4 <- data.frame(date=reports3$date, snow=reports3$snow)
reports_count <- aggregate(snow ~ date, data = reports4, FUN=length)
plot(snow~date, data=reports_count, col="red", type="l")

#both plots
par(mfrow = c(2, 1))
plot(dates, ims_snow_area, type="l")
plot(snow~date, data=reports_count, col="red", type="l")
par(mfrow=c(1,1))

 
