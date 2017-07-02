// Copyright (c) 2016, Helio de Jesus and contributors
// For license information, please see license.txt




frappe.query_reports["TESTES_GRID"] = {
	"filters": [

	]

},
fff()

function fff(){
//	alert("adada:")

	var grid;
	var columns = [
		{id: "title", name: "Title", field: "title"},
		{id: "duration", name: "Duration", field: "duration"},
		{id: "%", name: "% Complete", field: "percentComplete"},
		{id: "start", name: "Start", field: "start"},
		{id: "finish", name: "Finish", field: "finish"},
		{id: "effort-driven", name: "Effort Driven", field: "effortDriven"}
	];
	var options = {
		enableCellNavigation: true,
		enableColumnReorder: false
	};
	$(function () {
		var data = [];
		for (var i = 0; i < 500; i++) {
			data[i] = {
				title: "Task " + i,
				duration: "5 days",
				percentComplete: Math.round(Math.random() * 100),
				start: "01/01/2009",
				finish: "01/05/2009",
				effortDriven: (i % 5 == 0)
			};
		}
	alert(typeof(data))
	grid = new Slick.Grid("#myGrid", data, columns, options);
	})
		                

}

frappe.ui.form.on('TESTES_GRID', {

	init: function(){
		alert("ADFASDFASDFSAFDSA")
	    var columns = [{ id: 'col0', name: 'Time',      toolTip: 'Date/Time',   sort_type: 'date' , plot_master_time: 'true' },
		           { id: 'col1', name: 'Value 1',   toolTip: 'Value 1',     sort_type: 'float',     style: 'text-align: right;'},
		           { id: 'col2', name: 'Value 2',   toolTip: 'Value 2',     sort_type: 'float',     style: 'text-align: right;'},
		           { id: 'col3', name: 'Value 3',   toolTip: 'Value 3',     sort_type: 'float',     style: 'text-align: right;'},
	    ];                                                                                                                      
		                                                                                                                    
	    var options = { caption:            'Time line with diagram',                 
		            width:              '100%',                                                                             
		            maxHeight:          '100',                                                                              
		            locale:              'en',
	    };                                                                                                                      
		                                                                                                                    
	    var data = [{ col0: '2013/10/01 14:05', col1: '66,20', col2: '12124', col3: '12' },
		        { col0: '2013/10/01 14:10', col1: '22,10', col2: '23344', col3: '22' },
		        { col0: '2013/10/01 14:20', col1: '33,40', col2: '65472', col3: '55' },
		        { col0: '2013/10/01 14:30', col1: '77,90', col2: '81224', col3: '22' },
		        { col0: '2013/10/01 14:40', col1: '10,20', col2: '12421', col3: '55' },
		        { col0: '2013/10/01 14:50', col1: '12,24', col2: '23552', col3: '88' },
		        { col0: '2013/10/01 15:00', col1: '88,20', col2: '36333', col3: '65' },
		        { col0: '2013/10/01 15:20', col1: '45,30', col2: '23355', col3: '14' },
		        { col0: '2013/10/01 15:40', col1: '55,40', col2: '23566', col3: '23' },
	    ];                                                                                                                      
		                                                                                                                    
	    var additional_menu_entries = [{ label: 'Additional entry', hint: 'Additional entry just for fun', action: function(t){alert('Just for fun');} }];   
		                                                                                                                    
	    Slick.Grid('demo_div', data, columns, options, additional_menu_entries);                                   
	},
	load: function(){
		alert("bbbbbbbb")
	}

});
