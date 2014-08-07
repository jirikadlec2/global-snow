var map, sno_wms, highlightLayer;
var proj4326 = new OpenLayers.Projection("EPSG:4326");	
var mapserver_url = 'http://mapserver.snow.hydrodata.org/mapserver.cgi?';	
		
function get_date() {
    return document.getElementById("datepicker1").value
}

function get_date2() {
	return $("#datepicker1").datepicker( "getDate" );     
}

function update_date() {  
    var new_date = get_date();                
	sno_wms.mergeNewParams({'time':new_date});
	if (highlightLayer.features.length > 0) {
	    var pt = new OpenLayers.LonLat(highlightLayer.features[0].geometry.x, highlightLayer.features[0].geometry.y);
		var lonlat = pt.transform(map.getProjectionObject(), proj4326);
	    update_chart(lonlat.lat, lonlat.lon, new_date, 100.0);
	}
}

var show_selected_station = function(lat, lon) {  
  var lonlat = new OpenLayers.LonLat(lon, lat);
  var lonlatTransf = lonlat.transform(proj4326, map.getProjectionObject());
  console.log(lonlatTransf.lat + ' ' + lonlatTransf.lon);
  var feature = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(lonlatTransf.lon, lonlatTransf.lat));
  highlightLayer.removeAllFeatures();
  highlightLayer.addFeatures(feature);
}

var update_chart = function(lat, lon, date, tolerance) {
   var series_url = 'get_time_series.php?lat=' + lat + '&lon=' + lon + '&res=' + tolerance + '&date=' + date;
   console.log(series_url);
   $.getJSON(series_url, function(data) {
        var beginDate = Date.UTC(date.substring(0,4), date.substring(5, 7) - 1, date.substring(8, 10));
		console.log(date + ' ' + beginDate);
        seriesData = [];
        for (var i = 0; i < data.values.length; i++){
            seriesData.push([beginDate + (3600 * 1000 * 24 * i), data.values[i]]);
        }  
		chart.series[0].setData(seriesData);
		chart.setTitle({text: data.name});
		
		show_selected_station(data.lat, data.lon);
   });
}

$( document ).ready(function() {
	$("#datepicker1").datepicker({ dateFormat: 'yy-mm-dd', 
	onSelect: function(dateText) {
       update_date()
	}});
	
	$("#btn_next").click(function(){       
		var d = get_date2();
		d.setDate(d.getDate() + 1);
		$("#datepicker1").datepicker("setDate", d);
		update_date();
		update_chart();
    }); 
	
	$("#btn_prev").click(function(){       
		var d = get_date2();
		d.setDate(d.getDate() - 1);
		$("#datepicker1").datepicker("setDate", d);
		update_date();
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
	
	map = new OpenLayers.Map({
	    div: 'map', 
		projection: "EPSG:3857",
		layers: [
            new OpenLayers.Layer.Google(
                "Google Physical",
                {type: google.maps.MapTypeId.TERRAIN}
            ),
            new OpenLayers.Layer.Google(
                "Google Streets", // the default
                {numZoomLevels: 20}
            ),
            new OpenLayers.Layer.Google(
                "Google Hybrid",
                {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 20}
            ),
            new OpenLayers.Layer.Google(
                "Google Satellite",
                {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22}
            )
        ],
	});
	
	var osm = new OpenLayers.Layer.OSM( "Simple OSM Map");
		
	highlightLayer = new OpenLayers.Layer.Vector("Highlighted Features", {
            displayInLayerSwitcher: false, 
            isBaseLayer: false 
            }
        );
		
	var sno_sites = new OpenLayers.Layer.WMS("Snow all sites",
	    mapserver_url,
	    {layers:"snow_stations", projection: "EPSG:3857", transparent:true, 
	    format:'image/png', info_format: "text/plain"});

	sno_wms = new OpenLayers.Layer.WMS("Snow sites",mapserver_url,
	{layers:"snow_daily", projection: "EPSG:3857", transparent:true, 
	    format:'image/png', info_format: "text/plain", time:get_date()},
	{featureInfoFormat: "text/plain"});
	
	//map clicking event
	map.events.register("click", map, function(e) {
        var position = this.events.getMousePosition(e);
        var lonlat = map.getLonLatFromPixel(position);
        var lonlatTransf = lonlat.transform(map.getProjectionObject(), proj4326);
		var metersPerPixel = map.getResolution();	//res is in meters per pixel
        var clickTolerance = 15.0;
        var date = get_date();		
		update_chart(lonlatTransf.lat, lonlatTransf.lon, date, metersPerPixel * clickTolerance);       
    });
	
	var infoControls = {
            info1: new OpenLayers.Control.WMSGetFeatureInfo({
                url: mapserver_url, 
                title: 'Identify features by clicking',
                layers: [sno_wms],
                queryVisible: true,
				eventListeners: {
                getfeatureinfo: function(event) {
				    while (map.popups.length > 0) {
                       map.popups[0].destroy();
                    }
					var t1 = event.text.substring(event.text.indexOf("="));
                    map.addPopup(new OpenLayers.Popup.FramedCloud(
                        "chicken", 
                        map.getLonLatFromPixel(event.xy),
                        null,
                        t1.substring(0, t1.indexOf(" ", 2)),
                        null,
                        true
                    ));
                }
            }
            })
        };
		
	map.addLayers([osm, sno_sites, sno_wms, highlightLayer]);
	map.addControl(new OpenLayers.Control.LayerSwitcher());
	
	for (var i in infoControls) { 
            //infoControls[i].events.register("getfeatureinfo", this, showInfo);
            map.addControl(infoControls[i]); 
        }
	//infoControls.info1.activate();	
	
	map.setCenter(
                new OpenLayers.LonLat(15, 50).transform(
                    new OpenLayers.Projection("EPSG:4326"),
                    map.getProjectionObject()
                ), 4
            );    
})