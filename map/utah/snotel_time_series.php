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

//$url = "http://www.wcc.nrcs.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/1039:UT:SNTL%7Cid=%22%22%7Cname/2014-01-01,2014-08-28/SNWD::value";



$start = $_GET['start'];
$end = $_GET['end'];
$id = $_GET['id'];
$var = $_GET['var'];
$url = "http://www.wcc.nrcs.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/" . $id . ":UT:SNTL%7Cid=%22%22%7Cname/" . $start . "," . $end . "/SNWD::value";

$txt_file = file_get_contents($url);
$rows        = explode("\n", $txt_file);
array_shift($rows);
$nr = 0;

$empty_array = array_fill_keys(dateRange($start,$end), 0);

foreach($rows as $row => $data)
{
  $nr++;
  if ($nr > 7) {
    $row_data = explode(',', $data);
    $time = $row_data[0];
	if (array_key_exists($time, $empty_array)) {
	    $empty_array[$time] = $row_data[1];
	}
  }
}
//display the JSON
$vals = array('values' => array_values($empty_array));
echo json_encode($vals, JSON_NUMERIC_CHECK);