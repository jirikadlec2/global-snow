library(sp)
library(rgdal)
library(raster)
library(gstat)

datum <- "2014-01-27"

a <- read.csv("snowdata.csv", header=FALSE)
a1 <- a[a$V1==datum,]

coordinates(a1) <- ~V4+V3
proj4string(a1) <- CRS("+proj=longlat")
snih <- spTransform(a1, CRS("+proj=utm +zone=33"))
plot(snih)

r <- raster(extent(snih))
res(r) <- 1000.0
proj4string(r) <- CRS("+proj=utm +zone=33")

mg <- gstat(id = "i2", formula = V6~1, data=snih, 
            nmax=7, set=list(idp = .5))
z <- interpolate(r, mg)
plot(z)
plot(snih, add=TRUE)

reclas <- c(0, 2, 1, 2, 6, 3, 6, 15, 8)
rclmat <- matrix(reclas, ncol=3, byrow=TRUE)
rc <- reclassify(z, rclmat)
plot(rc)
poly <- rasterToPolygons(rc)
plot(poly)

