use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSpan {
    pub span_id: String,
    pub agent: String,
    pub step_number: usize,
    pub status: String, // "SUCCESS" | "FAILURE" | "DEGRADED"
    pub latency_ms: u64,
    pub summary: String,
    pub confidence: f32,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceSession {
    pub trace_id: String,
    pub task: String,
    pub circuit_breaker: String, // "CLOSED" | "OPEN" | "HALF-OPEN"
    pub consecutive_failures: usize,
    pub created_at: String,
    pub updated_at: String,
    pub spans: Vec<AgentSpan>,
}

pub fn init_trace(task: &str) -> Result<TraceSession, String> {
    let now = current_time_millis();
    let trace_id = format!("trace-ui-{}", now);
    let session = TraceSession {
        trace_id: trace_id.clone(),
        task: task.to_string(),
        circuit_breaker: "CLOSED".into(),
        consecutive_failures: 0,
        created_at: iso_timestamp(),
        updated_at: iso_timestamp(),
        spans: Vec::new(),
    };

    save_session(&session)?;
    Ok(session)
}

pub fn record_step(
    trace_id: &str,
    agent: &str,
    status: &str,
    summary: &str,
    latency_ms: u64,
    confidence: f32,
) -> Result<TraceSession, String> {
    let mut session = match load_session(trace_id) {
        Ok(s) => s,
        Err(_) => {
            let s = TraceSession {
                trace_id: trace_id.to_string(),
                task: format!("Auto-initialized session for trace '{}'", trace_id),
                circuit_breaker: "CLOSED".into(),
                consecutive_failures: 0,
                created_at: iso_timestamp(),
                updated_at: iso_timestamp(),
                spans: Vec::new(),
            };
            save_session(&s)?;
            s
        }
    };

    let step_num = session.spans.len() + 1;
    let span_id = format!("{}-step-{}", trace_id, step_num);

    let is_failure = status.to_uppercase() == "FAILURE";
    if is_failure {
        session.consecutive_failures += 1;
        if session.consecutive_failures >= 2 {
            session.circuit_breaker = "OPEN".into();
        }
    } else {
        session.consecutive_failures = 0;
        if session.circuit_breaker == "HALF-OPEN" {
            session.circuit_breaker = "CLOSED".into();
        }
    }

    session.spans.push(AgentSpan {
        span_id,
        agent: agent.to_string(),
        step_number: step_num,
        status: status.to_uppercase(),
        latency_ms,
        summary: summary.to_string(),
        confidence,
        timestamp: iso_timestamp(),
    });

    session.updated_at = iso_timestamp();
    save_session(&session)?;
    Ok(session)
}

pub fn get_trace(trace_id: &str) -> Result<TraceSession, String> {
    load_session(trace_id)
}

fn get_traces_dir() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".into());
    let dir = Path::new(&home).join(".gemini/antigravity/traces");
    if !dir.exists() {
        let _ = fs::create_dir_all(&dir);
    }
    dir
}

fn save_session(session: &TraceSession) -> Result<(), String> {
    let file = get_traces_dir().join(format!("{}.json", session.trace_id));
    let data = serde_json::to_string_pretty(session).map_err(|e| e.to_string())?;
    fs::write(&file, data).map_err(|e| e.to_string())
}

fn load_session(trace_id: &str) -> Result<TraceSession, String> {
    let file = get_traces_dir().join(format!("{}.json", trace_id));
    if !file.exists() {
        return Err(format!("Trace '{}' not found at {}", trace_id, file.display()));
    }
    let data = fs::read_to_string(&file).map_err(|e| e.to_string())?;
    serde_json::from_str(&data).map_err(|e| e.to_string())
}

fn current_time_millis() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
}

fn iso_timestamp() -> String {
    let now = current_time_millis();
    let secs = (now / 1000) as u64;
    format!("T+{}s", secs % 86400)
}
