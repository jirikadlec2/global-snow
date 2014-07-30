$(function () {
    var url_test='series2.json'
    // Get the CSV and create the chart
    $.getJSON(url_test, function (my_data) {
        
        $('#chart_container').highcharts({
            chart: {
                zoomType: 'x'
            },
            title: {
                text: 'Snow depth: Praha'
            },
            xAxis: {
                type: 'datetime',
                minRange: 14 * 24 * 3600000 // fourteen days
            },
            yAxis: {
                title: {
                    text: 'Snow depth (cm)'
                }
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                area: {
                    fillColor: {
                        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 0},
                        stops: [
                            [0, Highcharts.getOptions().colors[0]],
                            [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                        ]
                    },
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
            series: [{
                type: 'area',
                name: 'Snow Depth',
                pointInterval: 24 * 3600 * 1000, //1 day
                pointStart: Date.UTC(2006, 0, 01),
                data: my_data
            }]
        });
    });
});