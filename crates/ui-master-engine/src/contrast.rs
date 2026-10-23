use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RgbColor {
    pub r: u8,
    pub g: u8,
    pub b: u8,
    pub a: f32,
    pub hex: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContrastReport {
    pub fg: RgbColor,
    pub bg: RgbColor,
    pub ratio: f64,
    pub formatted_ratio: String,
    pub passes_aa_normal: bool,
    pub passes_aa_large: bool,
    pub passes_aaa_normal: bool,
    pub passes_aaa_large: bool,
    pub passes_ui_component: bool,
    pub recommendation: String,
}

impl RgbColor {
    pub fn parse(input: &str) -> Result<Self, String> {
        let trimmed = input.trim();
        if trimmed.starts_with('#') {
            Self::from_hex(trimmed)
        } else if trimmed.starts_with("rgb") {
            Self::from_rgb_fn(trimmed)
        } else {
            Self::from_hex(&format!("#{}", trimmed))
        }
    }

    pub fn from_hex(hex: &str) -> Result<Self, String> {
        let cleaned = hex.trim_start_matches('#');
        match cleaned.len() {
            3 => {
                let r = u8::from_str_radix(&cleaned[0..1].repeat(2), 16).map_err(|e| e.to_string())?;
                let g = u8::from_str_radix(&cleaned[1..2].repeat(2), 16).map_err(|e| e.to_string())?;
                let b = u8::from_str_radix(&cleaned[2..3].repeat(2), 16).map_err(|e| e.to_string())?;
                Ok(Self { r, g, b, a: 1.0, hex: format!("#{:02x}{:02x}{:02x}", r, g, b) })
            }
            6 => {
                let r = u8::from_str_radix(&cleaned[0..2], 16).map_err(|e| e.to_string())?;
                let g = u8::from_str_radix(&cleaned[2..4], 16).map_err(|e| e.to_string())?;
                let b = u8::from_str_radix(&cleaned[4..6], 16).map_err(|e| e.to_string())?;
                Ok(Self { r, g, b, a: 1.0, hex: format!("#{:02x}{:02x}{:02x}", r, g, b) })
            }
            8 => {
                let r = u8::from_str_radix(&cleaned[0..2], 16).map_err(|e| e.to_string())?;
                let g = u8::from_str_radix(&cleaned[2..4], 16).map_err(|e| e.to_string())?;
                let b = u8::from_str_radix(&cleaned[4..6], 16).map_err(|e| e.to_string())?;
                let a_raw = u8::from_str_radix(&cleaned[6..8], 16).map_err(|e| e.to_string())?;
                let a = (a_raw as f32) / 255.0;
                Ok(Self { r, g, b, a, hex: format!("#{:02x}{:02x}{:02x}", r, g, b) })
            }
            _ => Err(format!("Invalid hex color: {}", hex)),
        }
    }

    fn from_rgb_fn(s: &str) -> Result<Self, String> {
        let inside = s.split('(').nth(1).and_then(|x| x.split(')').next()).ok_or("Malformed rgb string")?;
        let parts: Vec<&str> = inside.split(',').map(|x| x.trim()).collect();
        if parts.len() < 3 {
            return Err("RGB requires at least 3 components".into());
        }
        let r = parts[0].parse::<u8>().map_err(|e| e.to_string())?;
        let g = parts[1].parse::<u8>().map_err(|e| e.to_string())?;
        let b = parts[2].parse::<u8>().map_err(|e| e.to_string())?;
        let a = if parts.len() >= 4 {
            parts[3].parse::<f32>().unwrap_or(1.0)
        } else {
            1.0
        };
        Ok(Self { r, g, b, a, hex: format!("#{:02x}{:02x}{:02x}", r, g, b) })
    }

    pub fn relative_luminance(&self) -> f64 {
        let rs = (self.r as f64) / 255.0;
        let gs = (self.g as f64) / 255.0;
        let bs = (self.b as f64) / 255.0;

        let r_lin = if rs <= 0.04045 { rs / 12.92 } else { ((rs + 0.055) / 1.055).powf(2.4) };
        let g_lin = if gs <= 0.04045 { gs / 12.92 } else { ((gs + 0.055) / 1.055).powf(2.4) };
        let b_lin = if bs <= 0.04045 { bs / 12.92 } else { ((bs + 0.055) / 1.055).powf(2.4) };

        0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    }
}

pub fn calculate_contrast(fg: &RgbColor, bg: &RgbColor) -> ContrastReport {
    let l1 = fg.relative_luminance();
    let l2 = bg.relative_luminance();

    let (lighter, darker) = if l1 > l2 { (l1, l2) } else { (l2, l1) };
    let ratio = (lighter + 0.05) / (darker + 0.05);

    let passes_aa_normal = ratio >= 4.5;
    let passes_aa_large = ratio >= 3.0;
    let passes_aaa_normal = ratio >= 7.0;
    let passes_aaa_large = ratio >= 4.5;
    let passes_ui_component = ratio >= 3.0;

    let recommendation = if passes_aaa_normal {
        "Superb contrast (WCAG AAA compliant). Ideal for critical body text, labels, and small copy.".to_string()
    } else if passes_aa_normal {
        "Complies with WCAG AA standard for normal text (>= 4.5:1). Safe for general production use.".to_string()
    } else if passes_aa_large {
        "Passes for Large Text (>= 18pt or >= 14pt bold) and UI components only. FAIL for normal body text (<4.5:1).".to_string()
    } else {
        "FAILS WCAG AA! Insufficient contrast. Increase lightness difference between foreground and background.".to_string()
    };

    ContrastReport {
        fg: fg.clone(),
        bg: bg.clone(),
        ratio: (ratio * 100.0).round() / 100.0,
        formatted_ratio: format!("{:.2}:1", ratio),
        passes_aa_normal,
        passes_aa_large,
        passes_aaa_normal,
        passes_aaa_large,
        passes_ui_component,
        recommendation,
    }
}
