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
get_snow_area <- function(date, study_area_raster, country) {
  dat <- as.Date(date)
  year <- year(dat)
  jd <- yday(dat)
  base_uri <- "ftp://sidads.colorado.edu/DATASETS/NOAA/G02156/GIS/4km"
  url <- sprintf("%s/%d/ims%d%03d_4km_GIS_v1.3.tif.gz",
                 base_uri, year, year, jd)
  gzfile <- sprintf("ims%d%03d_4km_GIS_v1.3.tif.gz", year, jd)
  download.file(url, gzfile)
  #unzip the gz file
  rasterfile <- gunzip(gzfile, overwrite=TRUE)
  
  ims_r <- raster(rasterfile)
  
  #clip raster by study area
  snowras <- projectRaster(ims_r, study_area_raster, method="ngb")
  snowras <- mask(snowras, study_area_raster)
  plot(snowras)
  plot(country, add=TRUE)
  
  #calculation of the area
  study_area_cells <- cellStats(study_area_raster, sum)
  
  snow_area <- cellStats(snowras == 4, sum)
  area_percent <- snow_area / czech_area
  
  return (area_percent)
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

start <- "2014-12-02"
end <- "2015-03-31"
dates <- seq(as.Date(start), as.Date(end), by = 1)

N <- length(dates)
ims_snow_area <- rep(0, N)
for (i in 1: N) {
  ims_snow_area[i] <- get_snow_area(dates[i], czechras, czechia)
}

#################################################################
# TEST: compare with number of ground volunteer reports from CZ #
#################################################################
reports <- read.csv("../user_reports/snowdata.csv", header = TRUE,
                    stringsAsFactors = FALSE)
names(reports) <- c("date", "time", "latitude", "longitude", "site", "snow")
reports$date <- as.Date(reports$date)
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

#scatterplot
snow_ims <- data.frame(date = dates, ims_snow = ims_snow_area)
reg <- merge(snow_ims, reports_count, by.x="date", by.y="date")
plot(snow~ims_snow, data=reg, ylab="#snow reports", xlab="IMS snow covered area")
m <- lm(snow~ims_snow, data=reg)
summary(m)
abline(m, col="red")
