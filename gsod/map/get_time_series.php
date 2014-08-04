<?php
function dateRange( $first, $last, $step = '+1 day', $format = 'Y-m-d' ) {
	$dates = array();
	$current = strtotime( $first );
	$last = strtotime( $last );

	while( $current <= $last ) {

		$dates[] = date( $format, $current );
		$current = strtotime( $step, $current );
	}
	return $dates;
}

$conn = 'mysql:host=localhost;dbname=snow';
$pdo = new PDO($conn, 'root', '');
$lat = $_GET['lat'];
$lon = $_GET['lon'];
$dist_lat = $_GET['res'] / 200000;
$dist_lon = $dist_lat * 0.75;
$lat1 = $lat - $dist_lat;
$lat2 = $lat + $dist_lat;
$lon1 = $lon - $dist_lon;
$lon2 = $lon + $dist_lon;

$db = $pdo-> prepare('SELECT site_id, site_code, site_name, elev, lat, lon FROM sites WHERE lat >= :lat1 AND lat <= :lat2 AND lon >= :lon1 AND lon <= :lon2');
$date = $_GET['date'];
$db->bindParam(':lat1', $lat1, PDO::PARAM_STR); 
$db->bindParam(':lat2', $lat2, PDO::PARAM_STR); 
$db->bindParam(':lon1', $lon1, PDO::PARAM_STR); 
$db->bindParam(':lon2', $lon2, PDO::PARAM_STR); 
//$db->bindParam(':dat', $date, PDO::PARAM_STR);
$db->execute();
$rows = $db->fetchAll(PDO::FETCH_ASSOC);
//$rows_found = $db->rowCount();
//
//if ($rows_found == 0) {
//  echo "no data";
//  exit();
//}
$id = $rows[0]['site_id'];
$name = $rows[0]['site_name'];
$code = $rows[0]['site_code'];
$elev = $rows[0]['elev'];
$site_lat = $rows[0]['lat'];
$site_lon = $rows[0]['lon'];
//$id = $_GET['id'];
$db2 = $pdo-> prepare('SELECT time, val FROM snow WHERE site_id = :site_id AND time >= :date');
$db2->bindParam(':site_id', $id, PDO::PARAM_INT);
$db2->bindParam(':date', $date);
$db2->execute();
$rw = $db2->fetchAll(PDO::FETCH_ASSOC);

$today = (new \DateTime())->format('Y-m-d');
$empty_array = array_fill_keys(dateRange($_GET['date'],$today), 0);

//fill-in empty observations with zeros
foreach ($rw as $row) { 
  $time = date($row['time']);
  if (array_key_exists($time, $empty_array)){ 
    $empty_array[$time] = $row['val'];  
  }
}

//display the JSON
$start = DateTime::createFromFormat("Y-m-d", $_GET['date']);
$year = $start->format("Y");
$month = $start->format('m');
$day = $start->format('d');
echo '{"year":"'.$year.'","month":"'.$month.'","day":"'.$day.'",';
echo '"id":"'.$id.'","code":"'.$code.'","name":"'.$name.'","elev":"'.$elev.'","lat":"'.$site_lat.'","lon":"'.$site_lon.'",';
echo '"values":';
echo '[';
foreach ($empty_array as $row) {
  echo $row.',';
}
echo 'null'.']}';