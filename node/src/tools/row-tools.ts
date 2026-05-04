import { z } from "zod";
import type { ServerInstance } from "../common";
import { getAnalyticsClient, config } from '../utils/apiUtil';
import { retryWithFallback } from "../utils/common";
import { ToolResponse, logAndReturnError } from "../utils/common";


export function registerRowTools(server: ServerInstance) {

    server.registerTool("add_row",
    {
        description: `
        <use_case>
        Adds a new row to the specified table.
        </use_case>
        `,
        inputSchema: {
            workspace_id: z.string().describe("The ID of the workspace where the table is located"),
            table_id: z.string().describe("The ID of the table to which the row will be added"),
            columns: z.record(z.string(), z.string()).describe("A dictionary containing the column names and their corresponding values for the new row"),
            org_id: z.string().optional().describe("The organization ID for the request, if applicable. This is a mandatory parameter for shared workspaces")
        },
        annotations: {
          title: "Add Row",
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: false
        }
    },
    async ({ workspace_id, table_id, columns, org_id }) => {
        try {
            if (!org_id) {
                org_id = config.ORGID || "";
            }
            return await retryWithFallback([org_id], workspace_id, "WORKSPACE", async (org_id, workspace, table, cols) => {
                const analyticsClient = getAnalyticsClient();
                const view = analyticsClient.getViewInstance(org_id || "", workspace, table);
                await view.addRow(cols);
                return ToolResponse("Row added successfully.");
            },workspace_id, table_id, columns);
        } catch (err) {
            return logAndReturnError(err, "Error while adding row");
        }
    });

    server.registerTool("delete_rows",
    {
        description: `
        <use_case>
        Deletes rows from the specified table based on the given criteria.
        </use_case>
        `,
        inputSchema: {
            workspace_id: z.string().describe("The ID of the workspace where the table is located"),
            table_id: z.string().describe("The ID of the table from which rows will be deleted"),
            criteria: z.string().describe("A string representing the criteria for selecting rows to delete. Example criteria: \"\\\"SalesTable\\\".\\\"Region\\\"='East'\""),
            org_id: z.string().optional().describe("The organization ID for the request, if applicable. This is a mandatory parameter for shared workspaces")
        },
        annotations: {
          title: "Delete Rows",
          readOnlyHint: false,
          destructiveHint: true,
          idempotentHint: false,
          openWorldHint: false
        }
    },
    async ({ workspace_id, table_id, criteria, org_id }) => {
        try {
            if (!org_id) {
                org_id = config.ORGID || "";
            }
            return await retryWithFallback([org_id], workspace_id, "WORKSPACE", async (org_id, workspace, table, crit) => {
                const analyticsClient = getAnalyticsClient();
                const view = analyticsClient.getViewInstance(org_id || "", workspace, table);
                await view.deleteRow(crit);
                return ToolResponse("Rows deleted successfully.");
            }, workspace_id, table_id, criteria);
        } catch (err) {
            return logAndReturnError(err, "Error while deleting rows");
        }
    });

    server.registerTool("update_rows",
    {
        description: `
        <use_case>
        Updates rows in the specified table based on the given criteria.
        </use_case>
        `,
        inputSchema: {
            workspace_id: z.string().describe("The ID of the workspace where the table is located"),
            table_id: z.string().describe("The ID of the table to be updated"),
            columns: z.record(z.string(), z.string()).describe("A dictionary containing the column names and their new values for the update"),
            criteria: z.string().describe("A string representing the criteria for selecting rows to update. Example criteria: \"\\\"SalesTable\\\".\\\"Region\\\"='East'\""),
            org_id: z.string().optional().describe("The organization ID for the request, if applicable. This is a mandatory parameter for shared workspaces")
        },
        annotations: {
          title: "Update Rows",
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: true, //Update is considered idempotent because we expect the input to be the desired final value of the row(s). There is no scope for updating based on current value of the row, which may lead to non-idempotency.
          openWorldHint: false
        }
    },
    async ({ workspace_id, table_id, columns, criteria, org_id }) => {
        try {
            if (!org_id) {
                org_id = config.ORGID || "";
            }
            return await retryWithFallback([org_id], workspace_id, "WORKSPACE", async (org_id, workspace, table, crit, cols) => {
                const analyticsClient = getAnalyticsClient();
                const view = analyticsClient.getViewInstance(org_id, workspace, table);
                await view.updateRow(cols, crit);
                return ToolResponse("Rows updated successfully.");
            }, workspace_id, table_id, criteria, columns);
        } catch (err) {
            return logAndReturnError(err, "Error while updating rows");
        }
    });
}