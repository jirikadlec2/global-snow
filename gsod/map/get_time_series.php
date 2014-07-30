<?php
require_once 'db_config.php';

$siteid=$_GET['siteid'];

$query = "SELECT time, val FROM datavalues";
$query .= " WHERE SiteID=.$siteid. ORDER BY time ASC";

$result = mysql_query($query) or die("SQL Error 1: " . mysql_error());

$num_rows = mysql_num_rows($result);
$count=1;
 while ($row = mysql_fetch_array($result, MYSQL_ASSOC))
  {
	  if (!($row['DataValue'] == $NoValue))
{
    echocsv( $row );
   if($count!=$num_rows)
	{echo "\r\n";}
  $count=$count+1;
  }
  }
?>