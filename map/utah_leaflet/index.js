var map = L.map('map').setView([40.205, -111.70], 11);

		L.tileLayer('https://{s}.tiles.mapbox.com/v3/{id}/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
				'<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
				'Imagery © <a href="http://mapbox.com">Mapbox</a>',
			id: 'examples.map-i875mjb7'
		}).addTo(map);


		
		
		var template =
        "https://map1{s}.vis.earthdata.nasa.gov/wmts-webmerc/" +
        "{layer}/default/{time}/{tileMatrixSet}/{z}/{y}/{x}.png";

		var layer = L.tileLayer(template, {
			layer: "MODIS_Terra_Snow_Cover",
			tileMatrixSet: "GoogleMapsCompatible_Level8",
			maxNativeZoom: 8,
			maxZoom: 18,
			time: "2014-10-13",
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
				"</a>"
		});

		map.addLayer(layer);