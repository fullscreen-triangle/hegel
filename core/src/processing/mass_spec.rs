//! Mass Spectrometry Processing Module
//! 
//! This module handles the processing and analysis of mass spectrometry data
//! for molecular identification and evidence generation.

use anyhow::{Result, Context, anyhow};
use log::{info, debug, warn, error};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use ndarray::Array1;

/// Initialize the mass spectrometry processing module
pub fn initialize() -> Result<()> {
    info!("Initializing mass spectrometry processing module");
    info!("Mass spectrometry module initialized successfully");
    Ok(())
}

/// Mass spectrometry data types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum MassSpecType {
    /// LC-MS/MS data
    LCMSMS,
    
    /// GC-MS data
    GCMS,
    
    /// MALDI-TOF data
    MALDITOF,
    
    /// Direct infusion MS
    DirectInfusion,
    
    /// Ion mobility MS
    IonMobility,
    
    /// Custom or other MS type
    Other,
}

/// Mass spectrometry data for analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MassSpecData {
    /// Type of mass spectrometry data
    pub ms_type: MassSpecType,
    
    /// Experiment ID or name
    pub experiment_id: String,
    
    /// Sample ID or name
    pub sample_id: String,
    
    /// Raw data content
    pub data: MassSpecContent,
    
    /// Metadata and additional properties
    pub metadata: HashMap<String, serde_json::Value>,
}

/// Mass spectrometry data content
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "format", content = "content")]
pub enum MassSpecContent {
    /// Peak list data
    Peaks {
        /// m/z values
        mz_values: Vec<f64>,
        
        /// Intensity values
        intensities: Vec<f64>,
        
        /// Retention times (optional)
        retention_times: Option<Vec<f64>>,
    },
    
    /// MS/MS spectrum data
    MSMS {
        /// Precursor m/z
        precursor_mz: f64,
        
        /// Precursor charge
        precursor_charge: i32,
        
        /// Fragment m/z values
        fragment_mz: Vec<f64>,
        
        /// Fragment intensities
        fragment_intensities: Vec<f64>,
    },
    
    /// Chromatogram data
    Chromatogram {
        /// Retention times
        retention_times: Vec<f64>,
        
        /// Intensities
        intensities: Vec<f64>,
        
        /// m/z channel (if extracted ion chromatogram)
        mz_channel: Option<f64>,
    },
    
    /// Other format data
    Other {
        /// Format description
        format_description: String,
        
        /// Raw data as JSON
        data: serde_json::Value,
    },
}

/// Mass spectrometry processing result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MassSpecResult {
    /// Molecule ID the result relates to
    pub molecule_id: String,
    
    /// Evidence type
    pub evidence_type: String,
    
    /// Confidence score (0.0 - 1.0)
    pub confidence: f64,
    
    /// Specific findings
    pub findings: Vec<MassSpecFinding>,
    
    /// Processing metadata
    pub processing_metadata: HashMap<String, serde_json::Value>,
}

/// Finding from mass spectrometry analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MassSpecFinding {
    /// Type of finding
    pub finding_type: String,
    
    /// Description of the finding
    pub description: String,
    
    /// Score or value
    pub score: f64,
    
    /// Additional details
    pub details: serde_json::Value,
}

/// Options for mass spectrometry data processing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MassSpecProcessingOptions {
    /// Mass tolerance in Da or ppm
    pub mass_tolerance: f64,
    
    /// Whether mass tolerance is in ppm (true) or Da (false)
    pub mass_tolerance_in_ppm: bool,
    
    /// Minimum intensity threshold
    pub min_intensity: f64,
    
    /// Signal-to-noise ratio threshold
    pub snr_threshold: f64,
    
    /// Retention time tolerance in minutes
    pub rt_tolerance: f64,
}

impl Default for MassSpecProcessingOptions {
    fn default() -> Self {
        Self {
            mass_tolerance: 10.0,
            mass_tolerance_in_ppm: true,
            min_intensity: 1000.0,
            snr_threshold: 3.0,
            rt_tolerance: 0.5,
        }
    }
}

/// Mass spectrometry data processor
pub struct MassSpecProcessor {
    /// Processing options
    options: MassSpecProcessingOptions,
}

impl MassSpecProcessor {
    /// Create a new processor with default options
    pub fn new() -> Self {
        Self {
            options: MassSpecProcessingOptions::default(),
        }
    }
    
    /// Create a new processor with the given options
    pub fn with_options(options: MassSpecProcessingOptions) -> Self {
        Self { options }
    }
    
    /// Process mass spectrometry data for a molecule
    pub fn process(&self, molecule_id: &str, data: &MassSpecData) -> Result<Vec<MassSpecResult>> {
        debug!("Processing mass spec data for molecule {}: {}", molecule_id, data.experiment_id);
        
        match &data.data {
            MassSpecContent::Peaks { mz_values, intensities, retention_times } => {
                self.process_peaks(molecule_id, mz_values, intensities, retention_times.as_ref(), &data.metadata)
            },
            MassSpecContent::MSMS { precursor_mz, precursor_charge, fragment_mz, fragment_intensities } => {
                self.process_msms(molecule_id, *precursor_mz, *precursor_charge, 
                                  fragment_mz, fragment_intensities, &data.metadata)
            },
            MassSpecContent::Chromatogram { retention_times, intensities, mz_channel } => {
                self.process_chromatogram(molecule_id, retention_times, intensities, *mz_channel, &data.metadata)
            },
            MassSpecContent::Other { format_description, data } => {
                warn!("Processing custom mass spec data format: {}", format_description);
                Err(anyhow!("Custom mass spec data format not supported: {}", format_description))
            },
        }
    }
    
    /// Process peak list data
    fn process_peaks(
        &self,
        molecule_id: &str,
        mz_values: &[f64],
        intensities: &[f64],
        retention_times: Option<&Vec<f64>>,
        metadata: &HashMap<String, serde_json::Value>,
    ) -> Result<Vec<MassSpecResult>> {
        debug!("Processing mass spec peak data with {} peaks", mz_values.len());
        
        if mz_values.len() != intensities.len() {
            return Err(anyhow!("Mismatch between m/z values and intensities"));
        }
        
        // Filter peaks by intensity threshold
        let significant_peaks: Vec<(usize, &f64, &f64)> = mz_values.iter().zip(intensities.iter())
            .enumerate()
            .filter(|(_, (_, &intensity))| intensity >= self.options.min_intensity)
            .collect();
        
        debug!("Found {} significant peaks above intensity threshold", significant_peaks.len());
        
        // Calculate noise level as the median of the lower half of intensities
        let mut sorted_intensities = intensities.to_vec();
        sorted_intensities.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let noise_level = if sorted_intensities.is_empty() {
            0.0
        } else {
            sorted_intensities[sorted_intensities.len() / 4]
        };
        
        // Filter by signal-to-noise ratio
        let high_snr_peaks: Vec<(usize, &f64, &f64)> = significant_peaks.into_iter()
            .filter(|(_, _, &intensity)| intensity / noise_level >= self.options.snr_threshold)
            .collect();
        
        debug!("Found {} peaks with high SNR", high_snr_peaks.len());
        
        // Create findings for each high SNR peak
        let findings = high_snr_peaks.iter()
            .map(|&(idx, &mz, &intensity)| {
                // Calculate score based on intensity
                let max_intensity = intensities.iter().fold(0.0, |max, &i| max.max(i));
                let normalized_intensity = intensity / max_intensity;
                
                // If we have retention time, include it
                let rt_info = if let Some(rts) = retention_times {
                    if idx < rts.len() {
                        format!(", RT: {:.2} min", rts[idx])
                    } else {
                        String::new()
                    }
                } else {
                    String::new()
                };
                
                MassSpecFinding {
                    finding_type: "peak".to_string(),
                    description: format!("Found significant peak at m/z {:.4}{}, intensity: {:.0e}", 
                                         mz, rt_info, intensity),
                    score: normalized_intensity,
                    details: serde_json::json!({
                        "mz": mz,
                        "intensity": intensity,
                        "retention_time": retention_times.and_then(|rts| rts.get(idx).copied()),
                        "snr": intensity / noise_level,
                    }),
                }
            })
            .collect::<Vec<_>>();
        
        // Calculate overall confidence based on peak count and intensities
        let confidence = if findings.is_empty() {
            0.0
        } else {
            // Weighted average of scores with a boost for having more peaks
            let peak_count_factor = (findings.len() as f64).min(10.0) / 10.0;
            let avg_score = findings.iter().map(|f| f.score).sum::<f64>() / findings.len() as f64;
            (0.7 * avg_score + 0.3 * peak_count_factor).min(1.0)
        };
        
        // Create the result
        let result = MassSpecResult {
            molecule_id: molecule_id.to_string(),
            evidence_type: "ms_peaks".to_string(),
            confidence,
            findings,
            processing_metadata: metadata.clone(),
        };
        
        Ok(vec![result])
    }
    
    /// Process MS/MS data
    fn process_msms(
        &self,
        molecule_id: &str,
        precursor_mz: f64,
        precursor_charge: i32,
        fragment_mz: &[f64],
        fragment_intensities: &[f64],
        metadata: &HashMap<String, serde_json::Value>,
    ) -> Result<Vec<MassSpecResult>> {
        debug!("Processing MS/MS spectrum with precursor m/z {}", precursor_mz);
        
        if fragment_mz.len() != fragment_intensities.len() {
            return Err(anyhow!("Mismatch between fragment m/z values and intensities"));
        }
        
        // Filter fragments by intensity threshold
        let significant_fragments: Vec<(usize, &f64, &f64)> = fragment_mz.iter().zip(fragment_intensities.iter())
            .enumerate()
            .filter(|(_, (_, &intensity))| intensity >= self.options.min_intensity)
            .collect();
        
        debug!("Found {} significant fragments", significant_fragments.len());
        
        // Create findings for the precursor and top N fragments
        let mut findings = Vec::new();
        
        // Add precursor finding
        findings.push(MassSpecFinding {
            finding_type: "precursor".to_string(),
            description: format!("Precursor ion at m/z {:.4} with charge {}", precursor_mz, precursor_charge),
            score: 1.0, // Highest confidence for precursor
            details: serde_json::json!({
                "mz": precursor_mz,
                "charge": precursor_charge,
                "mass": (precursor_mz - 1.007825) * precursor_charge as f64,
            }),
        });
        
        // Sort fragments by intensity and get top 10
        let mut sorted_fragments = significant_fragments;
        sorted_fragments.sort_by(|(_, _, a), (_, _, b)| 
            b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
        
        let top_fragments = sorted_fragments.iter()
            .take(10)
            .collect::<Vec<_>>();
        
        // Add top fragment findings
        for (i, &&(idx, &mz, &intensity)) in top_fragments.iter().enumerate() {
            // Normalize intensity
            let max_intensity = fragment_intensities.iter().fold(0.0, |max, &i| max.max(i));
            let normalized_intensity = intensity / max_intensity;
            
            findings.push(MassSpecFinding {
                finding_type: "fragment".to_string(),
                description: format!("Fragment ion #{} at m/z {:.4}, intensity: {:.0e}", 
                                    i+1, mz, intensity),
                score: normalized_intensity,
                details: serde_json::json!({
                    "rank": i+1,
                    "mz": mz,
                    "intensity": intensity,
                    "relative_intensity": normalized_intensity,
                }),
            });
        }
        
        // Calculate overall confidence based on having good fragments
        let confidence = if top_fragments.is_empty() {
            0.2 // Low confidence with just precursor
        } else {
            // Higher confidence with more fragments
            let fragment_count_factor = (top_fragments.len() as f64).min(10.0) / 10.0;
            (0.3 + 0.7 * fragment_count_factor).min(1.0)
        };
        
        // Create the result
        let result = MassSpecResult {
            molecule_id: molecule_id.to_string(),
            evidence_type: "ms_msms".to_string(),
            confidence,
            findings,
            processing_metadata: metadata.clone(),
        };
        
        Ok(vec![result])
    }
    
    /// Process chromatogram data
    fn process_chromatogram(
        &self,
        molecule_id: &str,
        retention_times: &[f64],
        intensities: &[f64],
        mz_channel: Option<f64>,
        metadata: &HashMap<String, serde_json::Value>,
    ) -> Result<Vec<MassSpecResult>> {
        debug!("Processing chromatogram data with {} points", retention_times.len());
        
        if retention_times.len() != intensities.len() {
            return Err(anyhow!("Mismatch between retention times and intensities"));
        }
        
        // Find chromatographic peaks (simple algorithm - local maxima)
        let chrom_peaks = self.find_chromatographic_peaks(retention_times, intensities)?;
        debug!("Found {} chromatographic peaks", chrom_peaks.len());
        
        // Create findings for each chromatographic peak
        let findings = chrom_peaks.iter()
            .map(|&(idx, height, area, fwhm)| {
                // Normalize score based on peak height and width
                let max_intensity = intensities.iter().fold(0.0, |max, &i| max.max(i));
                let normalized_height = height / max_intensity;
                
                // Peak quality score combines height, area and width
                let quality_score = normalized_height * 0.7 + (area / 1_000_000.0).min(1.0) * 0.2 
                                    + (fwhm / 0.5).min(1.0) * 0.1;
                
                MassSpecFinding {
                    finding_type: "chromatographic_peak".to_string(),
                    description: format!("Chromatographic peak at RT {:.2} min, height: {:.0e}, area: {:.0e}", 
                                        retention_times[idx], height, area),
                    score: quality_score.min(1.0),
                    details: serde_json::json!({
                        "retention_time": retention_times[idx],
                        "height": height,
                        "area": area,
                        "fwhm": fwhm,
                        "mz_channel": mz_channel,
                    }),
                }
            })
            .collect::<Vec<_>>();
        
        // Calculate overall confidence based on chromatographic peak quality
        let confidence = if findings.is_empty() {
            0.0
        } else {
            // Weight by best peak quality
            let best_score = findings.iter().map(|f| f.score).fold(0.0, f64::max);
            best_score.min(1.0)
        };
        
        // Create the result
        let result = MassSpecResult {
            molecule_id: molecule_id.to_string(),
            evidence_type: "ms_chromatogram".to_string(),
            confidence,
            findings,
            processing_metadata: metadata.clone(),
        };
        
        Ok(vec![result])
    }
    
    /// Find chromatographic peaks in the data
    /// Returns vec of (peak_index, height, area, fwhm)
    fn find_chromatographic_peaks(&self, times: &[f64], intensities: &[f64]) -> Result<Vec<(usize, f64, f64, f64)>> {
        if times.is_empty() || intensities.is_empty() {
            return Ok(Vec::new());
        }
        
        let mut peaks = Vec::new();
        
        // Simple algorithm to find local maxima
        for i in 1..intensities.len()-1 {
            if intensities[i] > intensities[i-1] && intensities[i] > intensities[i+1] && 
               intensities[i] >= self.options.min_intensity {
                
                // Found a local maximum
                let peak_index = i;
                let peak_height = intensities[i];
                
                // Estimate peak width (FWHM)
                let half_height = peak_height / 2.0;
                
                // Find left boundary (first point below half height)
                let mut left_idx = i;
                while left_idx > 0 && intensities[left_idx] > half_height {
                    left_idx -= 1;
                }
                
                // Find right boundary (first point below half height)
                let mut right_idx = i;
                while right_idx < intensities.len() - 1 && intensities[right_idx] > half_height {
                    right_idx += 1;
                }
                
                // Calculate FWHM in time units
                let fwhm = times[right_idx] - times[left_idx];
                
                // Estimate peak area by trapezoidal rule
                let mut area = 0.0;
                for j in left_idx..right_idx {
                    let dt = times[j+1] - times[j];
                    area += dt * (intensities[j] + intensities[j+1]) / 2.0;
                }
                
                peaks.push((peak_index, peak_height, area, fwhm));
            }
        }
        
        Ok(peaks)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_find_chromatographic_peaks() {
        let processor = MassSpecProcessor::new();
        
        // Simple test case with a gaussian peak
        let times = vec![0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0];
        let intensities = vec![1000.0, 2000.0, 5000.0, 12000.0, 20000.0, 12000.0, 5000.0, 2000.0, 1000.0, 500.0, 500.0];
        
        let peaks = processor.find_chromatographic_peaks(&times, &intensities).unwrap();
        
        // Should find one peak at index 4 (time 4.0)
        assert_eq!(peaks.len(), 1);
        assert_eq!(peaks[0].0, 4);
        assert_eq!(peaks[0].1, 20000.0); // height
    }
} 