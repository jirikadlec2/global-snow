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
getActivity <- function(activity_id) {
  #activity_id <- 269583360
  url <- paste("http://raceshape.com/strava.export.php?ride=",
               activity_id, "&type=tcx", sep="")
  my_file <- paste(activity_id, ".tcx", sep="")
  download.file(url, destfile=my_file)
  Sys.sleep(30)
  download.file(url, destfile=my_file)
  track <- parseTcx(my_file)
}
############################################################

############################################################
# HTML parsing for STRAVA activities
############################################################
#activities_file <- download.file(destfile="activities.html", url="https://www.strava.com/activities/search?activity_type=NordicSki&city=Prague&country=Czech+Republic&distance_end=200&distance_start=0&elev_gain_end=15000&elev_gain_start=0&keywords=&lat_lng=50.0755381%2C14.43780049999998&location=Praha&page=1&state=Hlavn%C3%AD+m%C4%9Bsto+Praha&time_end=10.0&time_start=0.0&type=&utf8=%E2%9C%93")
html.raw <- htmlTreeParse("lists/cheb_WinterSport_1.html", useInternalNodes=TRUE)
html.parse <- xpathApply(html.raw, "//a", xmlAttrs)
activ.parse <- grep('*/activities/[0-9]+', unlist(html.parse), value=TRUE)

i <- 1
for (i in 1: length(activ.parse)) {
  activ.parse[i]
  activity_id <- as.numeric(substr(activ.parse[i], 13, 23))
  getActivity(activity_id)
}
