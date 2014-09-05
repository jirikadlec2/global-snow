function get_date() {
    return document.getElementById("datepicker1").value
}

function get_date2() {
	return $("#datepicker1").datepicker( "getDate" );     
}

function update_date() {  
    selected_date = get_date(); 
	map.overlayMapTypes.removeAt(0); 
    map.overlayMapTypes.setAt(0,modisOverlay); 
}

function get_hydrologic_year(date) {
   var year = parseInt(date.substring(0,4));
   var mon = parseInt(date.substring(5,7));
   if (mon > 10){
     year = year + 1;
   }
   return year;
}
function get_chart_url(st_id, date) {
    var year = get_hydrologic_year(date);
	var begin = (year - 1) + "1101";
	var end = year + "1031";
	return "http://hydrodata.info/grafy/en-snw-" + st_id + "-" + begin + "-" + end + ".png";
}

var map;
var modisOverlay;
var selected_date = '2014-01-01';

$(document).ready(function () {
    
	$("#datepicker1").datepicker({ dateFormat: 'yy-mm-dd', 
	onSelect: function(dateText) {
       update_date()
	}});
	
	$("#btn_next").click(function(){       
		var d = get_date2();
		d.setDate(d.getDate() + 1);
		$("#datepicker1").datepicker("setDate", d);
		update_date();
    }); 
	
	$("#btn_prev").click(function(){       
		var d = get_date2();
		d.setDate(d.getDate() - 1);
		$("#datepicker1").datepicker("setDate", d);
		update_date();
    });
	
	$("#checkbox_snow").click( function(){
      
	  if( $(this).is(':checked') ){
	    map.overlayMapTypes.setAt(0,modisOverlay); 
	  } else {
	    map.overlayMapTypes.removeAt(0);
	  }
    });

	var myOptions = {
      center: new google.maps.LatLng(50, 15),
      zoom: 8,
      mapTypeId: google.maps.MapTypeId.ROADMAP,
    };
	
    map = new google.maps.Map(document.getElementById("map_canvas"),
        myOptions);
		
	var layer = new google.maps.FusionTablesLayer({
          query: {
            select: 'Name',
            from: '1qPo5qb6qDcz6WaIJGnO5jDfxpojqS_QKlDBLQbMU'
          },
          map: map
        });
		
	google.maps.event.addListener(layer,'click',function(e) {
        var st_id = e.row['id'].value;
	    console.log('site id:' + st_id);
		var img_url = get_chart_url(st_id, get_date());		
		$("#graph_img").attr("src", img_url);
    });	
	
	var getTileUrl = function(tile, zoom) {
        return "http://map1.vis.earthdata.nasa.gov/wmts-webmerc/" +
               "MODIS_Terra_CorrectedReflectance_TrueColor/default/" + 
			   get_date() + "/" +
               "GoogleMapsCompatible_Level9/" +
                zoom + "/" + tile.y + "/" +
                tile.x + ".jpeg";
    };

    var layerOptions = {
        alt: "MODIS_Terra_TrueColor",
        getTileUrl: getTileUrl,
        maxZoom: 11,
        minZoom: 1,
        name: "MODIS_Terra_TrueColor",
        tileSize: new google.maps.Size(256, 256),
        opacity: 0.8
    };
    modisOverlay = new google.maps.ImageMapType(layerOptions);
    map.overlayMapTypes.insertAt(0, modisOverlay);
});