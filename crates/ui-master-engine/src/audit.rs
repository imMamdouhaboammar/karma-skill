use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditViolation {
    pub file: String,
    pub line: usize,
    pub rule: String,
    pub severity: String, // "BLOCK" | "FLAG"
    pub message: String,
    pub snippet: String,
    pub fix: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditSummary {
    pub files_scanned: usize,
    pub violations_count: usize,
    pub blocks: usize,
    pub flags: usize,
    pub violations: Vec<AuditViolation>,
}

pub fn scan_path(target: &Path) -> Result<AuditSummary, String> {
    let mut files = Vec::new();
    collect_files(target, &mut files);

    let mut violations = Vec::new();
    for f in &files {
        scan_single_file(f, &mut violations);
    }

    let blocks = violations.iter().filter(|v| v.severity == "BLOCK").count();
    let flags = violations.iter().filter(|v| v.severity == "FLAG").count();

    Ok(AuditSummary {
        files_scanned: files.len(),
        violations_count: violations.len(),
        blocks,
        flags,
        violations,
    })
}

fn collect_files(path: &Path, acc: &mut Vec<PathBuf>) {
    if path.is_file() {
        if is_ui_file(path) {
            acc.push(path.to_path_buf());
        }
        return;
    }

    if let Ok(entries) = fs::read_dir(path) {
        for entry in entries.flatten() {
            let p = entry.path();
            let name = p.file_name().and_then(|n| n.to_str()).unwrap_or("");
            if name.starts_with('.') || name == "node_modules" || name == "target" || name == "dist" {
                continue;
            }
            if p.is_dir() {
                collect_files(&p, acc);
            } else if is_ui_file(&p) {
                acc.push(p);
            }
        }
    }
}

fn is_ui_file(p: &Path) -> bool {
    let ext = p.extension().and_then(|e| e.to_str()).unwrap_or("");
    matches!(ext, "tsx" | "jsx" | "html" | "vue" | "svelte" | "css")
}

fn scan_single_file(path: &Path, violations: &mut Vec<AuditViolation>) {
    let content = match fs::read_to_string(path) {
        Ok(c) => c,
        Err(_) => return,
    };

    let file_str = path.display().to_string();
    let lines: Vec<&str> = content.lines().collect();
    let mut font_sizes_found = HashSet::new();

    let font_size_classes = [
        "text-xs", "text-sm", "text-base", "text-lg", "text-xl",
        "text-2xl", "text-3xl", "text-4xl", "text-5xl", "text-6xl", "text-7xl"
    ];

    for (idx, line) in lines.iter().enumerate() {
        let line_num = idx + 1;
        let line_trimmed = line.trim();

        // Rule 1: Purple-to-pink gradient cliche
        if (line.contains("from-purple-") && (line.contains("to-pink-") || line.contains("to-fuchsia-")))
            || (line.contains("bg-gradient-to-r") && line.contains("purple"))
        {
            violations.push(AuditViolation {
                file: file_str.clone(),
                line: line_num,
                rule: "anti-slop/purple-gradient".into(),
                severity: "BLOCK".into(),
                message: "Generic AI slop: Multicolored purple/pink gradient detected. Avoid unearned AI gradients.".into(),
                snippet: line_trimmed.to_string(),
                fix: "Replace with purposeful solid brand token or subtle monochromatic surface elevation.".into(),
            });
        }

        // Rule 2: h-screen viewport jump
        if line.contains("h-screen") && !line.contains("h-dvh") {
            violations.push(AuditViolation {
                file: file_str.clone(),
                line: line_num,
                rule: "layout/viewport-hscreen".into(),
                severity: "FLAG".into(),
                message: "Viewport unit 'h-screen' causes mobile address bar jumping and scroll bugs.".into(),
                snippet: line_trimmed.to_string(),
                fix: "Use 'h-dvh' (dynamic viewport height) or 'min-h-dvh' instead of 'h-screen'.".into(),
            });
        }

        // Rule 3: Layout property animation
        if (line.contains("animate=") || line.contains("transition:") || line.contains("transition="))
            && (line.contains("width") || line.contains("height") || line.contains("margin") || line.contains("padding"))
        {
            violations.push(AuditViolation {
                file: file_str.clone(),
                line: line_num,
                rule: "motion/layout-thrashing".into(),
                severity: "BLOCK".into(),
                message: "Performance violation: Animating layout geometry (width/height/margin) causes layout thrashing.".into(),
                snippet: line_trimmed.to_string(),
                fix: "Animate compositor properties only: 'transform' (scale/translate) and 'opacity'.".into(),
            });
        }

        // Rule 4: Outline hidden without focus-visible
        if line.contains("outline-none") && !line.contains("focus-visible:") {
            violations.push(AuditViolation {
                file: file_str.clone(),
                line: line_num,
                rule: "a11y/focus-outline".into(),
                severity: "BLOCK".into(),
                message: "Accessibility violation: 'outline-none' removes keyboard focus indicator without replacement.".into(),
                snippet: line_trimmed.to_string(),
                fix: "Add 'focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary'.".into(),
            });
        }

        // Rule 5: Arbitrary non-4px spacing values
        for word in line.split_whitespace() {
            if (word.starts_with("p-[") || word.starts_with("m-[") || word.starts_with("gap-[")) && word.ends_with("px]") {
                let inner = &word[3..word.len()-3];
                if let Ok(px) = inner.parse::<i32>() {
                    if px % 4 != 0 {
                        violations.push(AuditViolation {
                            file: file_str.clone(),
                            line: line_num,
                            rule: "layout/arbitrary-spacing".into(),
                            severity: "FLAG".into(),
                            message: format!("Grid breaking: '{}' does not align with the 4px/8px design scale.", word),
                            snippet: word.to_string(),
                            fix: format!("Use standard Tailwind scale or round to nearest 4px multiple (e.g. {}px).", (px / 4) * 4),
                        });
                    }
                }
            }
        }

        // Rule 6: Track typography sizes
        for sz in font_size_classes {
            if line.contains(sz) {
                font_sizes_found.insert(sz);
            }
        }
    }

    // Check typography scale count
    if font_sizes_found.len() > 4 {
        violations.push(AuditViolation {
            file: file_str,
            line: 1,
            rule: "typography/excess-scale".into(),
            severity: "BLOCK".into(),
            message: format!("Visual chaos: Found {} distinct font sizes in single component ({:?}). Maximum allowed is 4.", font_sizes_found.len(), font_sizes_found),
            snippet: "Multiple font sizes".into(),
            fix: "Consolidate typography to at most 4 steps (e.g. caption: text-xs, body: text-sm, header: text-base, title: text-xl).".into(),
        });
    }
}
