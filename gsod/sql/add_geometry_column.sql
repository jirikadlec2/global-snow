SELECT AddGeometryColumn('sites','geom', 4326, 'POINT', 2);
UPDATE sites SET geom = ST_SetSRID(ST_MakePoint(lon, lat),4326);
CREATE INDEX sites_geom_index ON sites USING GIST ( [geom] );