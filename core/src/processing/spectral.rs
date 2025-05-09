// Spectral analysis module for processing mass spectrometry data

use crate::HegelError;
use std::collections::HashMap;

/// Calculate similarity between two spectral data points
pub fn calculate_spectral_similarity(
    spectral_data: &str,
    reference_data: &str,
) -> Result<f64, HegelError> {
    // Parse spectral data
    let experimental_peaks = parse_spectral_data(spectral_data)
        .map_err(|e| HegelError::ComputationError(format!("Error parsing experimental data: {}", e)))?;
    
    let reference_peaks = parse_spectral_data(reference_data)
        .map_err(|e| HegelError::ComputationError(format!("Error parsing reference data: {}", e)))?;
    
    // Calculate cosine similarity between spectra
    let similarity = calculate_cosine_similarity(&experimental_peaks, &reference_peaks);
    
    Ok(similarity)
}

/// Parse spectral data in m/z,intensity format
fn parse_spectral_data(data: &str) -> Result<HashMap<f64, f64>, String> {
    let mut peaks = HashMap::new();
    
    for line in data.lines() {
        if line.trim().is_empty() || line.starts_with('#') {
            continue;
        }
        
        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() != 2 {
            return Err(format!("Invalid format in line: {}", line));
        }
        
        let mz = parts[0].trim().parse::<f64>()
            .map_err(|e| format!("Invalid m/z value: {}", e))?;
        
        let intensity = parts[1].trim().parse::<f64>()
            .map_err(|e| format!("Invalid intensity value: {}", e))?;
        
        peaks.insert(mz, intensity);
    }
    
    Ok(peaks)
}

/// Calculate cosine similarity between two spectra
fn calculate_cosine_similarity(
    spectrum1: &HashMap<f64, f64>,
    spectrum2: &HashMap<f64, f64>,
) -> f64 {
    let mut dot_product = 0.0;
    let mut norm1 = 0.0;
    let mut norm2 = 0.0;
    
    // Calculate dot product and norms
    for (mz, intensity) in spectrum1 {
        norm1 += intensity * intensity;
        
        // Find matching peak in spectrum2 within a tolerance
        if let Some(matched_intensity) = find_matching_peak(spectrum2, *mz, 0.1) {
            dot_product += intensity * matched_intensity;
        }
    }
    
    // Calculate norm for spectrum2
    for (_, intensity) in spectrum2 {
        norm2 += intensity * intensity;
    }
    
    // Calculate cosine similarity
    if norm1 > 0.0 && norm2 > 0.0 {
        dot_product / (norm1.sqrt() * norm2.sqrt())
    } else {
        0.0
    }
}

/// Find a matching peak within a tolerance in the spectrum
fn find_matching_peak(
    spectrum: &HashMap<f64, f64>,
    target_mz: f64,
    tolerance: f64,
) -> Option<f64> {
    for (mz, intensity) in spectrum {
        if (mz - target_mz).abs() <= tolerance {
            return Some(*intensity);
        }
    }
    
    None
}

/// Process a mass spectrum to identify significant peaks
pub fn identify_significant_peaks(
    spectrum: &HashMap<f64, f64>,
    threshold_percentage: f64,
) -> Vec<(f64, f64)> {
    if spectrum.is_empty() {
        return Vec::new();
    }
    
    // Find maximum intensity
    let max_intensity = spectrum.values().cloned().fold(0.0, f64::max);
    let threshold = max_intensity * threshold_percentage;
    
    // Extract significant peaks
    spectrum
        .iter()
        .filter(|(_, &intensity)| intensity >= threshold)
        .map(|(&mz, &intensity)| (mz, intensity))
        .collect()
}

/// De-noise a spectrum by removing low intensity peaks
pub fn denoise_spectrum(
    spectrum: &HashMap<f64, f64>,
    noise_threshold: f64,
) -> HashMap<f64, f64> {
    spectrum
        .iter()
        .filter(|(_, &intensity)| intensity > noise_threshold)
        .map(|(&mz, &intensity)| (mz, intensity))
        .collect()
} 