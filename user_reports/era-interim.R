#extracts data from the ERA-interim snow ECMWF grids
library(raster)
library(ncdf)
library(sp)
library(WaterML)

#todo: store this file on HydroShare! and use API to access it
file <- "C:/dev/snow_data/era_interim/era-snow-2015-jfm.nc"
b <- brick(file)

#how to get the time variable label
nc <- open.ncdf(file)
timevar <- get.var.ncdf(nc, varid="time")
netcdf_times <- as.POSIXct(timevar * 3600, origin="1900-01-01")


#example: Compare snow for a selected site
services <- GetServices()
server <- "http://hydrodata.info/CHMI-D/cuahsi_1_1.asmx?WSDL"
serviceID <- services[services$networkName == "HYDRODATACZ-D",]$id
snow_site_info <- HISCentral_GetSeriesCatalog(west=0, south=0, north=90, east=180, serviceID=serviceID)
snow_site_info_selected <- subset(snow_site_info, FullVariableCode=="CHMI-D:SNIH")

snow_sites_sp <- snow_site_info_selected
coordinates(snow_sites_sp) <- ~Longitude+Latitude

#change these two variables: map_date and site_code!
# good examples are Sindelova (CHMI-D:533)
map_date <- "2015-01-29"
site_code <- "CHMI-D:232"

#for map select the layer according to the map date
map_time <- as.POSIXct(map_date)
layer_index <- which(netcdf_times > map_time - 7200 & netcdf_times < map_time + 7200)
netcdf_band <- b[[layer_index]]
plot(netcdf_band)

points(snow_sites_sp)


#example: extract data for one site with site info
my_site <- snow_sites_sp[snow_sites_sp$FullSiteCode==site_code, ]
site_info <- GetSiteInfo(server, siteCode=site_code)
site_name <- as.character(site_info$SiteName[1])
points(my_site, col="red")

#ECMWF dates graphic plot
vals <- extract(b, my_site)
vals_t <- t(vals)
plot(netcdf_times, vals_t * 1000, type="l", ylab="snow depth (cm)", xlab="time", main=site_name)

abline(v = as.POSIXct(map_date), col="green")

#add observed data to our plot
site_vals <- GetValues(server, siteCode=site_code,
                       variableCode=as.character(my_site$FullVariableCode),
                       startDate = min(netcdf_times), endDate = max(netcdf_times))
points(site_vals$time, site_vals$DataValue, col="red")
lines(site_vals$time, site_vals$DataValue, col="red")




#compare with the SNOW INSPECTOR plot
inspector_app <- "http://apps.hydroshare.org/apps/snow-inspector/"
start_date <- strftime(min(netcdf_times), "%Y-%m-%d")
end_date <- strftime(max(netcdf_times), "%Y-%m-%d")
lon <- my_site@coords[1]
lat <- my_site@coords[2]
inspector_url <- paste(inspector_app, "waterml?", "start=", start_date, "&end=", end_date,
                       "&lat=", lat, "&lon=", lon, sep="")
modis_vals <- GetValues(server=inspector_url)
points(modis_vals$time, modis_vals$DataValue / 10, pch=16, col="blue")


