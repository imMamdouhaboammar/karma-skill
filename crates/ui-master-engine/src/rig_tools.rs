use crate::audit::{self, AuditSummary};
use crate::contrast::{self, ContrastReport, RgbColor};
use crate::crx::{self, CrxAuditReport};
use crate::skills::{self, SkillSearchHit};
use crate::trace::{self, TraceSession};

use rig_core::tool::{Tool, ToolContext};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, thiserror::Error)]
pub enum UiToolError {
    #[error("Color parse error: {0}")]
    ColorParse(String),
    #[error("Audit error: {0}")]
    Audit(String),
    #[error("CRX audit error: {0}")]
    Crx(String),
    #[error("Skill search error: {0}")]
    SkillSearch(String),
    #[error("Skill get error: {0}")]
    SkillGet(String),
    #[error("Trace error: {0}")]
    Trace(String),
}

// 1. RigContrastTool
#[derive(Deserialize, Serialize)]
pub struct ContrastArgs {
    pub fg: String,
    pub bg: String,
}

pub struct RigContrastTool;

impl Tool for RigContrastTool {
    const NAME: &'static str = "ui_contrast";
    type Error = UiToolError;
    type Args = ContrastArgs;
    type Output = ContrastReport;

    fn description(&self) -> String {
        "Calculates exact WCAG 2.2 color contrast ratio and verifies AA/AAA compliance.".into()
    }

    fn parameters(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "fg": { "type": "string", "description": "Foreground color in hex (#fff, #0f172a) or rgb(r, g, b)" },
                "bg": { "type": "string", "description": "Background color in hex (#fff, #0f172a) or rgb(r, g, b)" }
            },
            "required": ["fg", "bg"]
        })
    }

    async fn call(&self, _ctx: &mut ToolContext, args: Self::Args) -> Result<Self::Output, Self::Error> {
        let fg = RgbColor::parse(&args.fg).map_err(UiToolError::ColorParse)?;
        let bg = RgbColor::parse(&args.bg).map_err(UiToolError::ColorParse)?;
        Ok(contrast::calculate_contrast(&fg, &bg))
    }
}

// 2. RigAntiSlopLinterTool
#[derive(Deserialize, Serialize)]
pub struct LinterArgs {
    pub path: String,
}

pub struct RigAntiSlopLinterTool;

impl Tool for RigAntiSlopLinterTool {
    const NAME: &'static str = "ui_anti_slop_lint";
    type Error = UiToolError;
    type Args = LinterArgs;
    type Output = AuditSummary;

    fn description(&self) -> String {
        "Scans UI files for anti-slop violations, h-screen bugs, layout thrashing, and typography bloat.".into()
    }

    fn parameters(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "path": { "type": "string", "description": "Path to file or directory to scan" }
            },
            "required": ["path"]
        })
    }

    async fn call(&self, _ctx: &mut ToolContext, args: Self::Args) -> Result<Self::Output, Self::Error> {
        audit::scan_path(Path::new(&args.path)).map_err(UiToolError::Audit)
    }
}

// 3. RigCrxAuditTool
#[derive(Deserialize, Serialize)]
pub struct CrxArgs {
    pub dir: String,
}

pub struct RigCrxAuditTool;

impl Tool for RigCrxAuditTool {
    const NAME: &'static str = "ui_crx_audit";
    type Error = UiToolError;
    type Args = CrxArgs;
    type Output = CrxAuditReport;

    fn description(&self) -> String {
        "Audits Chrome Extensions for Manifest V3, Closed Shadow DOM encapsulation, and popup geometry.".into()
    }

    fn parameters(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "dir": { "type": "string", "description": "Directory containing manifest.json" }
            },
            "required": ["dir"]
        })
    }

    async fn call(&self, _ctx: &mut ToolContext, args: Self::Args) -> Result<Self::Output, Self::Error> {
        crx::audit_crx(Path::new(&args.dir)).map_err(UiToolError::Crx)
    }
}

// 4. RigSkillSearchTool
#[derive(Deserialize, Serialize)]
pub struct SkillSearchArgs {
    pub query: String,
    pub limit: Option<usize>,
}

pub struct RigSkillSearchTool;

impl Tool for RigSkillSearchTool {
    const NAME: &'static str = "ui_skill_search";
    type Error = UiToolError;
    type Args = SkillSearchArgs;
    type Output = Vec<SkillSearchHit>;

    fn description(&self) -> String {
        "Sub-millisecond BM25 search across 421 design engineering skills in ui-skills.".into()
    }

    fn parameters(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "query": { "type": "string", "description": "Search keyword or topic" },
                "limit": { "type": "number", "description": "Maximum hits to return (default 10)" }
            },
            "required": ["query"]
        })
    }

    async fn call(&self, _ctx: &mut ToolContext, args: Self::Args) -> Result<Self::Output, Self::Error> {
        let limit = args.limit.unwrap_or(10);
        skills::search_skills(&args.query, limit).map_err(UiToolError::SkillSearch)
    }
}

// 5. RigSkillGetTool
#[derive(Deserialize, Serialize)]
pub struct SkillGetArgs {
    pub slug: String,
}

#[derive(Serialize)]
pub struct SkillGetOutput {
    pub slug: String,
    pub content: String,
}

pub struct RigSkillGetTool;

impl Tool for RigSkillGetTool {
    const NAME: &'static str = "ui_skill_get";
    type Error = UiToolError;
    type Args = SkillGetArgs;
    type Output = SkillGetOutput;

    fn description(&self) -> String {
        "Fetches full markdown guidance for any design skill by slug from local catalog.".into()
    }

    fn parameters(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "slug": { "type": "string", "description": "Skill slug (e.g. baseline-ui, fixing-accessibility)" }
            },
            "required": ["slug"]
        })
    }

    async fn call(&self, _ctx: &mut ToolContext, args: Self::Args) -> Result<Self::Output, Self::Error> {
        let content = skills::get_skill_content(&args.slug).map_err(UiToolError::SkillGet)?;
        Ok(SkillGetOutput {
            slug: args.slug,
            content,
        })
    }
}

// 6. RigTraceTool
#[derive(Deserialize, Serialize)]
pub struct TraceStepArgs {
    pub trace_id: String,
    pub agent: String,
    pub status: String,
    pub summary: String,
}

pub struct RigTraceTool;

impl Tool for RigTraceTool {
    const NAME: &'static str = "ui_multi_agent_trace";
    type Error = UiToolError;
    type Args = TraceStepArgs;
    type Output = TraceSession;

    fn description(&self) -> String {
        "Records a subagent span in the multi-agent task ledger and monitors the circuit breaker.".into()
    }

    fn parameters(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "trace_id": { "type": "string", "description": "The current multi-agent trace identifier" },
                "agent": { "type": "string", "description": "Subagent name (e.g. ui-master-critic, ui-master-motion)" },
                "status": { "type": "string", "description": "Outcome status: SUCCESS, FAILURE, or DEGRADED" },
                "summary": { "type": "string", "description": "Short explanation of findings and actions" }
            },
            "required": ["trace_id", "agent", "status", "summary"]
        })
    }

    async fn call(&self, _ctx: &mut ToolContext, args: Self::Args) -> Result<Self::Output, Self::Error> {
        trace::record_step(&args.trace_id, &args.agent, &args.status, &args.summary, 120, 0.95)
            .map_err(UiToolError::Trace)
    }
}

// Convenience runner to invoke Rig tools by name
pub async fn execute_rig_tool(name: &str, raw_args: &str) -> Result<serde_json::Value, String> {
    let mut ctx = ToolContext::default();

    match name {
        RigContrastTool::NAME => {
            let args: ContrastArgs = serde_json::from_str(raw_args).map_err(|e| format!("Invalid args: {}", e))?;
            let res = RigContrastTool.call(&mut ctx, args).await.map_err(|e| e.to_string())?;
            serde_json::to_value(res).map_err(|e| e.to_string())
        }
        RigAntiSlopLinterTool::NAME => {
            let args: LinterArgs = serde_json::from_str(raw_args).map_err(|e| format!("Invalid args: {}", e))?;
            let res = RigAntiSlopLinterTool.call(&mut ctx, args).await.map_err(|e| e.to_string())?;
            serde_json::to_value(res).map_err(|e| e.to_string())
        }
        RigCrxAuditTool::NAME => {
            let args: CrxArgs = serde_json::from_str(raw_args).map_err(|e| format!("Invalid args: {}", e))?;
            let res = RigCrxAuditTool.call(&mut ctx, args).await.map_err(|e| e.to_string())?;
            serde_json::to_value(res).map_err(|e| e.to_string())
        }
        RigSkillSearchTool::NAME => {
            let args: SkillSearchArgs = serde_json::from_str(raw_args).map_err(|e| format!("Invalid args: {}", e))?;
            let res = RigSkillSearchTool.call(&mut ctx, args).await.map_err(|e| e.to_string())?;
            serde_json::to_value(res).map_err(|e| e.to_string())
        }
        RigSkillGetTool::NAME => {
            let args: SkillGetArgs = serde_json::from_str(raw_args).map_err(|e| format!("Invalid args: {}", e))?;
            let res = RigSkillGetTool.call(&mut ctx, args).await.map_err(|e| e.to_string())?;
            serde_json::to_value(res).map_err(|e| e.to_string())
        }
        RigTraceTool::NAME => {
            let args: TraceStepArgs = serde_json::from_str(raw_args).map_err(|e| format!("Invalid args: {}", e))?;
            let res = RigTraceTool.call(&mut ctx, args).await.map_err(|e| e.to_string())?;
            serde_json::to_value(res).map_err(|e| e.to_string())
        }
        _ => Err(format!("Unknown Rig tool: '{}'. Available tools: ui_contrast, ui_anti_slop_lint, ui_crx_audit, ui_skill_search, ui_skill_get, ui_multi_agent_trace", name)),
    }
}

pub fn list_rig_tools_manifest() -> serde_json::Value {
    serde_json::json!([
        {
            "name": RigContrastTool::NAME,
            "description": RigContrastTool.description(),
            "inputSchema": RigContrastTool.parameters(),
            "parameters": RigContrastTool.parameters()
        },
        {
            "name": RigAntiSlopLinterTool::NAME,
            "description": RigAntiSlopLinterTool.description(),
            "inputSchema": RigAntiSlopLinterTool.parameters(),
            "parameters": RigAntiSlopLinterTool.parameters()
        },
        {
            "name": RigCrxAuditTool::NAME,
            "description": RigCrxAuditTool.description(),
            "inputSchema": RigCrxAuditTool.parameters(),
            "parameters": RigCrxAuditTool.parameters()
        },
        {
            "name": RigSkillSearchTool::NAME,
            "description": RigSkillSearchTool.description(),
            "inputSchema": RigSkillSearchTool.parameters(),
            "parameters": RigSkillSearchTool.parameters()
        },
        {
            "name": RigSkillGetTool::NAME,
            "description": RigSkillGetTool.description(),
            "inputSchema": RigSkillGetTool.parameters(),
            "parameters": RigSkillGetTool.parameters()
        },
        {
            "name": RigTraceTool::NAME,
            "description": RigTraceTool.description(),
            "inputSchema": RigTraceTool.parameters(),
            "parameters": RigTraceTool.parameters()
        }
    ])
}
