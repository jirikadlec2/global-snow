#extracts data from the ERA-interim snow ECMWF grids
library(raster)
library(ncdf)
library(sp)
library(WaterML)
library(httr)
library(rworldmap)

#store this file on HydroShare! and use API to access it
#this is the HydroShare resource ID
resource_id <- "cea10ad2d9534d0cae21f5950eb7649b"
nc_file <- "era-snow-cz-1979-2015.nc"
resource_url <- paste("http://hydroshare.org/hsapi/resource/", resource_id, "/files/", file_name, sep="")

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
plot(netcdf_band, main=paste("ECMWF SWE (mm):", map_date))

points(snow_sites_sp)

#plot country boundaries
countries <- getMap(resolution="low")
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
     ylab="SWE (mm)", xlab="time", main=site_name, ylim=c(0, 110))

abline(v = as.POSIXct(map_date), col="green")

#add observed data to our plot
site_vals <- GetValues(server, siteCode=site_code,
                       variableCode=as.character(my_site$FullVariableCode),
                       startDate = start_date, endDate = end_date)
points(site_vals$time, site_vals$DataValue * 5, col="red")
lines(site_vals$time, site_vals$DataValue * 5, col="red")




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


