<?php header('Content-type: application/json');
/*
 * Title:   SNOTEL sites to GeoJSON
 * Notes:   Query a MySQL table or view of points with x and y columns and return the results in GeoJSON format, suitable for use in OpenLayers, Leaflet, etc.
 * Author:  Bryan R. McBride, GISP
 * Contact: bryanmcbride.com
 * GitHub:  https://github.com/bmcbride/PHP-Database-GeoJSON
 */

# get url
$url = "http://www.wcc.nrcs.usda.gov/ftpref/data/water/wcs/map/stations.js";
$txt_file = file_get_contents($url);
$rows = explode("\n", $txt_file);
array_shift($rows);
$nr = 0;


# Build GeoJSON feature collection array
$geojson = array(
   'type'      => 'FeatureCollection',
   'features'  => array()
);

# Loop through rows to build feature arrays
foreach($rows as $row => $data) {
    $r = explode(',', $data);
    //print_r($r);
    if (count($r) > 10) {
		$properties['name'] = trim(substr($r[0], 1),'"');
		$properties['id'] = trim($r[3], '"');
		$properties['state'] = trim($r[4], '"');
		$properties['network'] = trim($r[5], '"');
		$properties['elev'] = trim($r[6], '"');
		$feature = array(
			'type' => 'Feature',
			'geometry' => array(
				'type' => 'Point',
				'coordinates' => array(
					$r[2],
					$r[1]
				)
			),
			'properties' => $properties
		);
		# Add feature arrays to feature collection array
		if ($properties['state'] == 'UT' && $properties['network'] == 'SNTL') {
		    array_push($geojson['features'], $feature);
		}
	}
}

echo json_encode($geojson, JSON_NUMERIC_CHECK);