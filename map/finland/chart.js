var chart;


function get_date_for_chart(date) {
    var year = date.substring(0,4);
	var mon = parseInt(date.substring(5,7));
	var day = date.substring(8,10);
	return Date.UTC(year, mon-1, day);
}

function get_chart_url(st_id, year) {
	return "http://api.snow.hydrodata.org/values/" + st_id + "/" + year;
}

function get_hydrologic_year(date) {
   var year = parseInt(date.substring(0,4));
   var mon = parseInt(date.substring(5,7));
   if (mon > 10){
     year = year + 1;
   }
   return year;
}

function update_chart(station_id, selected_date, site_name) { 
   var hydro_year = get_hydrologic_year(selected_date);
   var beginDate = Date.UTC((hydro_year - 1), 9, 1);
   var series_url = get_chart_url(station_id, hydro_year);
   console.log('update_chart: load data from ' + series_url);
   $.getJSON(series_url, function(data) {
        
        for (var i = 0; i < data.values.length; i++){
		    var p = data.values[i][0].split('-');
            data.values[i][0] = Date.UTC(p[0], p[1]-1, p[2]);
        }  
		chart.series[0].setData(data.values);
		//chart.setTitle({text: site_name});
		chart.setTitle({text: ''});
		var sel_date = get_date_for_chart(selected_date);
		chart.xAxis[0].removePlotLine('plot-line-1');
	    chart.xAxis[0].addPlotLine({ value: sel_date, color: 'red', width: 2, zIndex: 5, id: 'plot-line-1'});
   });
}


$(document).ready(function () {

var chart_options = {
	chart: {
		renderTo: 'chart',
		zoomType: 'x',
	},
	title: {
		text: 'Snow depth: Select site on map'
	},
	xAxis: {
		type: 'datetime',
		minRange: 14 * 24 * 3600000
	},
	yAxis: {
		title: {
			text: 'Snow(cm)'
		},
		min: 0.0
	},
	legend: {
		enabled: false
	},
	plotOptions: {
		area: {
			fillColor: Highcharts.getOptions().colors[0],
			marker: {
				radius: 2
			},
			lineWidth: 1,
			states: {
				hover: {
					lineWidth: 1
				}
			},
			threshold: null
		}
	},
	series: [{}]
};

chart_options.series[0].type = 'area';
chart_options.series[0].name = 'Snow Depth';
chart = new Highcharts.Chart(chart_options);

});