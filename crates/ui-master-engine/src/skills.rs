use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegistrySkill {
    pub slug: String,
    pub name: Option<String>,
    pub topics: Option<Vec<String>>,
    pub description: Option<String>,
    #[serde(rename = "pathSlug")]
    pub path_slug: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SkillSearchHit {
    pub slug: String,
    pub name: String,
    pub topics: Vec<String>,
    pub description: String,
    pub score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct RegistryFile {
    pub registry: Vec<RegistrySkill>,
}

pub fn search_skills(query: &str, limit: usize) -> Result<Vec<SkillSearchHit>, String> {
    let reg_path = get_registry_path();
    if !reg_path.exists() {
        return Err(format!("registry.json not found at {}. Run 'ui-skills' first to populate catalog.", reg_path.display()));
    }

    let data = fs::read_to_string(&reg_path).map_err(|e| e.to_string())?;
    let parsed: RegistryFile = serde_json::from_str(&data).map_err(|e| e.to_string())?;

    let q_tokens: Vec<String> = query.to_lowercase().split_whitespace().map(|s| s.to_string()).collect();
    if q_tokens.is_empty() {
        return Ok(Vec::new());
    }

    let mut hits = Vec::new();

    for skill in parsed.registry {
        let slug = skill.slug.to_lowercase();
        let name = skill.name.clone().unwrap_or_default().to_lowercase();
        let desc = skill.description.clone().unwrap_or_default().to_lowercase();
        let topics = skill.topics.clone().unwrap_or_default();
        let topics_str = topics.join(" ").to_lowercase();

        let mut score = 0.0;
        for token in &q_tokens {
            if slug == *token {
                score += 25.0;
            } else if slug.contains(token) {
                score += 10.0;
            }

            if name.contains(token) {
                score += 8.0;
            }

            if topics_str.contains(token) {
                score += 5.0;
            }

            if desc.contains(token) {
                score += 2.0;
            }
        }

        if score > 0.0 {
            hits.push(SkillSearchHit {
                slug: skill.slug,
                name: skill.name.unwrap_or_default(),
                topics,
                description: skill.description.unwrap_or_default(),
                score,
            });
        }
    }

    hits.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    if hits.len() > limit {
        hits.truncate(limit);
    }

    Ok(hits)
}

pub fn get_skill_content(slug: &str) -> Result<String, String> {
    let base = get_skills_cache_dir();
    let direct_path = base.join(format!("{}.md", slug));
    if direct_path.exists() {
        return fs::read_to_string(&direct_path).map_err(|e| e.to_string());
    }

    // Try finding by path_slug or prefix
    if let Ok(entries) = fs::read_dir(&base) {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if name.ends_with(".md") && (name.contains(slug) || slug.contains(name.trim_end_matches(".md"))) {
                return fs::read_to_string(entry.path()).map_err(|e| e.to_string());
            }
        }
    }

    Err(format!("Skill '{}' not found in local cache at {}", slug, base.display()))
}

fn get_registry_path() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".into());
    Path::new(&home).join(".gemini/antigravity/ui-skills-catalog/registry.json")
}

fn get_skills_cache_dir() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".into());
    Path::new(&home).join(".gemini/antigravity/ui-skills-catalog/skills")
}
