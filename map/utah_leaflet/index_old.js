var sitesLayer, snotelLayer;
//var layerModisTerraTrueColor, layerModisTerraSnow;
var selectControl;

var GIBS_WMTS_GEO_ENDPOINT = "http://map1.vis.earthdata.nasa.gov/wmts-geo/wmts.cgi";
var TILEMATRIXSET_GEO_250m = "EPSG4326_250m";
var TILEMATRIXSET_GEO_2km  = "EPSG4326_2km";
var TILEMATRIXSET_GEO_500m = "EPSG4326_500m";

$(function() {
	
	// TODO: When the day is changed, cache previous layers. This allows already
    // loaded tiles to be used when revisiting a day. Since this is a
    // simple example, layers never "expire" from the cache.
    var cache = {};
	
	// GIBS needs the day as a string parameter in the form of YYYY-MM-DD.
    // Date.toISOString returns YYYY-MM-DDTHH:MM:SSZ. Split at the "T" and
    // take the date which is the first part.
    var dayParameter = function(day) {
        return day.toISOString().split("T")[0];
    };
	
	var map = L.map('map').setView([40.205, -111.70], 11);
	
	//to store the background layer
	var backgroundLayer;

	var get_date = function() {
        return document.getElementById("datepicker1").value;
    };

	//var get_date2() = function() {
	//    //return $("#datepicker1").datepicker( "getDate" ); 
    //    return document.getElementById("datepicker1").datepicker("getDate");	
	//};
	
	var update = function(selected_date) {
        // TODO: Using the day as the cache key, see if the layer is already in the cache.
        //var key = day;
        //var layer = cache[key];

        // If not, create a new layer and add it to the cache.
        //if ( !layer ) {
        //    layer = createOverlay(selected_date);
        //    cache[key] = layer;
        //}
		layer = createOverlay(selected_date);

		//remove all layers except background
        clearLayers();

        // Add the new layer for the selected time
        map.addLayer(layer);
    };

    var clearLayers = function() {
        map.eachLayer(function(layer) {	
            console.log(layer.options.myName);	
            if (layer.options.myName === "overlay") {			
                map.removeLayer(layer);
			}
        });
    };


	function get_units() {
		if( $("#cmb_units").val() === "cm") {
			return { "snow_unit_name": "cm",
					"elev_unit_name": "m"
					};
		} else {
			return {"snow_unit_name": "in",
					"elev_unit_name": "ft"
					};
		}				
	}

	function get_hydrologic_year(date) {
	   var year = parseInt(date.substring(0,4));
	   var mon = parseInt(date.substring(5,7));
	   if (mon > 10){
		 year = year + 1;
	   }
	   return year;
	}

	function get_date_for_chart(date) {
		var year = date.substring(0,4);
		var mon = parseInt(date.substring(5,7));
		var day = date.substring(8,10);
		return Date.UTC(year, mon-1, day);
	}


    $("#datepicker1").datepicker({ dateFormat: 'yy-mm-dd', 
	    onSelect: function(dateStr, dateVal) {
			console.log(dateStr);
			console.log(dateVal);
		    update(dateStr);
	}});


	$("#btn_next").click(function(){       
		var d = $("#datepicker1").datepicker("getDate");
		d.setDate(d.getDate() + 1);
		$("#datepicker1").datepicker("setDate", d);
		update(dayParameter(d));
    }); 
	
	$("#btn_prev").click(function(){       
		var d = $("#datepicker1").datepicker("getDate");
		d.setDate(d.getDate() - 1);
		$("#datepicker1").datepicker("setDate", d);
		update(dayParameter(d));
    });
	
	$("#cmb_units").change(function() {
	    update_units();
	});

	
    function showInfo(evt) {
	    //alert('show info!');
        if (evt.features && evt.features.length) {
             highlightLayer.destroyFeatures();
             highlightLayer.addFeatures(evt.features);
             highlightLayer.redraw();
		} else {
		    alert(evt.text);
        }
    }

	
    var template =
	"https://map1{s}.vis.earthdata.nasa.gov/wmts-webmerc/" +
	"{layer}/default/{time}/{tileMatrixSet}/{z}/{y}/{x}.png";
	

	var createBackground = function() {
		L.tileLayer('https://{s}.tiles.mapbox.com/v3/{id}/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
				'<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
				'Imagery © <a href="http://mapbox.com">Mapbox</a>',
			id: 'examples.map-i875mjb7',
			myName: 'background'
		}).addTo(map);
	}

    var createOverlay = function(day) {
		var new_layer = L.tileLayer(template, {
			layer: "MODIS_Terra_Snow_Cover",
			tileMatrixSet: "GoogleMapsCompatible_Level8",
			maxNativeZoom: 8,
			maxZoom: 18,
			time: day,
			tileSize: 256,
			subdomains: "abc",
			noWrap: true,
			continuousWorld: true,
			// Prevent Leaflet from retrieving non-existent tiles on the
			// borders.
			bounds: [
				[-85.0511287776, -179.999999975],
				[85.0511287776, 179.999999975]
			],
			attribution:
				"<a href='https://earthdata.nasa.gov/gibs'>" +
				"NASA EOSDIS GIBS</a>&nbsp;&nbsp;&nbsp;" +
				"<a href='https://github.com/nasa-gibs/web-examples/blob/release/leaflet/js/webmercator-epsg3857.js'>" +
				"View Source" +
				"</a>",
            myName: "overlay"				
		});
		return new_layer; 
	}
	
	backgroundLayer = createBackground();
	//set date to today
	$("#datepicker1").datepicker('setDate', new Date());
	update(get_date());
});