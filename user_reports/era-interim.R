#Load the R Packages
library(raster)
library(ncdf)
library(sp)
library(WaterML)
library(httr)
library(rworldmap)
library(RColorBrewer)
library(gstat)

my_colors <- brewer.pal(7, "Purples")

#store this file on HydroShare! and use API to access it
#this is the HydroShare resource ID
resource_id <- "cea10ad2d9534d0cae21f5950eb7649b"
nc_file <- "era-snow-cz-1979-2015.nc"
resource_url <- paste("http://hydroshare.org/hsapi/resource/", resource_id, "/files/", nc_file, sep="")

#if nc_file doesn't exist: download it from HydroShare
if (!file.exists(nc_file)) {
  print("downloading netcdf file from HydroShare...")
  response <- GET(url=resource_url, write_disk(nc_file, overwrite = TRUE))
}

  
#file <- "C:/dev/snow_data/era_interim/era-snow-2015-jfm.nc"

b <- brick(nc_file)

#how to get the time variable label
nc <- open.ncdf(nc_file)
timevar <- get.var.ncdf(nc, varid="time")
latvar <- get.var.ncdf(nc, varid="latitude")
min_lat <- min(latvar)
max_lat <- max(latvar)
lonvar <- get.var.ncdf(nc, varid="longitude")
min_lon <- min(lonvar)
max_lon <- max(lonvar)
netcdf_times <- as.POSIXct(timevar * 3600, origin="1900-01-01")


#example: Compare snow for a selected site
services <- GetServices()

network_name <- "HYDRODATACZ-D"
serviceID <- services[services$networkName == network_name,]$id
server <- services[services$networkName == network_name,]$url

#use limit coordinates based on the nc file
snow_site_info <- HISCentral_GetSeriesCatalog(west=min_lon, south=min_lat, north=max_lat, east=max_lon, 
                                              serviceID=serviceID, keyword="snow depth")
snow_site_info_selected <- subset(snow_site_info, FullVariableCode=="CHMI-D:SNIH")

snow_sites_sp <- snow_site_info_selected
coordinates(snow_sites_sp) <- ~Longitude+Latitude

#change these two variables: map_date and site_code!
# good examples are Sindelova (CHMI-D:533)
map_date <- "2015-01-28"
site_code <- "CHMI-D:533"
start_date <- "2013-11-01"
end_date <- "2015-03-31"

#for map select the layer according to the map date
map_time <- as.POSIXct(map_date)
layer_index <- which(netcdf_times > map_time - 7200 & netcdf_times < map_time + 7200)
netcdf_band <- b[[layer_index]] * 1000
plot(netcdf_band, col=my_colors, main=paste("ECMWF SWE (mm):", map_date))

points(snow_sites_sp, col="red", pch=16)

#plot country boundaries
countries <- getMap(resolution="low")
plot(countries, add=TRUE)

#fetch data values for specific day
map_time1 <- map_time - 3600 * 24
map_time2 <- map_time + 3600 * 24
variable_code <- as.character(snow_sites_sp$FullVariableCode[1])
snow_sites_sp$site_code <- as.character(snow_sites_sp$FullSiteCode)
for(i in 1: nrow(snow_sites_sp)) {
  snow_sites_sp$snow_val[i] <- NA
  my_v <- GetValues(server, snow_sites_sp$site_code[i], variable_code,
                                           startDate=map_time1, endDate=map_time2)
  if (nrow(my_v) > 0) {
    snow_sites_sp$snow_val[i] <- my_v$DataValue[1]
  }
}
#interpolate snow depth for the specific day
projection(snow_sites_sp) <- projection(netcdf_band)
snow_grid <- as(netcdf_band, "SpatialGridDataFrame")
snow_sites_valid <- snow_sites_sp[!is.na(snow_sites_sp$snow_val),]
snow_idw = idw(snow_val~1, snow_sites_valid, snow_grid)

snow_idw_raster <- raster(snow_idw)
plot(snow_idw_raster, col=my_colors, main=paste("Interpolated Snow Depth on", map_date, "(cm)"))
points(snow_sites_sp, col="red", pch=16)
text(snow_sites_sp, labels="snow_val", pos=4, cex=0.7)
plot(countries, add=TRUE)


#example: extract data for one site with site info
my_site <- snow_sites_sp[snow_sites_sp$FullSiteCode==site_code, ]
site_info <- GetSiteInfo(server, siteCode=site_code)
site_name <- as.character(site_info$SiteName[1])
points(my_site, col="red", pch=16)
text(my_site, labels=site_name, cex=0.7, pos=4)

#ECMWF dates graphic plot
vals <- as.vector(extract(b, my_site))

ecmwf_swe <- data.frame(time=netcdf_times, value=vals)
ecmwf_swe_subset <- subset(ecmwf_swe, time >= as.POSIXct(start_date) & time <= as.POSIXct(end_date))


plot(ecmwf_swe_subset$time, ecmwf_swe_subset$value * 1000, type="l", 
     ylab="SWE (mm)", xlab="time", main=site_name)

abline(v = as.POSIXct(map_date), col="green")

#add observed data to our plot
site_vals <- GetValues(server, siteCode=site_code,
                       variableCode=as.character(my_site$FullVariableCode),
                       startDate = start_date, endDate = end_date)
points(site_vals$time, site_vals$DataValue, col="red")
lines(site_vals$time, site_vals$DataValue, col="red")




#compare with the SNOW INSPECTOR plot
inspector_app <- "http://apps.hydroshare.org/apps/snow-inspector/"
m_start_date <- strftime(as.POSIXct(start_date), "%Y-%m-%d")
m_end_date <- strftime(as.POSIXct(end_date), "%Y-%m-%d")
lon <- my_site@coords[1]
lat <- my_site@coords[2]
inspector_url <- paste(inspector_app, "waterml?", "start=", m_start_date, "&end=", m_end_date,
                       "&lat=", lat, "&lon=", lon, sep="")
modis_vals <- GetValues(server=inspector_url)
points(modis_vals$time, modis_vals$DataValue, pch=16, col="blue")

# 


