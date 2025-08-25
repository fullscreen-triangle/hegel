//! Oxygen substrate implementation for paramagnetic oscillatory information processing

use crate::constants;
use crate::error::{ProcessingError, Result};
use serde::{Deserialize, Serialize};

/// Paramagnetic oscillatory information processing substrate
///
/// Represents the physical and computational properties of oxygen molecules
/// that enable biological information processing at room temperature with
/// quantum coherence maintenance.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OxygenSubstrate {
    /// Information processing density (bits/molecule/second)
    pub information_density: f64,

    /// Paramagnetic oscillation frequency (Hz)
    pub oscillation_frequency: f64,

    /// Quantum coherence duration (microseconds)
    pub coherence_duration: f64,

    /// Operating temperature (Kelvin)
    pub temperature: f64,

    /// Temperature coefficient for biological optimization (K⁻¹)
    pub temperature_coefficient: f64,

    /// Paramagnetic enhancement factor
    pub paramagnetic_enhancement: f64,

    /// Molecule concentration (molecules/m³)
    pub molecule_concentration: f64,

    /// Quantum efficiency factor
    pub quantum_efficiency: f64,

    /// Biological compatibility score
    pub biological_compatibility: f64,
}

impl OxygenSubstrate {
    /// Create new oxygen substrate with default biological parameters
    pub fn new() -> Self {
        Self {
            information_density: constants::OXYGEN_INFORMATION_DENSITY,
            oscillation_frequency: constants::OSCILLATION_FREQUENCY,
            coherence_duration: constants::COHERENCE_DURATION,
            temperature: constants::BIOLOGICAL_TEMPERATURE,
            temperature_coefficient: 1.0 / constants::BIOLOGICAL_TEMPERATURE,
            paramagnetic_enhancement: constants::PARAMAGNETIC_ENHANCEMENT,
            molecule_concentration: 2.5e25, // Typical atmospheric O₂ concentration
            quantum_efficiency: 0.95,
            biological_compatibility: 1.0,
        }
    }

    /// Create substrate optimized for specific temperature
    pub fn for_temperature(temperature: f64) -> Result<Self> {
        if !Self::is_valid_biological_temperature(temperature) {
            return Err(ProcessingError::InvalidTemperature { temperature });
        }

        let mut substrate = Self::new();
        substrate.temperature = temperature;
        substrate.temperature_coefficient = 1.0 / temperature;

        // Adjust parameters based on temperature
        substrate.coherence_duration = Self::calculate_temperature_adjusted_coherence(temperature);
        substrate.quantum_efficiency = Self::calculate_temperature_adjusted_efficiency(temperature);
        substrate.biological_compatibility = Self::calculate_biological_compatibility(temperature);

        Ok(substrate)
    }

    /// Calculate total information processing capacity
    pub fn processing_capacity(&self, molecule_count: u64) -> f64 {
        let base_capacity = self.information_density * molecule_count as f64;
        let temperature_factor = self.temperature_adjustment_factor();
        let quantum_factor = self.quantum_efficiency;
        let paramagnetic_factor = self.paramagnetic_enhancement;

        base_capacity * temperature_factor * quantum_factor * paramagnetic_factor
    }

    /// Generate paramagnetic oscillation pattern for given duration
    pub fn oscillation_pattern(&self, time_duration: f64) -> Vec<f64> {
        let mut pattern = Vec::new();
        let sample_rate = self.oscillation_frequency * 2.0; // Nyquist rate
        let total_samples = (time_duration * sample_rate) as usize;

        for i in 0..total_samples {
            let t = i as f64 / sample_rate;

            // Exponential decay due to decoherence
            let decay_factor = (-t / (self.coherence_duration * 1e-6)).exp();

            // Paramagnetic oscillation with biological enhancement
            let phase = 2.0 * std::f64::consts::PI * self.oscillation_frequency * t;
            let amplitude = decay_factor * self.paramagnetic_enhancement;

            // Add biological noise for realistic cellular conditions
            let noise = self.biological_noise(t);

            pattern.push(amplitude * phase.sin() + noise);
        }

        pattern
    }

    /// Validate biological temperature conditions
    pub fn validate_temperature(&self) -> Result<()> {
        if !Self::is_valid_biological_temperature(self.temperature) {
            return Err(ProcessingError::InvalidTemperature {
                temperature: self.temperature,
            });
        }
        Ok(())
    }

    /// Check if temperature is within biological range
    pub fn is_valid_biological_temperature(temperature: f64) -> bool {
        temperature >= constants::MIN_BIOLOGICAL_TEMP
            && temperature <= constants::MAX_BIOLOGICAL_TEMP
    }

    /// Calculate temperature adjustment factor for processing capacity
    fn temperature_adjustment_factor(&self) -> f64 {
        // Biological systems are optimized around 310K (37°C)
        let optimal_temp = constants::BIOLOGICAL_TEMPERATURE;
        let temp_deviation = (self.temperature - optimal_temp).abs();

        // Gaussian temperature response with biological optimum
        let temp_factor = (-temp_deviation * temp_deviation / (2.0 * 10.0 * 10.0)).exp();

        // Ensure minimum efficiency even at temperature extremes
        temp_factor.max(0.1)
    }

    /// Calculate quantum efficiency based on temperature
    fn calculate_temperature_adjusted_efficiency(temperature: f64) -> f64 {
        let optimal_temp = constants::BIOLOGICAL_TEMPERATURE;
        let temp_factor = (-((temperature - optimal_temp) / 20.0).powi(2)).exp();

        // Base quantum efficiency with temperature adjustment
        let base_efficiency = 0.95;
        (base_efficiency * temp_factor).max(0.5)
    }

    /// Calculate coherence duration based on temperature
    fn calculate_temperature_adjusted_coherence(temperature: f64) -> f64 {
        let base_coherence = constants::COHERENCE_DURATION;
        let optimal_temp = constants::BIOLOGICAL_TEMPERATURE;

        // Higher temperatures reduce coherence time
        let temp_factor = optimal_temp / temperature;

        base_coherence * temp_factor.powf(0.5)
    }

    /// Calculate biological compatibility score
    fn calculate_biological_compatibility(temperature: f64) -> f64 {
        if !Self::is_valid_biological_temperature(temperature) {
            return 0.0;
        }

        let optimal_temp = constants::BIOLOGICAL_TEMPERATURE;
        let temp_deviation = (temperature - optimal_temp).abs();

        // Compatibility decreases with temperature deviation
        (1.0 - temp_deviation / 50.0).max(0.1)
    }

    /// Generate biological noise for realistic cellular conditions
    fn biological_noise(&self, time: f64) -> f64 {
        use rand::Rng;
        use rand_distr::{Distribution, Normal};

        // Biological noise is typically low-frequency and follows normal distribution
        let mut rng = rand::thread_rng();
        let normal = Normal::new(0.0, 0.01).unwrap();

        // Time-correlated noise to simulate cellular fluctuations
        let noise_amplitude = normal.sample(&mut rng);
        let correlation_factor = (time * 2.0 * std::f64::consts::PI / 1e-3).sin() * 0.1;

        noise_amplitude + correlation_factor
    }

    /// Calculate molecular oxygen utilization rate
    pub fn oxygen_utilization_rate(&self, processing_load: f64) -> f64 {
        // O₂ utilization scales with processing requirements
        let base_rate = processing_load / self.information_density;
        let efficiency_factor = self.quantum_efficiency;

        base_rate / efficiency_factor
    }

    /// Estimate processing power consumption (biological ATP equivalent)
    pub fn power_consumption(&self, molecule_count: u64) -> f64 {
        let processing_capacity = self.processing_capacity(molecule_count);

        // Biological power consumption: ~1 ATP per 10¹² bits processed
        let atp_per_bit = 1e-12;

        processing_capacity * atp_per_bit
    }

    /// Get substrate health metrics
    pub fn health_metrics(&self) -> SubstrateHealthMetrics {
        SubstrateHealthMetrics {
            temperature_optimal: (self.temperature - constants::BIOLOGICAL_TEMPERATURE).abs() < 5.0,
            quantum_coherence_stable: self.coherence_duration > 100.0,
            paramagnetic_enhancement_active: self.paramagnetic_enhancement > 1.0,
            biological_compatibility_high: self.biological_compatibility > 0.8,
            overall_health: self.calculate_overall_health(),
        }
    }

    /// Calculate overall substrate health score
    fn calculate_overall_health(&self) -> f64 {
        let temp_score = if (self.temperature - constants::BIOLOGICAL_TEMPERATURE).abs() < 5.0 {
            1.0
        } else {
            0.5
        };
        let coherence_score = (self.coherence_duration / constants::COHERENCE_DURATION).min(1.0);
        let efficiency_score = self.quantum_efficiency;
        let compatibility_score = self.biological_compatibility;

        (temp_score + coherence_score + efficiency_score + compatibility_score) / 4.0
    }
}

/// Substrate health monitoring metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubstrateHealthMetrics {
    pub temperature_optimal: bool,
    pub quantum_coherence_stable: bool,
    pub paramagnetic_enhancement_active: bool,
    pub biological_compatibility_high: bool,
    pub overall_health: f64,
}

impl Default for OxygenSubstrate {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_substrate_creation() {
        let substrate = OxygenSubstrate::new();

        assert_eq!(
            substrate.information_density,
            constants::OXYGEN_INFORMATION_DENSITY
        );
        assert_eq!(
            substrate.oscillation_frequency,
            constants::OSCILLATION_FREQUENCY
        );
        assert_eq!(substrate.coherence_duration, constants::COHERENCE_DURATION);
        assert_eq!(substrate.temperature, constants::BIOLOGICAL_TEMPERATURE);
    }

    #[test]
    fn test_temperature_validation() {
        let substrate = OxygenSubstrate::new();
        assert!(substrate.validate_temperature().is_ok());

        let cold_substrate = OxygenSubstrate::for_temperature(200.0);
        assert!(cold_substrate.is_err());

        let hot_substrate = OxygenSubstrate::for_temperature(400.0);
        assert!(hot_substrate.is_err());
    }

    #[test]
    fn test_processing_capacity() {
        let substrate = OxygenSubstrate::new();
        let capacity = substrate.processing_capacity(1000);

        assert!(capacity > 0.0);
        assert_eq!(
            capacity,
            constants::OXYGEN_INFORMATION_DENSITY
                * 1000.0
                * substrate.paramagnetic_enhancement
                * substrate.quantum_efficiency
        );
    }

    #[test]
    fn test_oscillation_pattern_generation() {
        let substrate = OxygenSubstrate::new();
        let pattern = substrate.oscillation_pattern(1e-6); // 1 microsecond

        assert!(!pattern.is_empty());
        assert!(pattern.len() > 1000); // Should have many samples for 1μs at THz frequency
    }

    #[test]
    fn test_health_metrics() {
        let substrate = OxygenSubstrate::new();
        let health = substrate.health_metrics();

        assert!(health.temperature_optimal);
        assert!(health.quantum_coherence_stable);
        assert!(health.paramagnetic_enhancement_active);
        assert!(health.biological_compatibility_high);
        assert!(health.overall_health > 0.8);
    }

    #[test]
    fn test_power_consumption() {
        let substrate = OxygenSubstrate::new();
        let power = substrate.power_consumption(1000);

        assert!(power > 0.0);
    }

    #[test]
    fn test_oxygen_utilization() {
        let substrate = OxygenSubstrate::new();
        let utilization = substrate.oxygen_utilization_rate(1e12); // 1 Tbits processing

        assert!(utilization > 0.0);
    }
}
