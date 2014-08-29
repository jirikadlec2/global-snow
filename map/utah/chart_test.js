var chart;

$(document).ready(function () {
//var series_url='http://localhost:8080/map/get_time_series.php?lat1=49&lat2=49.5&lon1=12&lon2=15&id=2&date=2014-01-01';
//var url_test='series2.json'

var chart_options = {
	chart: {
		renderTo: 'chart_container',
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