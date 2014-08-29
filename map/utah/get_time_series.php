<?php header('content-type: application/json; charset=utf-8');
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

//$conn = 'mysql:host=localhost;dbname=snow';
$conn = 'mysql:host=localhost;dbname=ogimet-snow';
$pdo = new PDO($conn, 'root', '');
$start = $_GET['start'];
$end = $_GET['end'];

$id = $_GET['id'];
$db2 = $pdo-> prepare('SELECT LocalDateTime AS time, DataValue AS val FROM datavalues WHERE SiteID = :site_id AND LocalDateTime >= :start AND LocalDateTime < :end');
$db2->bindParam(':site_id', $id, PDO::PARAM_INT);
$db2->bindParam(':start', $start);
$db2->bindParam(':end', $end);
$db2->execute();
$rw = $db2->fetchAll(PDO::FETCH_ASSOC);

$empty_array = array_fill_keys(dateRange($start,$end), 0);

//fill-in empty observations with zeros
foreach ($rw as $row) { 
  $time = substr($row['time'], 0, 10);
  if (array_key_exists($time, $empty_array)){ 
    $val = $row['val'];
	if ($val < 0)
	  $val = NULL;
    $empty_array[$time] = $val; 
  }
}

//display the JSON
$vals = array('values' => array_values($empty_array));
echo json_encode($vals, JSON_NUMERIC_CHECK);
$pdo = NULL;