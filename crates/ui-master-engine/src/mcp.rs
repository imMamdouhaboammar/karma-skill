use crate::rig_tools;
use serde_json::Value;
use std::io::{self, BufRead, Write};

pub async fn run_mcp_server() -> io::Result<()> {
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    let mut log_file = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open("/tmp/uim_mcp_traffic.log")
        .ok();

    for line in stdin.lock().lines() {
        let line = match line {
            Ok(l) => l,
            Err(_) => break,
        };
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        if let Some(ref mut f) = log_file {
            use std::io::Write as _;
            let _ = writeln!(f, ">>> INCOMING: {}", trimmed);
            let _ = f.flush();
        }

        let req: Value = match serde_json::from_str(trimmed) {
            Ok(v) => v,
            Err(e) => {
                let err_res = serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": null,
                    "error": { "code": -32700, "message": format!("Parse error: {}", e) }
                });
                writeln!(stdout, "{}", serde_json::to_string(&err_res).unwrap())?;
                stdout.flush()?;
                continue;
            }
        };

        // Standard JSON-RPC 2.0: Notifications do NOT have an "id" field and MUST NOT receive any response.
        let has_id = req.get("id").is_some() && !req["id"].is_null();
        let method = req.get("method").and_then(|m| m.as_str()).unwrap_or("");

        // Handle notifications silently
        if !has_id || method.starts_with("notifications/") || method == "initialized" || method.starts_with("$/") {
            continue;
        }

        let id = req["id"].clone();

        let res = match method {
            "initialize" => {
                let proto = req
                    .get("params")
                    .and_then(|p| p.get("protocolVersion"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("2024-11-05");

                serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "protocolVersion": proto,
                        "capabilities": {
                            "tools": {
                                "listChanged": false
                            }
                        },
                        "serverInfo": {
                            "name": "ui-master-rig",
                            "version": "0.2.0"
                        }
                    }
                })
            }

            "tools/list" => {
                let tools = rig_tools::list_rig_tools_manifest();
                serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "tools": tools
                    }
                })
            }

            "tools/call" => {
                let params = req.get("params");
                let name = params.and_then(|p| p.get("name")).and_then(|n| n.as_str()).unwrap_or("");
                let args_val = params.and_then(|p| p.get("arguments")).cloned().unwrap_or(serde_json::json!({}));
                let args_str = args_val.to_string();

                match rig_tools::execute_rig_tool(name, &args_str).await {
                    Ok(val) => {
                        serde_json::json!({
                            "jsonrpc": "2.0",
                            "id": id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": serde_json::to_string_pretty(&val).unwrap_or_default()
                                    }
                                ],
                                "isError": false
                            }
                        })
                    }
                    Err(e) => {
                        serde_json::json!({
                            "jsonrpc": "2.0",
                            "id": id,
                            "result": {
                                "isError": true,
                                "content": [
                                    {
                                        "type": "text",
                                        "text": format!("Tool execution error: {}", e)
                                    }
                                ]
                            }
                        })
                    }
                }
            }

            "ping" => {
                serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {}
                })
            }

            _ => {
                serde_json::json!({
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {
                        "code": -32601,
                        "message": format!("Method not found: {}", method)
                    }
                })
            }
        };

        let res_str = serde_json::to_string(&res).unwrap();
        if let Some(ref mut f) = log_file {
            use std::io::Write as _;
            let _ = writeln!(f, "<<< OUTGOING: {}", res_str);
            let _ = f.flush();
        }

        writeln!(stdout, "{}", res_str)?;
        stdout.flush()?;
    }

    Ok(())
}
