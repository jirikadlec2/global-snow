##############################################
# STRAVA GPX Exporter Library                #
##############################################

library(httr)
library(sp)
library(rgdal)
library(XML)

parseTcx <- function(my_file) {
  doc <- xmlParse(my_file)
  nodes <- getNodeSet(doc, "//ns:Trackpoint", "ns")
  mydf  <- plyr::ldply(nodes, as.data.frame(xmlToList))
  names(mydf) <- c("time", "lat", "lon", "elev", "dist")
  mydf$lat <- as.numeric(as.character(mydf$lat))
  mydf$lon <- as.numeric(as.character(mydf$lon))
  coordinates(mydf) <- ~lon+lat
  plot(mydf, pch=16, col="red")
  return(mydf)
}

############################################################
activity_id <- 256120402
url <- paste("http://raceshape.com/strava.export.php?ride=",
             activity_id, "&type=tcx", sep="")
my_file <- paste(activity_id, ".tcx", sep="")
download.file(url, destfile=my_file)
Sys.sleep(30)
download.file(url, destfile=my_file)
track <- parseTcx(my_file)

############################################################

