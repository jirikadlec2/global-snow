var map, sno_wms, cryoland_wms1, cryoland_wms2, highlightLayer;
var proj4326 = new OpenLayers.Projection("EPSG:4326");	
var mapserver_url = 'http://mapserver.snow.hydrodata.org/mapserver.cgi?';
var cryoland_url = "http://neso.cryoland.enveo.at/cryoland/ows?";
		
function get_date() {
    return document.getElementById("datepicker1").value
}

function get_date2() {
	return $("#datepicker1").datepicker( "getDate" );     
}

function get_date_cryoland() {
    var d_start = get_date();
	var d = get_date2();
	d.setDate(d.getDate() + 1);
	
	var yyyy = d.getFullYear().toString();
	var mm = (d.getMonth()+1).toString();
	var dd =  d.getDate().toString();
	
	var d_end = yyyy + "-" + (mm[1]?mm:"0"+mm[0]) + "-" + (dd[1]?dd:"0"+dd[0]);
	
	return d_start + 'T00:00:00Z' + '/' + d_end + 'T23:59:59Z';
}

function update_date() {  
    var new_date = get_date(); 
    var cryoland_date = get_date_cryoland();	
	sno_wms.mergeNewParams({'time':new_date});
	cryoland_wms1.mergeNewParams({'time':cryoland_date});
	cryoland_wms2.mergeNewParams({'time':cryoland_date});
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
		chart.setTitle({text: data.name + ' (' + data.elev + ' m)'});
		
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
	
	cryoland_wms1 = new OpenLayers.Layer.WMS("Microwave daily SWE", "http://neso.cryoland.enveo.at/cryoland/ows?",
	{layers:"daily_SWE_PanEuropean_Microwave", projection: "EPSG:3857", transparent:true,
        format:'image/png', info_format: "text/plain", time:get_date()},
	{featureInfoFormat: "text/plain", visibility:false});
	
	cryoland_wms2 = new OpenLayers.Layer.WMS("MODIS fraction of snow", "http://neso.cryoland.enveo.at/cryoland/ows?",
	{layers:"daily_FSC_PanEuropean_Optical", projection: "EPSG:3857", transparent:true,
        format:'image/png', info_format: "text/plain", time:get_date()},
	{featureInfoFormat: "text/plain", visibility:false});
	
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
	
    var info1 = new OpenLayers.Control.WMSGetFeatureInfo({
		url: cryoland_url, 
		title: 'Identify features by clicking',
		layers: [cryoland_wms1],
		queryVisible: true,
		eventListeners: {
			getfeatureinfo: function(event) {
				while (map.popups.length > 0) {
				   map.popups[0].destroy();
				}
				var t1 = event.text;
				map.addPopup(new OpenLayers.Popup.FramedCloud(
					"chicken", 
					map.getLonLatFromPixel(event.xy),
					null,
					t1,
					null,
					true
				));
			}
		}
    })

		
	map.addLayers([osm, cryoland_wms1, cryoland_wms2, sno_sites, sno_wms, highlightLayer]);
	map.addControl(new OpenLayers.Control.LayerSwitcher());
	
	//map.addControl(info1);
	//info1.activate();	
	
	map.setCenter(
                new OpenLayers.LonLat(15, 50).transform(
                    new OpenLayers.Projection("EPSG:4326"),
                    map.getProjectionObject()
                ), 4
            );    
})