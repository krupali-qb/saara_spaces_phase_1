/**@odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from  "@odoo/owl";
const actionRegistry = registry.category("actions");
class CustomReports extends Component {}
CustomReports.template = "saara_spaces_models.CustomReports";
//  Tag name that we entered in the first step.
actionRegistry.add("reports_tag", CustomReports);