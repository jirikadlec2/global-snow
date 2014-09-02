var map, highlightLayer;
var sitesLayer, snotelLayer;
var layerModisTerraTrueColor, layerModisTerraSnow;
var wfs;
var proj4326 = new OpenLayers.Projection("EPSG:4326");	
var mapserver_url = 'http://mapserver.snow.hydrodata.org/mapserver.cgi?';
var cryoland_url = "http://neso.cryoland.enveo.at/cryoland/ows?";
var selectControl;

var GIBS_WMTS_GEO_ENDPOINT = "http://map1.vis.earthdata.nasa.gov/wmts-geo/wmts.cgi";
var TILEMATRIXSET_GEO_250m = "EPSG4326_250m";
var TILEMATRIXSET_GEO_2km  = "EPSG4326_2km";
var TILEMATRIXSET_GEO_500m = "EPSG4326_500m";

var my_style = new OpenLayers.Style({
   'pointRadius': 6,
   'externalGraphic': 'favicon.ico',
   'label' : '${DataValue}',
   'labelAlign' : 'lb'
});
var style_snotel = new OpenLayers.Style({
   'pointRadius': 6,
   'externalGraphic': 'snotel.gif',
});
var style_ghcn = new OpenLayers.Style({
   'pointRadius': 6,
   'externalGraphic': 'favicon.ico',
})
var highlight_style = new OpenLayers.Style({
    'strokeColor': '#000000'
})	
		
function get_date() {
    return document.getElementById("datepicker1").value
}

function get_date2() {
	return $("#datepicker1").datepicker( "getDate" );     
}

function get_hydrologic_year(date) {
   var year = date.substring(0,4);
   var mon = date.substring(6,7);
   if (mon < 10){
     year = year - 1;
   }
   return year;
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

	if (sitesLayer.selectedFeatures.length > 0) {
	    update_chart(sitesLayer.selectedFeatures[0].attributes, new_date);
	}
	
    layerModisTerraTrueColor.mergeNewParams({'time':new_date});
	layerModisTerraSnow.mergeNewParams({'time':new_date});
}


function update_chart(site_attributes, selected_date) {
   
   var hydro_year = get_hydrologic_year(selected_date);  
   var start_date = (hydro_year - 1) + "-10-01";
   var end_date = hydro_year + "-09-30";
   var site_id = site_attributes["SiteID"];
   var series_url = 'get_time_series.php?id=' + site_id + '&start=' + start_date + '&end=' + end_date;
   console.log(series_url);
   $.getJSON(series_url, function(data) {
        
        var beginDate = Date.UTC(hydro_year, 9, 1);
		console.log('update_chart: date' + ' ' + beginDate);
        seriesData = [];
        for (var i = 0; i < data.values.length; i++){
            seriesData.push([beginDate + (3600 * 1000 * 24 * i), data.values[i] * 0.1]);
        }  
		chart.series[0].setData(seriesData);
		chart.setTitle({text: site_attributes["SiteName"] + "(" + site_attributes["Elevation_m"] + " m)"});
   });
}

function update_chart_snotel(site_attributes, selected_date) {
   
   var hydro_year = get_hydrologic_year(selected_date);  
   var start_date = (hydro_year - 1) + "-10-01";
   var end_date = hydro_year + "-09-30";
   var site_id = site_attributes["id"];
   var series_url = 'snotel_time_series.php?id=' + site_id + '&start=' + start_date + '&end=' + end_date + '&var=SNWD';
   console.log(series_url);
   $.getJSON(series_url, function(data) {
        
        var beginDate = Date.UTC(hydro_year, 9, 1);
		console.log('update_chart: date' + ' ' + beginDate);
        seriesData = [];
        for (var i = 0; i < data.values.length; i++){
            seriesData.push([beginDate + (3600 * 1000 * 24 * i), data.values[i] * 2.54]);
        }  
		chart.series[0].setData(seriesData);
		chart.setTitle({text: site_attributes["name"] + "(" + site_attributes["elev"] + " ft)"});
   });
}

function selected(feature) {
    console.log("select:"+ feature.layer.name +":"+ feature.id + feature.attributes["SiteName"]);
	var highlight_point = new OpenLayers.Feature.Vector(feature.geometry);
	highlightLayer.removeAllFeatures();
    highlightLayer.addFeatures(highlight_point);
	var year = get_date().substring(0,4);
	if (feature.layer === sitesLayer) {
	    update_chart(feature.attributes, get_date());
	} else {
	    update_chart_snotel(feature.attributes, get_date());
	}
}
 
function unselected(feature) {
    console.log("unselected:" + feature.id);
	//feature.style = my_style2;
	//feature.layer.redraw();
}

function update_stations(){
    //var sites_url = 'geojson.php?date=' + get_date();
	var sites_url = 'geojson.php';
	sitesLayer = new OpenLayers.Layer.Vector('GHCN Sites', {
	    strategies: [new OpenLayers.Strategy.Fixed()],
		protocol: new OpenLayers.Protocol.HTTP({
		    url: sites_url, 
			format: new OpenLayers.Format.GeoJSON()
		}),
		styleMap: style_ghcn
	});
	map.addLayer(sitesLayer);
	map.addLayer(highlightLayer);
}

function update_stations_snotel(){
	var sites_url = 'snotel_geojson.php';
	snotelLayer = new OpenLayers.Layer.Vector('SNOTEL Sites', {
	    strategies: [new OpenLayers.Strategy.Fixed()],
		protocol: new OpenLayers.Protocol.HTTP({
		    url: sites_url, 
			format: new OpenLayers.Format.GeoJSON()
		}),
		styleMap: style_snotel
	});
	map.addLayer(snotelLayer);
}

function update_stations2(date){
    var sites_url = 'geojson.php' + '?date=' + date;
	sitesLayer.refresh({url: sites_url});
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
        div: "map",
        projection: "EPSG:4326",
        numZoomLevels: 11,
        zoom: 7
    });
	

	
	// Create base layers
    layerModisTerraTrueColor = new OpenLayers.Layer.WMTS({
        name: "Terra / MODIS Corrected Reflectance (True Color), 2012-06-08",
        url: GIBS_WMTS_GEO_ENDPOINT,
        layer: "MODIS_Terra_CorrectedReflectance_TrueColor",
        matrixSet: TILEMATRIXSET_GEO_250m,
        format: "image/jpeg",
        style: "",
        transitionEffect: "resize",
        projection: "EPSG:4326",
        numZoomLevels: 9,
        maxResolution: 0.5625,
        resolutions: [0.5625, 0.28125, 0.140625, 0.0703125, 0.03515625, 0.017578125, 0.0087890625, 0.00439453125, 0.002197265625], 
        serverResolutions: [0.5625, 0.28125, 0.140625, 0.0703125, 0.03515625, 0.017578125, 0.0087890625, 0.00439453125, 0.002197265625],
        'tileSize': new OpenLayers.Size(512, 512),
        isBaseLayer: true
    });
 
    // Create overlays: snow
	layerModisTerraSnow = new OpenLayers.Layer.WMTS({
		name: "Terra / MODIS Snow cover",
		url: GIBS_WMTS_GEO_ENDPOINT,
		layer: "MODIS_Terra_Snow_Cover",
		matrixSet: TILEMATRIXSET_GEO_500m,
		format: "image/png",
		style: "",
		transitionEffect: "resize",
		projection: "EPSG:4326",
		numZoomLevels: 9,
		maxResolution: 0.5625,
		resolutions: [0.5625, 0.28125, 0.140625, 0.0703125, 0.03515625, 0.017578125, 0.0087890625, 0.00439453125, 0.002197265625],
		serverResolutions: [0.5625, 0.28125, 0.140625, 0.0703125, 0.03515625, 0.017578125, 0.0087890625],
		'tileSize': new OpenLayers.Size(512, 512),
		isBaseLayer: false,
		visibility: false
	});
 
    // The "time" parameter isn't being included in tile requests to the server
    // in the current version of OpenLayers (2.12);  need to use this hack
    // to force the inclusion of the time parameter.
    //
    // If the time parameter is omitted, the current (UTC) day is retrieved
    // from the server
    layerModisTerraTrueColor.mergeNewParams({time:get_date()});
    layerModisTerraSnow.mergeNewParams({time:get_date()});
	
	
	//create overlays: WFS
	wfs = new OpenLayers.Layer.Vector(
		"GHCN Stations", {
			strategies: new OpenLayers.Strategy.BBOX(),
			protocol: new OpenLayers.Protocol.WFS({
				version: "1.0.0",
				srsName: "EPSG:4326",
				url: "http://snow.hydrodata.org/utah/services/index.php/wfs/write_xml",
				featureNS: "http://snow.hydrodata.org/",
				featureType: "hydroserver_1"
		})
	})
	
	
	
	// Add layers to the map
    map.addLayers([layerModisTerraTrueColor,
        layerModisTerraSnow]);
		
     
    // Add layer switcher control
    map.addControl(new OpenLayers.Control.LayerSwitcher());
 
    // Set global view
    var extent = "-115.0, 37.5, -108.0, 42.0";
    var OLExtent = new OpenLayers.Bounds.fromString(extent, false).transform(
        new OpenLayers.Projection("EPSG:4326"),
        map.getProjectionObject());
    map.zoomToExtent(OLExtent, true);
	
		
	highlightLayer = new OpenLayers.Layer.Vector("Highlighted Features", {
        displayInLayerSwitcher: false, 
        isBaseLayer: false
        //styleMap: highlight_style	
    });
		
	var sno_sites = new OpenLayers.Layer.WMS("Snow all sites",
	    mapserver_url,
	    {layers:"snow_stations", projection: "EPSG:4326", transparent:true, 
	    format:'image/png', info_format: "text/plain"});

	sno_wms = new OpenLayers.Layer.WMS("Snow sites",mapserver_url,
	{layers:"snow_daily", projection: "EPSG:3857", transparent:true, 
	    format:'image/png', info_format: "text/plain", time:get_date()},
	{featureInfoFormat: "text/plain"});
	
	update_stations();
	update_stations_snotel();
	
	//var selectedFeature;
	selectControl = new OpenLayers.Control.SelectFeature([sitesLayer, snotelLayer],
    {
        onSelect: selected,
		onUnselect: unselected,
		hover:false
    });
    map.addControl(selectControl);
    selectControl.activate();
	
	
	//map clicking event
	map.events.register("click", map, function(e) {
        var position = this.events.getMousePosition(e);
        var lonlat = map.getLonLatFromPixel(position);
        //var lonlatTransf = lonlat.transform(map.getProjectionObject(), proj4326);
		var metersPerPixel = map.getResolution();	//res is in meters per pixel
        var clickTolerance = 100.0;
        var date = get_date();		
		update_chart(lonlat.lat, lonlat.lon, date, metersPerPixel * clickTolerance);       
    });
})