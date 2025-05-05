import React from "react";
import GenomicsDashboard from "../genome/genomics-dashboard";
import MassSpecDashboard from "../spectra/mass-spec-dashboard";
import EvidenceRectifier from "./EvidenceRectifier";

const MolecularData = ({ ActiveIndex }) => {
  return (
    <div className={ActiveIndex === 4 ? "cavani_tm_section active" : "cavani_tm_section"} id="molecular_data">
      <div className="section_inner">
        <div className="cavani_tm_service">
          <div className="cavani_tm_title">
            <span>Molecular Data</span>
          </div>
          
          <div className="service_list">
            <div className="molecular-data-container">
              <p className="data-description">
                Explore experimental results from our genomics and mass spectrometry analyses.
                The Hegel framework rectifies evidence by integrating data from multiple sources
                using a high-performance Rust engine guided by metacognitive AI.
              </p>
              
              <EvidenceRectifier />
              
              <div className="section-divider"></div>
              
              <GenomicsDashboard />
              
              <div className="section-divider"></div>
              
              <MassSpecDashboard />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MolecularData; 