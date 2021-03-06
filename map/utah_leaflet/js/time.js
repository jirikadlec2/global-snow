/**
 * GIBS Web Examples
 *
 * Copyright 2013 - 2014 United States Government as represented by the
 * Administrator of the National Aeronautics and Space Administration.
 * All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

$(function() {

    // When the day is changed, cache previous layers. This allows already
    // loaded tiles to be used when revisiting a day. Since this is a
    // simple example, layers never "expire" from the cache.
    var cache1 = {};
	var cache2 = {};
	
	var template1 =
	"http://map1{s}.vis.earthdata.nasa.gov/wmts-webmerc/" +
	"{layer}/default/{time}/{tileMatrixSet}/{z}/{y}/{x}.png";
	
	var template2 =
	"http://map1{s}.vis.earthdata.nasa.gov/wmts-webmerc/" +
	"{layer}/default/{time}/{tileMatrixSet}/{z}/{y}/{x}.jpg";

    // GIBS needs the day as a string parameter in the form of YYYY-MM-DD.
    // Date.toISOString returns YYYY-MM-DDTHH:MM:SSZ. Split at the "T" and
    // take the date which is the first part.
    var dayParameter = function(day) {
        return day.toISOString().split("T")[0];
    };

    var map = L.map("map", {
        center: [40.205, -111.70],
        zoom: 10,
        // Animation interferes with smooth scrolling of the slider once
        // all the layers are cached
        fadeAnimation: false
    });

    var update = function(selectedDay) {
        // Using the day as the cache key, see if the layer is already
        // in the cache.
        var key = selectedDay;
        var layer1 = cache1[key];
		var layer2 = cache2[key];

        // If not, create a new layer and add it to the cache.
        if ( !layer1 ) {
            layer1 = createOverlay(selectedDay, "MODIS_Terra_Snow_Cover", 8, template1);
            cache1[key] = layer1;
        }
		
		if ( !layer2 ) {
            layer2 = createOverlay(selectedDay, "MODIS_Terra_CorrectedReflectance_TrueColor", 9, template2);
            cache2[key] = layer2;
        }

        // There is only one layer in this example, but remove them all
        // anyway
        clearLayers();

        // Add the new layer for the selected time
		// Only do this if appropriate checkbox is checked
		if( $("#checkbox_snow2").is(':checked') ){
			map.addLayer(layer2);
		}
		if( $("#checkbox_snow").is(':checked') ){
			map.addLayer(layer1);
		}
    };

    var clearLayers = function() {
        map.eachLayer(function(layer) {	
            if (layer.options.myName === "overlay") {			
                map.removeLayer(layer);
			}
        });
    };
	
	
	

	var createBackground = function() {
		L.tileLayer('http://{s}.tiles.mapbox.com/v3/{id}/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
				'<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
				'Imagery © <a href="http://mapbox.com">Mapbox</a>',
			id: 'examples.map-i875mjb7',
			myName: 'background'
		}).addTo(map);
	}

    var createOverlay = function(day, layerName, supportedZoom, templateURL) {
		var new_layer = L.tileLayer(templateURL, {
			layer: layerName,
			tileMatrixSet: "GoogleMapsCompatible_Level" + supportedZoom,
			maxNativeZoom: supportedZoom,
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
				"<a href='http://earthdata.nasa.gov/gibs'>" +
				"NASA EOSDIS GIBS</a>&nbsp;&nbsp;&nbsp;" +
				"<a href='http://github.com/nasa-gibs/web-examples/blob/release/leaflet/js/webmercator-epsg3857.js'>" +
				"View Source" +
				"</a>",
            myName: "overlay"				
		});
		return new_layer; 
	}
	
	var createOverlay2 = function(day) {
		var new_layer2 = L.tileLayer(template, {
			layer: "MODIS_Terra_CorrectedReflectance_TrueColor",
			tileMatrixSet: "GoogleMapsCompatible_Level9",
			maxNativeZoom: 9,
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
				"<a href='http://earthdata.nasa.gov/gibs'>" +
				"NASA EOSDIS GIBS</a>&nbsp;&nbsp;&nbsp;" +
				"<a href='http://github.com/nasa-gibs/web-examples/blob/release/leaflet/js/webmercator-epsg3857.js'>" +
				"View Source" +
				"</a>",
            myName: "overlay"				
		});
		return new_layer2; 
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
	
	$("#checkbox_snow").click( function(){     
	    var d = $("#datepicker1").datepicker("getDate");
	    update(dayParameter(d)); 
    });
	
	$("#checkbox_snow2").click( function(){     
	    var d = $("#datepicker1").datepicker("getDate");
	    update(dayParameter(d)); 
    });
    
	//set the default layers
	backgroundLayer = createBackground();
    $("#datepicker1").datepicker('setDate', new Date());
	var today = new Date();
	today.setDate(today.getDate() - 1);
	var yesterdayYMD = today.toISOString().slice(0,10);
    update(yesterdayYMD);
});
