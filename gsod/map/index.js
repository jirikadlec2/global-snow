var map, sno_wms;
var proj4326 = new OpenLayers.Projection("EPSG:4326");		
		
function get_date() {
    return document.getElementById("datepicker1").value
}

function get_date2() {
	return $("#datepicker1").datepicker( "getDate" );     
}

function update_date() {                  
	sno_wms.mergeNewParams({'time':get_date()});
}

var update_chart = function(lat, lon, date, tolerance) {
   var series_url = 'http://localhost:8080/map/get_time_series.php?lat=' + lat + '&lon=' + lon + '&res=' + tolerance + '&date=' + date;
   console.log(series_url);
   $.getJSON(series_url, function(data) {
        chart.series[0].pointStart = Date.UTC(date.substring(0,4), date.substring(5, 2) - 1, date.substring(8, 2));
        chart.series[0].setData(data.values);
		chart.setTitle({text: data.name});
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
        //    document.getElementById('responseText').innerHTML = evt.text;
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
	
	var ol_wms = new OpenLayers.Layer.WMS( "OpenLayers WMS",
		"http://vmap0.tiles.osgeo.org/wms/vmap0?", {layers: 'basic'} );
		
	highlightLayer = new OpenLayers.Layer.Vector("Highlighted Features", {
            displayInLayerSwitcher: false, 
            isBaseLayer: false 
            }
        );

	sno_wms = new OpenLayers.Layer.WMS("Snow sites","http://snow.hydrodata.org/mapserver.cgi?",
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
                url: "http://snow.hydrodata.org/mapserver.cgi?", 
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
		
	map.addLayers([osm, sno_wms, highlightLayer]);
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