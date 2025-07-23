/** @odoo-module **/

import { KanbanColumn } from "@web/views/kanban/kanban_column";
import { registry } from "@web/core/registry";

export class TaskKanbanColumn extends KanbanColumn {
    setup() {
        super.setup();
        this.sumField = this.props.arch.attrs.sum_field || "points";
    }

    get progressBar() {
        const total = this.props.records.reduce((sum, record) => {
            return sum + (record.data[this.sumField] || 0);
        }, 0);

        return [{
            value: total,
            maxValue: total,
            label: `${total} pts`
        }];
    }
}

registry.category("kanban_columns").add("project_task_kanban_column", TaskKanbanColumn);

