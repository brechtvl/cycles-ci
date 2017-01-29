
google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(draw_charts);

// select handler for extra info on click
function select_handler(device, selected_chart, elem, ncols)
{
	var selectedItem = selected_chart.getSelection()[0];
	if (selectedItem && selectedItem.row != null)
	{
		// create image
		imagename = device['images'][selectedItem.row][(selectedItem.column - 1)/ncols];
		image = '<div style="width: 100%; background-color: #000; text-align:center">';
		image += '<img src="images/' + imagename + '"/ style="max-width: 100%; max-height: 520px;">';
		image += '</div>';

		// create table of commits
		table = '';

		if (device['commits'])
		{
			commits = device['commits'][selectedItem.row];
			table += '<div><table>';
			for (var j = 0; j < commits.length; j++)
			{
				hash = commits[j]['hash'];
				link = '<b><a href="https://developer.blender.org/rB' + hash + '">' + hash + '</a></b>';
				table += '<tr><td>' + link + '</td><td>' + commits[j]['subject'] + '</td>';
			}
			table += '</table></div>'
		}

		elem.innerHTML = image + table + '<div style="clear: both;"/>';
		elem.style = 'display: block;';
	}
	else
	{
		// clear contents
		elem.style = 'display: none;';
		elem.innerHTML = '';
	}
}

// master charts
function draw_master_charts()
{
	// load json data
	var json_data = $.ajax({url: "master.json", dataType: "json", async: false}).responseJSON;

	// clear contents
	charts_elem = document.getElementById("master-charts");
	while(charts_elem.firstChild)
	{
		charts_elem.removeChild(charts_elem.firstChild);
	}

	// draw charts for each device
	for (var i = 0; i < json_data.length; i++)
	{
		device = json_data[i];

		// chart drawing options
		var options = {
			title: device["name"],
			//curveType: 'function',
			chartArea: {'height': '75%'},
			vAxis: {title: "Render Time", minorGridlines: {count: 3}, format:'#s'},
			pointsVisible: true,
			pointSize: 2.5,
			tooltip: { isHtml: true },
			intervals: { 'style': 'area', fillOpacity: 0.35 },
			//interpolateNulls: true,
		};

		// create chart div
		elem = document.createElement('div');
		elem.id = device["id"];
		elem.style = "width: 900px; height: 500px; padding: 10px 0px; ";
		charts_elem.appendChild(elem)

		// create chart
		var data = new google.visualization.DataTable(device["data"]);
		var chart = new google.visualization.LineChart(elem);
		chart.draw(data, options);

		// hidden element for extra info
		elem = document.createElement('div');
		elem.style = 'display: none;';
		charts_elem.appendChild(elem);

		google.visualization.events.addListener(chart, 'select', select_handler.bind(null, device, chart, elem, 4));
	}
}

// differential revision and local tag charts
function draw_comparison_charts(json_filename, element_id)
{
	// load json data
	var json_data = $.ajax({url: json_filename, dataType: "json", async: false}).responseJSON;

	// clear contents
	charts_elem = document.getElementById(element_id);
	if (json_data.length == 0)
	{
		charts_elem.innerHTML = 'No data.';
	}
	else
	{
		charts_elem.innerHTML = '';
	}

	// draw title for each revision
	for (var j = 0; j < json_data.length; j++)
	{
		revision_data = json_data[j];

		// create title bar
		title_elem = document.createElement('h3')
		title_elem.id = "revision-title";
		title_elem.onclick = revision_handler;
		title_elem.revision_id = j;
		title_elem.chart_visible = false;

		elem = document.createElement('b');
		elem.textContent = revision_data.name + ' '
		title_elem.appendChild(elem)

		elem = document.createElement('span');
		elem.href = 'https://developer.blender.org/' + revision_data.name
		elem.textContent = revision_data.description
		elem.style = 'font-weight: normal;'
		title_elem.appendChild(elem)

		charts_elem.appendChild(title_elem)

		// create container div
		parent_div = document.createElement('div')
		charts_elem.appendChild(parent_div)
	}

	function revision_handler()
	{
		var title_elem = this;
		var parent_div = this.nextSibling;

		parent_div.innerHTML = '';

		title_elem.chart_visible = !title_elem.chart_visible;
		if (!title_elem.chart_visible)
			return;

		var j = title_elem.revision_id;
		var revision_data = json_data[j];

		// draw charts for each device
		for (var i = 0; i < revision_data.data.length; i++)
		{
			device = revision_data.data[i];

			// chart drawing options
			var options = {
				title: device["name"],
				chartArea: {'height': '75%'},
				vAxis: {title: "Relative Render Time", minorGridlines: {count: 3}, baseline: 0.0, minValue: -0.025, maxValue: 0.025, format: '#.#%'},
				colors: ['#ddd', '#3366CC', '#DC3912', '#FF9900', '#109618', '#990099', '#3B3EAC'],
				dataOpacity: 1,
				tooltip: { isHtml: true },
				intervals: { 'style': 'points', fillOpacity: 0.7, pointSize: 3 },
			};

			// create chart div
			elem = document.createElement('div');
			elem.id = device["id"];
			elem.style = "width: 900px; height: 500px; padding: 10px 0px; ";
			parent_div.appendChild(elem)

			// create chart
			var data = new google.visualization.DataTable(device["data"]);
			var chart = new google.visualization.ScatterChart(elem);
			chart.draw(data, options);

			// hidden element for extra info
			elem = document.createElement('div');
			elem.style = 'display: none;';
			parent_div.appendChild(elem);

			google.visualization.events.addListener(chart, 'select', select_handler.bind(null, device, chart, elem, 1));
		}
	}
}

function draw_charts()
{
	draw_master_charts();
	draw_comparison_charts('diffs.json', 'diff-charts');
	draw_comparison_charts('tags.json', 'tag-charts');
}

