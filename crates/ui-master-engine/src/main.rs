mod audit;
mod contrast;
mod crx;
mod mcp;
mod rig_tools;
mod skills;
mod trace;

use std::env;
use std::path::Path;

const BANNER: &str = r#"
██╗   ██╗██╗      ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ 
██║   ██║██║      ████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
██║   ██║██║█████╗██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝
██║   ██║██║╚════╝██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗
╚██████╔╝██║      ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║
 ╚═════╝ ╚═╝      ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
UI-Master Engine (Rust + Rig Native Core) — Architecture & Multi-Agent Suite
"#;

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_help();
        return;
    }

    let command = args[1].as_str();
    let json_flag = args.iter().any(|a| a == "--json");

    match command {
        "mcp" => {
            if let Err(e) = mcp::run_mcp_server().await {
                eprintln!("MCP server error: {}", e);
            }
        }

        "rig" => {
            if args.len() < 3 {
                eprintln!("Usage: ui-master-engine rig <list|call> [args]");
                return;
            }
            let sub = args[2].as_str();
            match sub {
                "list" => {
                    let manifest = rig_tools::list_rig_tools_manifest();
                    println!("{}", serde_json::to_string_pretty(&manifest).unwrap());
                }
                "call" => {
                    if args.len() < 5 {
                        eprintln!("Usage: ui-master-engine rig call <tool_name> '<json_arguments>'");
                        eprintln!("Example: ui-master-engine rig call ui_contrast '{{\"fg\":\"#0f172a\",\"bg\":\"#ffffff\"}}'");
                        return;
                    }
                    let tool_name = &args[3];
                    let raw_args = &args[4];
                    match rig_tools::execute_rig_tool(tool_name, raw_args).await {
                        Ok(res) => println!("{}", serde_json::to_string_pretty(&res).unwrap()),
                        Err(e) => eprintln!("Error executing Rig tool '{}': {}", tool_name, e),
                    }
                }
                _ => eprintln!("Unknown rig subcommand: {}", sub),
            }
        }

        "audit" => {
            let target_path = args.get(2).map(|s| s.as_str()).unwrap_or(".");
            match audit::scan_path(Path::new(target_path)) {
                Ok(summary) => {
                    if json_flag {
                        println!("{}", serde_json::to_string_pretty(&summary).unwrap());
                    } else {
                        println!("\n🔍 UI-Master Anti-Slop & Quality Audit Report");
                        println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                        println!("Files scanned : {}", summary.files_scanned);
                        println!("Total findings: {} (BLOCK: {}, FLAG: {})", summary.violations_count, summary.blocks, summary.flags);
                        println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
                        for v in summary.violations {
                            let badge = if v.severity == "BLOCK" { "🔴 BLOCK" } else { "🟡 FLAG " };
                            println!("{} [{}] {}:{}", badge, v.rule, v.file, v.line);
                            println!("   Issue: {}", v.message);
                            println!("   Fix  : {}\n", v.fix);
                        }
                    }
                }
                Err(e) => eprintln!("Error running audit: {}", e),
            }
        }

        "contrast" => {
            if args.len() < 4 {
                eprintln!("Usage: ui-master-engine contrast <foreground> <background> [--json]");
                eprintln!("Example: ui-master-engine contrast '#0f172a' '#ffffff'");
                return;
            }
            let fg = match contrast::RgbColor::parse(&args[2]) {
                Ok(c) => c,
                Err(e) => { eprintln!("Error parsing foreground: {}", e); return; }
            };
            let bg = match contrast::RgbColor::parse(&args[3]) {
                Ok(c) => c,
                Err(e) => { eprintln!("Error parsing background: {}", e); return; }
            };

            let report = contrast::calculate_contrast(&fg, &bg);
            if json_flag {
                println!("{}", serde_json::to_string_pretty(&report).unwrap());
            } else {
                println!("\n🎨 WCAG 2.2 Color Contrast Analysis");
                println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                println!("Foreground : {} ({})", report.fg.hex, args[2]);
                println!("Background : {} ({})", report.bg.hex, args[3]);
                println!("Ratio      : {}", report.formatted_ratio);
                println!("AA Normal  : {}", if report.passes_aa_normal { "✅ PASS (>=4.5:1)" } else { "❌ FAIL (<4.5:1)" });
                println!("AA Large   : {}", if report.passes_aa_large { "✅ PASS (>=3.0:1)" } else { "❌ FAIL (<3.0:1)" });
                println!("AAA Normal : {}", if report.passes_aaa_normal { "✅ PASS (>=7.0:1)" } else { "❌ FAIL (<7.0:1)" });
                println!("UI Graphic : {}", if report.passes_ui_component { "✅ PASS (>=3.0:1)" } else { "❌ FAIL (<3.0:1)" });
                println!("\nVerdict: {}\n", report.recommendation);
            }
        }

        "crx" => {
            let target_path = args.get(2).map(|s| s.as_str()).unwrap_or(".");
            match crx::audit_crx(Path::new(target_path)) {
                Ok(report) => {
                    if json_flag {
                        println!("{}", serde_json::to_string_pretty(&report).unwrap());
                    } else {
                        println!("\n🛡️ Chrome Extension (CRX) Architecture & Isolation Report");
                        println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                        println!("Status         : {}", report.overall_status);
                        println!("Manifest V3    : {}", if report.is_manifest_v3 { "✅ YES" } else { "❌ NO" });
                        println!("Shadow DOM Safe: {}", if report.has_shadow_dom_isolation { "✅ YES" } else { "❌ VIOLATION" });
                        println!("Popup Bounds   : {}", if report.popup_dimensions_valid { "✅ VALID" } else { "❌ OVERSIZED" });
                        println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
                        for f in report.findings {
                            let badge = match f.severity.as_str() {
                                "PASS" => "🟢 PASS ",
                                "FLAG" => "🟡 FLAG ",
                                _ => "🔴 BLOCK",
                            };
                            println!("{} [{}] {}", badge, f.category, f.message);
                            println!("   Action: {}\n", f.recommendation);
                        }
                    }
                }
                Err(e) => eprintln!("Error analyzing CRX: {}", e),
            }
        }

        "skills" => {
            let query = args[2..].iter().filter(|s| *s != "--json").cloned().collect::<Vec<String>>().join(" ");
            if query.is_empty() {
                eprintln!("Usage: ui-master-engine skills <query>");
                return;
            }
            match skills::search_skills(&query, 10) {
                Ok(hits) => {
                    if json_flag {
                        println!("{}", serde_json::to_string_pretty(&hits).unwrap());
                    } else {
                        println!("\n⚡ Sub-millisecond UI Skills BM25 Search: '{}'", query);
                        println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                        for (i, h) in hits.iter().enumerate() {
                            println!("{}. {} (score: {:.1})", i + 1, h.slug, h.score);
                            println!("   Topics: [{}]", h.topics.join(", "));
                            println!("   Desc  : {}\n", h.description);
                        }
                    }
                }
                Err(e) => eprintln!("Error searching skills: {}", e),
            }
        }

        "get-skill" => {
            if args.len() < 3 {
                eprintln!("Usage: ui-master-engine get-skill <slug>");
                return;
            }
            let slug = &args[2];
            match skills::get_skill_content(slug) {
                Ok(content) => println!("{}", content),
                Err(e) => eprintln!("Error: {}", e),
            }
        }

        "trace" => {
            if args.len() < 3 {
                eprintln!("Usage: ui-master-engine trace <init|step|show> [args]");
                return;
            }
            let sub = args[2].as_str();
            match sub {
                "init" => {
                    let task = args.get(3).map(|s| s.as_str()).unwrap_or("Generic UI Task");
                    match trace::init_trace(task) {
                        Ok(t) => {
                            if json_flag {
                                println!("{}", serde_json::to_string_pretty(&t).unwrap());
                            } else {
                                println!("✅ Initialized Trace: {}", t.trace_id);
                                println!("   Task: {}", t.task);
                                println!("   Circuit Breaker: {}", t.circuit_breaker);
                            }
                        }
                        Err(e) => eprintln!("Error init trace: {}", e),
                    }
                }
                "step" => {
                    if args.len() < 7 {
                        eprintln!("Usage: ui-master-engine trace step <trace_id> <agent> <status> <summary>");
                        return;
                    }
                    let trace_id = &args[3];
                    let agent = &args[4];
                    let status = &args[5];
                    let summary = &args[6];
                    match trace::record_step(trace_id, agent, status, summary, 120, 0.95) {
                        Ok(t) => {
                            if json_flag {
                                println!("{}", serde_json::to_string_pretty(&t).unwrap());
                            } else {
                                println!("Recorded step for trace: {} (Breaker: {})", t.trace_id, t.circuit_breaker);
                            }
                        }
                        Err(e) => eprintln!("Error recording step: {}", e),
                    }
                }
                "show" => {
                    if args.len() < 4 {
                        eprintln!("Usage: ui-master-engine trace show <trace_id>");
                        return;
                    }
                    let trace_id = &args[3];
                    match trace::get_trace(trace_id) {
                        Ok(t) => {
                            if json_flag {
                                println!("{}", serde_json::to_string_pretty(&t).unwrap());
                            } else {
                                println!("\n📋 Multi-Agent Trace Ledger: {}", t.trace_id);
                                println!("Task            : {}", t.task);
                                println!("Circuit Breaker : {}", t.circuit_breaker);
                                println!("Failures Streak : {}", t.consecutive_failures);
                                println!("Spans Count     : {}", t.spans.len());
                                for s in t.spans {
                                    println!(" • Step {}: [{}] {} -> {} ({}ms)", s.step_number, s.agent, s.status, s.summary, s.latency_ms);
                                }
                            }
                        }
                        Err(e) => eprintln!("Error showing trace: {}", e),
                    }
                }
                _ => eprintln!("Unknown trace action: {}", sub),
            }
        }

        _ => print_help(),
    }
}

fn print_help() {
    println!("{}", BANNER);
    println!("{}", r##"
Usage: ui-master-engine <command> [options]

Rig AI Tools (rig.rs):
  rig list                              Output all 6 registered Rig tools with schemas (JSON)
  rig call <tool_name> '<args_json>'    Invoke a Rig tool directly through the Rig tool interface

Deterministic Quality Gates:
  audit <path> [--json]                 Scan files/directories for anti-slop, a11y, and layout violations
  contrast <fg> <bg> [--json]           Calculate WCAG 2.2 AA/AAA relative luminance and contrast ratio
  crx <dir> [--json]                    Audit Chrome Extension manifest v3, Shadow DOM, and popup bounds
  skills <query> [--json]               Sub-millisecond BM25 keyword search across 421 design skills
  get-skill <slug>                      Fetch cached skill markdown directly from local storage
  trace <init|step|show> [args]         Manage multi-agent observability traces and circuit breaker state
  mcp                                   Start JSON-RPC MCP server over stdio

Examples:
  ui-master-engine rig list
  ui-master-engine rig call ui_contrast '{"fg":"#000000","bg":"#ffffff"}'
  ui-master-engine audit ./src
  ui-master-engine contrast '#0f172a' '#38bdf8'
  ui-master-engine crx ./extension
  ui-master-engine skills 'animation scroll'
"##);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_wcag_contrast_black_white() {
        let fg = contrast::RgbColor::parse("#000000").unwrap();
        let bg = contrast::RgbColor::parse("#ffffff").unwrap();
        let report = contrast::calculate_contrast(&fg, &bg);
        assert_eq!(report.ratio, 21.0);
        assert!(report.passes_aaa_normal);
    }

    #[test]
    fn test_wcag_contrast_insufficient() {
        let fg = contrast::RgbColor::parse("#777777").unwrap();
        let bg = contrast::RgbColor::parse("#888888").unwrap();
        let report = contrast::calculate_contrast(&fg, &bg);
        assert!(!report.passes_aa_normal);
    }

    #[tokio::test]
    async fn test_rig_contrast_execution() {
        let res = rig_tools::execute_rig_tool(
            "ui_contrast",
            r##"{"fg":"#000000","bg":"#ffffff"}"##,
        ).await.unwrap();
        assert_eq!(res["ratio"], 21.0);
    }

    #[tokio::test]
    async fn test_rig_trace_lifecycle() {
        let t = trace::init_trace("Test Task").unwrap();
        let recorded = trace::record_step(&t.trace_id, "ui-master-critic", "SUCCESS", "Passed check", 50, 0.99).unwrap();
        assert_eq!(recorded.spans.len(), 1);
        assert_eq!(recorded.circuit_breaker, "CLOSED");
    }
}
