frappe.provide('frappe.pages');
frappe.provide('frappe.views');
frappe.provide('sample_register');
//frappe.require("assets/angola_erp/js/lib/slickgrid_extended/slickgrid_extended.js");
//frappe.require("assets/angola_erp/js/lib/slickgrid_extended/plot_diagram.js");
//frappe.require("assets/angola_erp/js/lib/slickgrid_extended/slickgrid_extended.css");

frappe.require('assets/frappe/js/lib/slickgrid/slick.grid.js');
frappe.require('assets/frappe/js/lib/slickgrid/slick.grid.css');
//frappe.require("assets/frappe/js/lib/slickgrid/slick.core.js");
//frappe.require("assets/frappe/js/lib/slickgrid/slick.editors.js");
//frappe.require("assets/frappe/js/lib/slickgrid/slick.formatters.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.checkboxselectcolumn.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.rowselectionmodel.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.autotooltips.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellrangedecorator.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellrangeselector.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellcopymanager.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellexternalcopymanager.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellselectionmodel.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.rowselectionmodel.js");
//frappe.require("assets/frappe/js/lib/slickgrid/plugins/slick.cellselectionmodel.js");



frappe.ui.form.on("jobcard", "onload", function(frm,doctype,name) {

    // $().appendTo($(wrapper).find('.layout-main-section'));
	alert("adfasdfasdfasf")

    $(cur_frm.fields_dict.mygrid.wrapper).append( "<table width='100%>\
  <tr>\
    <td valign='top' width='50%'>\
      <div id='myGrid' style='width:100%;height:300px;''></div>\
    </td>\
  </tr>\
</table>" );

});

