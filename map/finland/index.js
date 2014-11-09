var map;
var selected_date = '2014-01-01';
var modisOverlay;
var selected_station_id = 0;
var selected_station_name;



$(document).ready(function () {
    
	function get_date() {
       return document.getElementById("datepicker1").value;
    }

	function get_date2() {
		return $("#datepicker1").datepicker( "getDate" );     
	}

	function update_date() {  
		selected_date = get_date(); 
		map.overlayMapTypes.removeAt(0); 
		map.overlayMapTypes.setAt(0,modisOverlay); 
		if (selected_station_id > 0) {
			console.log('update_date: ' + selected_date);
			update_chart(selected_station_id, selected_date, selected_station_name);
		}
	}
	
	
	$("#datepicker1").datepicker({ dateFormat: 'yy-mm-dd', 
	onSelect: function(dateText) {
       update_date()
	}});
	$("#datepicker1").datepicker('setDate', new Date());
	
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
      center: new google.maps.LatLng(65, 25),
      zoom: 6,
      mapTypeId: google.maps.MapTypeId.ROADMAP,
    };
	
    map = new google.maps.Map(document.getElementById("map_canvas"),
        myOptions);
		
	var layer = new google.maps.FusionTablesLayer({
          query: {
            select: 'Name',
            from: '1f8Ft8gK6qlvdGKwZkDTjxSEoWLasnuANR3wZrOzQ'
          },
          map: map
        });
		
	google.maps.event.addListener(layer,'click',function(e) {
        selected_station_id = e.row['ID'].value;   
        selected_station_name = e.row['Name'].value;
		selected_date = get_date();	
		document.getElementById("chart_title").innerHTML = selected_station_name
        update_chart(selected_station_id, selected_date, selected_station_name)		
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
        maxZoom: 18,
        minZoom: 1,
        name: "MODIS_Terra_TrueColor",
        tileSize: new google.maps.Size(256, 256),
        opacity: 0.8
    };
    modisOverlay = new google.maps.ImageMapType(layerOptions);
    map.overlayMapTypes.insertAt(0, modisOverlay);
});