use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrxFinding {
    pub category: String, // "MANIFEST" | "ISOLATION" | "POPUP" | "SECURITY"
    pub severity: String, // "BLOCK" | "FLAG" | "PASS"
    pub message: String,
    pub recommendation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrxAuditReport {
    pub is_manifest_v3: bool,
    pub has_shadow_dom_isolation: bool,
    pub popup_dimensions_valid: bool,
    pub findings: Vec<CrxFinding>,
    pub overall_status: String, // "PASS" | "NEEDS_FIXES"
}

pub fn audit_crx(dir: &Path) -> Result<CrxAuditReport, String> {
    let mut findings = Vec::new();
    let mut is_mv3 = false;
    let mut shadow_dom_verified = true;
    let mut popup_dimensions_valid = true;

    let manifest_path = dir.join("manifest.json");
    if !manifest_path.exists() {
        return Err(format!("manifest.json not found in {}", dir.display()));
    }

    let manifest_raw = fs::read_to_string(&manifest_path).map_err(|e| e.to_string())?;
    let manifest: serde_json::Value = serde_json::from_str(&manifest_raw)
        .map_err(|e| format!("Failed to parse manifest.json: {}", e))?;

    // Check manifest version
    if let Some(mv) = manifest.get("manifest_version").and_then(|v| v.as_i64()) {
        if mv == 3 {
            is_mv3 = true;
            findings.push(CrxFinding {
                category: "MANIFEST".into(),
                severity: "PASS".into(),
                message: "Manifest Version 3 (MV3) confirmed.".into(),
                recommendation: "Keep using MV3 standards for Chrome Web Store compliance.".into(),
            });
        } else {
            findings.push(CrxFinding {
                category: "MANIFEST".into(),
                severity: "BLOCK".into(),
                message: format!("Deprecated manifest_version: {}. Chrome extensions require Manifest V3.", mv),
                recommendation: "Upgrade manifest to manifest_version: 3.".into(),
            });
        }
    } else {
        findings.push(CrxFinding {
            category: "MANIFEST".into(),
            severity: "BLOCK".into(),
            message: "Missing 'manifest_version' in manifest.json.".into(),
            recommendation: "Add 'manifest_version': 3 to manifest.json.".into(),
        });
    }

    // Check CSP
    if let Some(csp) = manifest.get("content_security_policy") {
        let csp_str = csp.to_string();
        if csp_str.contains("unsafe-eval") {
            findings.push(CrxFinding {
                category: "SECURITY".into(),
                severity: "BLOCK".into(),
                message: "Manifest V3 violation: 'unsafe-eval' detected in Content Security Policy.".into(),
                recommendation: "Remove unsafe-eval. Use pure ahead-of-time compiled templates or sandbox pages.".into(),
            });
        }
        if csp_str.contains("http://") {
            findings.push(CrxFinding {
                category: "SECURITY".into(),
                severity: "BLOCK".into(),
                message: "Security violation: Insecure http:// origin declared in CSP.".into(),
                recommendation: "All remote resource endpoints must use secure https:// or be bundled locally.".into(),
            });
        }
    }

    // Check permissions least-privilege
    if let Some(perms) = manifest.get("permissions").and_then(|p| p.as_array()) {
        for p in perms {
            if let Some(perm_str) = p.as_str() {
                if perm_str == "<all_urls>" {
                    findings.push(CrxFinding {
                        category: "SECURITY".into(),
                        severity: "FLAG".into(),
                        message: "Overly broad permission: '<all_urls>' triggers harsh Chrome Web Store review.".into(),
                        recommendation: "Scope permissions to 'activeTab' or specific required host patterns.".into(),
                    });
                }
            }
        }
    }

    // Check Content Scripts for Shadow DOM isolation
    let mut scanned_scripts = 0;
    scan_scripts_for_shadow_dom(dir, &mut scanned_scripts, &mut shadow_dom_verified, &mut findings);

    // Check popup dimensions if present
    if let Some(popup_path_val) = manifest
        .get("action")
        .and_then(|a| a.get("default_popup"))
        .and_then(|p| p.as_str())
    {
        let popup_file = dir.join(popup_path_val);
        if popup_file.exists() {
            if let Ok(content) = fs::read_to_string(&popup_file) {
                if content.contains("width:") || content.contains("w-[") {
                    // check if popup tries to exceed 800px width or 600px height
                    if content.contains("800px") || content.contains("w-[900px]") || content.contains("w-[1000px]") {
                        popup_dimensions_valid = false;
                        findings.push(CrxFinding {
                            category: "POPUP".into(),
                            severity: "BLOCK".into(),
                            message: "Chrome extension popups are physically clamped by browser to max 800x600px.".into(),
                            recommendation: "Design popup viewport within 380-420px width and 480-560px height.".into(),
                        });
                    }
                }
            }
        }
    }

    let has_blocks = findings.iter().any(|f| f.severity == "BLOCK");
    let overall_status = if has_blocks { "NEEDS_FIXES" } else { "PASS" }.to_string();

    Ok(CrxAuditReport {
        is_manifest_v3: is_mv3,
        has_shadow_dom_isolation: shadow_dom_verified,
        popup_dimensions_valid,
        findings,
        overall_status,
    })
}

fn scan_scripts_for_shadow_dom(
    dir: &Path,
    scanned_count: &mut usize,
    shadow_dom_ok: &mut bool,
    findings: &mut Vec<CrxFinding>,
) {
    if let Ok(entries) = fs::read_dir(dir) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_dir() {
                let name = p.file_name().and_then(|n| n.to_str()).unwrap_or("");
                if name != "node_modules" && name != "dist" && !name.starts_with('.') {
                    scan_scripts_for_shadow_dom(&p, scanned_count, shadow_dom_ok, findings);
                }
            } else {
                let ext = p.extension().and_then(|e| e.to_str()).unwrap_or("");
                if matches!(ext, "js" | "ts" | "tsx" | "jsx") {
                    let file_name = p.file_name().and_then(|n| n.to_str()).unwrap_or("");
                    if file_name.contains("content") || file_name.contains("inject") {
                        *scanned_count += 1;
                        if let Ok(code) = fs::read_to_string(&p) {
                            let creates_ui = code.contains("createElement") || code.contains("innerHTML") || code.contains("render(");
                            let uses_shadow = code.contains("attachShadow") || code.contains("shadowRoot");

                            if creates_ui && !uses_shadow {
                                *shadow_dom_ok = false;
                                findings.push(CrxFinding {
                                    category: "ISOLATION".into(),
                                    severity: "BLOCK".into(),
                                    message: format!("Content script '{}' injects UI into DOM without Shadow DOM encapsulation.", file_name),
                                    recommendation: "Mount all injected overlays inside a Closed Shadow Root: 'const shadow = host.attachShadow({ mode: \"closed\" });' to prevent CSS collision with host web pages.".into(),
                                });
                            }
                        }
                    }
                }
            }
        }
    }
}
