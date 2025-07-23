/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";

export class ProjectSprintKanbanController extends KanbanController {
    setup() {
        super.setup();
    }

    onTestClick() {
    const projectId = this.props.context.default_project_id || this.props.context.active_id;

    this.actionService.doAction({
        type: 'ir.actions.act_window',
        res_model: 'project.task',
        name: 'Project Tasks',
        view_mode: 'list,form',
        views: [
            [false, 'list'],
            [false, 'form'],
        ],
        target: 'current',
       domain: [
        ['project_id', '=', projectId],
        ['sprint_id', '=', false],  // only tasks without sprint
    ],
        context: {
            default_project_id: projectId,
            create: true,
        },
    });
}

}

export const ProjectSprintKanbanView = {
    ...kanbanView,
    Controller: ProjectSprintKanbanController,
    buttonTemplate: "project_sprint_management.KanbanView.Buttons",
};

registry.category("views").add("project_sprint_kanban_custom", ProjectSprintKanbanView);

