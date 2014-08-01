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
$db = $pdo-> prepare('SELECT site_id FROM sites WHERE lat >= :lat1 AND lat <= :lat2 AND lon >= :lon1 AND lon <= :lon2');
$db->bindParam(':lat1', $_GET['lat1'], PDO::PARAM_STR); 
$db->bindParam(':lat2', $_GET['lat2'], PDO::PARAM_STR); 
$db->bindParam(':lon1', $_GET['lon1'], PDO::PARAM_STR); 
$db->bindParam(':lon2', $_GET['lon2'], PDO::PARAM_STR); 
$db->execute();
$rows = $db->fetchAll(PDO::FETCH_ASSOC);
$rows_found = $db->rowCount();
#echo 'rows:';
#echo $rows_found;
#echo ' id: ';
#echo htmlentities($rows[0]['site_id']);
$id = $rows[0]['site_id'];
$id = $_GET['id'];
$db2 = $pdo-> prepare('SELECT time, val FROM snow WHERE site_id = :site_id AND time >= :date');
$db2->bindParam(':site_id', $id, PDO::PARAM_INT);
$db2->bindParam(':date', $_GET['date']);
$db2->execute();
$rw = $db2->fetchAll(PDO::FETCH_ASSOC);

$today = (new \DateTime())->format('Y-m-d');
$empty_array = array_fill_keys(dateRange($_GET['date'],$today), 0);

foreach ($rw as $row) { 
  $time = date($row['time']);
  if (array_key_exists($time, $empty_array)){ 
    $empty_array[$time] = $row['val'];  
  }
}

$start = DateTime::createFromFormat("Y-m-d", $_GET['date']);
$year = $start->format("Y");
$month = $start->format('m');
$day = $start->format('d');
echo '{"year":"'.$year.'","month":"'.$month,'","day":"'.$day.'",';
echo '"values":';
echo '[';
foreach ($empty_array as $row) {
  echo $row.',';
}
echo 'null'.']}';