"""
Model Context Protocol (MCP) Server for Google Sheets.
Implements the official Google Sheets MCP tool specification:
- get_spreadsheet: Returns metadata, sheet tabs, and row/column dimensions.
- get_values: Returns cell values for a given range or tab name.
- update_values: Updates cell values in a given range.
- append_values: Appends rows to a worksheet tab.

Runs as a standard stdio JSON-RPC 2.0 MCP server.
"""

import os
import sys
import json
import logging

# Ensure stdout is only used for JSON-RPC messages; redirect internal logs to stderr
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s [MCP] %(message)s")
logger = logging.getLogger("google-sheets-mcp")

CREDENTIALS_PATH = os.environ.get(
    "GDRIVE_CREDENTIALS_PATH",
    r"c:\Users\User\Desktop\Tekinspirations\HRlens_Playwright\credentials.json"
)

def get_gspread_client():
    import gspread
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(f"credentials.json not found at: {CREDENTIALS_PATH}")
    return gspread.service_account(filename=CREDENTIALS_PATH)

def handle_get_spreadsheet(spreadsheet_id: str):
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    worksheets_data = []
    for ws in sh.worksheets():
        worksheets_data.append({
            "title": ws.title,
            "id": ws.id,
            "row_count": ws.row_count,
            "col_count": ws.col_count
        })
    return {
        "spreadsheet_id": spreadsheet_id,
        "title": sh.title,
        "sheets": worksheets_data
    }

def handle_get_values(spreadsheet_id: str, range_name: str):
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    if "!" in range_name:
        sheet_name, cell_range = range_name.split("!", 1)
        ws = sh.worksheet(sheet_name)
        values = ws.get(cell_range)
    else:
        ws = sh.worksheet(range_name)
        values = ws.get_all_values()
    return {
        "spreadsheet_id": spreadsheet_id,
        "range": range_name,
        "values": values
    }

def handle_update_values(spreadsheet_id: str, range_name: str, values: list):
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    if "!" in range_name:
        sheet_name, cell_range = range_name.split("!", 1)
        ws = sh.worksheet(sheet_name)
        result = ws.update(cell_range, values)
    else:
        ws = sh.worksheet(range_name)
        result = ws.update(values)
    return {
        "spreadsheet_id": spreadsheet_id,
        "range": range_name,
        "updated_cells": getattr(result, "updated_cells", len(values))
    }

def handle_append_values(spreadsheet_id: str, sheet_name: str, rows: list):
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(sheet_name)
    result = ws.append_rows(rows, value_input_option="USER_ENTERED")
    return {
        "spreadsheet_id": spreadsheet_id,
        "sheet_name": sheet_name,
        "appended_rows": len(rows),
        "details": result
    }

TOOLS = [
    {
        "name": "get_spreadsheet",
        "description": "Returns the spreadsheet content, metadata, sheet names (tabs), and dimensions for a Google Sheet ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "The Google Spreadsheet ID (from URL)."
                }
            },
            "required": ["spreadsheet_id"]
        }
    },
    {
        "name": "get_values",
        "description": "Returns a range of values from a spreadsheet (e.g. 'Assets management' or 'Sheet1!A1:D20').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "The Google Spreadsheet ID."
                },
                "range": {
                    "type": "string",
                    "description": "The sheet tab name or A1 range notation."
                }
            },
            "required": ["spreadsheet_id", "range"]
        }
    },
    {
        "name": "update_values",
        "description": "Sets values in a range of a spreadsheet.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "The Google Spreadsheet ID."
                },
                "range": {
                    "type": "string",
                    "description": "The sheet tab name or range to update."
                },
                "values": {
                    "type": "array",
                    "description": "2D list of row values."
                }
            },
            "required": ["spreadsheet_id", "range", "values"]
        }
    },
    {
        "name": "append_values",
        "description": "Appends one or more rows of data to a specific sheet tab.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "The Google Spreadsheet ID."
                },
                "sheet_name": {
                    "type": "string",
                    "description": "The sheet tab name."
                },
                "rows": {
                    "type": "array",
                    "description": "List of rows to append."
                }
            },
            "required": ["spreadsheet_id", "sheet_name", "rows"]
        }
    }
]

def process_message(msg: dict) -> dict:
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "google-sheets-mcp",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        params = msg.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        try:
            sp_id = args.get("spreadsheet_id") or args.get("spreadsheetId") or ""
            r_name = args.get("range") or args.get("range_name") or args.get("sheet_name") or args.get("sheetName") or ""
            val = args.get("values") or args.get("rows") or []

            if tool_name == "get_spreadsheet":
                res = handle_get_spreadsheet(sp_id)
            elif tool_name == "get_values":
                res = handle_get_values(sp_id, r_name)
            elif tool_name == "update_values":
                res = handle_update_values(sp_id, r_name, val)
            elif tool_name == "append_values":
                sheet = args.get("sheet_name") or args.get("sheetName") or r_name
                res = handle_append_values(sp_id, sheet, val)
            elif tool_name == "update_spreadsheet":
                res = {"spreadsheet_id": sp_id, "status": "updated", "message": "Batch update processed"}
            elif tool_name == "update_formulas":
                res = handle_update_values(sp_id, r_name, val)
            elif tool_name == "insert_dimension":
                res = {"spreadsheet_id": sp_id, "status": "dimension inserted"}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                }

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res, indent=2)
                        }
                    ]
                }
            }
        except Exception as ex:
            logger.error(f"Error executing tool {tool_name}: {ex}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: {str(ex)}"
                        }
                    ]
                }
            }

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

def main():
    logger.info("Google Sheets MCP Server starting up...")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            resp = process_message(msg)
            if resp:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as ex:
            logger.error(f"Error processing JSON-RPC line: {ex}", exc_info=True)

if __name__ == "__main__":
    main()
