import React, { useState, useEffect } from "react";

const GenomicsDashboard = () => {
  const [genomicsData, setGenomicsData] = useState(null);
  const [activeTab, setActiveTab] = useState("genomics");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch the latest genomics results
    const fetchGenomicsData = async () => {
      try {
        setLoading(true);
        const response = await fetch('/public/genomics/results/complete_results_20250314_040714.json');
        const data = await response.json();
        setGenomicsData(data);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching genomics data:", error);
        setLoading(false);
      }
    };

    fetchGenomicsData();
  }, []);

  if (loading) {
    return (
      <div className="cavani_tm_section" id="genomics">
        <div className="section_inner">
          <div className="cavani_tm_service">
            <div className="cavani_tm_title">
              <span>Genomics Analysis</span>
            </div>
            <div className="service_list">
              <div className="loading">Loading genomics data...</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cavani_tm_section" id="genomics">
      <div className="section_inner">
        <div className="cavani_tm_service">
          <div className="cavani_tm_title">
            <span>Genomics Analysis</span>
          </div>
          
          <div className="service_list">
            <div className="tabs">
              <div className="tab-buttons">
                <button 
                  className={activeTab === "genomics" ? "active" : ""}
                  onClick={() => setActiveTab("genomics")}
                >
                  Genome Scoring
                </button>
                <button 
                  className={activeTab === "network" ? "active" : ""}
                  onClick={() => setActiveTab("network")}
                >
                  Network Analysis
                </button>
                <button 
                  className={activeTab === "deficiency" ? "active" : ""}
                  onClick={() => setActiveTab("deficiency")}
                >
                  Deficiency Analysis
                </button>
                <button 
                  className={activeTab === "drugs" ? "active" : ""}
                  onClick={() => setActiveTab("drugs")}
                >
                  Drug Interactions
                </button>
              </div>
              
              <div className="tab-content">
                {activeTab === "genomics" && genomicsData && (
                  <div className="genomics-content">
                    <div className="metrics-summary">
                      <div className="metric-card">
                        <h3>Total Score</h3>
                        <div className="metric-value">{genomicsData.genome_scoring.total_score}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Variants Analyzed</h3>
                        <div className="metric-value">{genomicsData.genome_scoring.summary.variants_analyzed}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Variants Found</h3>
                        <div className="metric-value">{genomicsData.genome_scoring.summary.variants_found}</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {activeTab === "network" && genomicsData && (
                  <div className="network-content">
                    <div className="metrics-summary">
                      <div className="metric-card">
                        <h3>Nodes</h3>
                        <div className="metric-value">{genomicsData.network_analysis.summary.num_nodes}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Edges</h3>
                        <div className="metric-value">{genomicsData.network_analysis.summary.num_edges}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Communities</h3>
                        <div className="metric-value">{genomicsData.network_analysis.summary.num_communities}</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {activeTab === "deficiency" && genomicsData && (
                  <div className="deficiency-content">
                    <div className="metrics-summary">
                      <div className="metric-card">
                        <h3>Total Deficiencies</h3>
                        <div className="metric-value">{genomicsData.deficiency_analysis.summary.total_deficiencies}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Affected Pathways</h3>
                        <div className="metric-value">{genomicsData.deficiency_analysis.summary.affected_pathways}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Network Nodes</h3>
                        <div className="metric-value">{genomicsData.deficiency_analysis.summary.network_nodes}</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {activeTab === "drugs" && genomicsData && (
                  <div className="drugs-content">
                    <div className="metrics-summary">
                      <div className="metric-card">
                        <h3>Total Drug Variants</h3>
                        <div className="metric-value">{genomicsData.drug_interaction_analysis.summary.total_drug_variants}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Affected Drugs</h3>
                        <div className="metric-value">{genomicsData.drug_interaction_analysis.summary.affected_drugs}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Network Nodes</h3>
                        <div className="metric-value">{genomicsData.drug_interaction_analysis.summary.network_nodes}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenomicsDashboard; 