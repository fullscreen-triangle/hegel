import React, { useState, useEffect } from "react";

const MassSpecDashboard = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [imagesLoaded, setImagesLoaded] = useState(false);
  const [spectraData, setSpectraData] = useState({
    images: [],
    results: null
  });

  useEffect(() => {
    // In a real implementation, we would fetch the actual image list from an API
    // For now, we'll use a simulated list of images
    const fetchSpectraData = async () => {
      try {
        setLoading(true);
        
        // Simulated data - in a real implementation, this would be fetched from an API
        const imageList = [
          "/public/mass_spec/output/images/spectrum_database/spectrum_1.png",
          "/public/mass_spec/output/images/spectrum_database/spectrum_2.png",
          "/public/mass_spec/output/images/spectrum_database/spectrum_3.png",
          "/public/mass_spec/output/images/spectrum_database/spectrum_4.png"
        ];
        
        setSpectraData({
          images: imageList,
          results: {
            total_compounds: 127,
            identified_compounds: 98,
            unknown_compounds: 29,
            confidence_level: "high",
            processing_time: "5m 32s"
          }
        });
        
        setImagesLoaded(true);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching mass spec data:", error);
        setLoading(false);
      }
    };

    fetchSpectraData();
  }, []);

  if (loading) {
    return (
      <div className="cavani_tm_section" id="massspec">
        <div className="section_inner">
          <div className="cavani_tm_service">
            <div className="cavani_tm_title">
              <span>Mass Spectrometry</span>
            </div>
            <div className="service_list">
              <div className="loading">Loading mass spectrometry data...</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cavani_tm_section" id="massspec">
      <div className="section_inner">
        <div className="cavani_tm_service">
          <div className="cavani_tm_title">
            <span>Mass Spectrometry</span>
          </div>
          
          <div className="service_list">
            <div className="tabs">
              <div className="tab-buttons">
                <button 
                  className={activeTab === "overview" ? "active" : ""}
                  onClick={() => setActiveTab("overview")}
                >
                  Overview
                </button>
                <button 
                  className={activeTab === "visualizations" ? "active" : ""}
                  onClick={() => setActiveTab("visualizations")}
                >
                  Spectra Visualizations
                </button>
                <button 
                  className={activeTab === "analysis" ? "active" : ""}
                  onClick={() => setActiveTab("analysis")}
                >
                  Analysis Results
                </button>
              </div>
              
              <div className="tab-content">
                {activeTab === "overview" && (
                  <div className="overview-content">
                    <div className="metrics-summary">
                      <div className="metric-card">
                        <h3>Total Compounds</h3>
                        <div className="metric-value">{spectraData.results.total_compounds}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Identified</h3>
                        <div className="metric-value">{spectraData.results.identified_compounds}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Unknown</h3>
                        <div className="metric-value">{spectraData.results.unknown_compounds}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Confidence</h3>
                        <div className="metric-value">{spectraData.results.confidence_level}</div>
                      </div>
                      <div className="metric-card">
                        <h3>Processing Time</h3>
                        <div className="metric-value">{spectraData.results.processing_time}</div>
                      </div>
                    </div>
                    
                    <div className="overview-image">
                      <div className="video-container">
                        <video width="100%" controls>
                          <source src="/public/mass_spec/output/images/analysis_video.mp4" type="video/mp4" />
                          Your browser does not support the video tag.
                        </video>
                      </div>
                    </div>
                  </div>
                )}
                
                {activeTab === "visualizations" && imagesLoaded && (
                  <div className="visualizations-content">
                    <div className="spectra-grid">
                      {spectraData.images.map((image, index) => (
                        <div key={index} className="spectra-image">
                          <div className="image-container">
                            <img src={image} alt={`Spectrum ${index + 1}`} />
                          </div>
                          <div className="image-caption">Spectrum {index + 1}</div>
                        </div>
                      ))}
                    </div>
                    <div className="viewer-container">
                      <h3>Spectrum Viewer</h3>
                      <p>Select a spectrum above to view detailed data.</p>
                      {/* In a real implementation, this would be replaced with an interactive spectrum viewer component */}
                      <div className="spectrum-viewer-placeholder">
                        <div className="placeholder-text">Interactive Spectrum Viewer</div>
                      </div>
                    </div>
                  </div>
                )}
                
                {activeTab === "analysis" && (
                  <div className="analysis-content">
                    <div className="analysis-section">
                      <h3>Compound Identification Summary</h3>
                      <div className="compound-table">
                        <table>
                          <thead>
                            <tr>
                              <th>Category</th>
                              <th>Count</th>
                              <th>Percentage</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td>Identified Compounds</td>
                              <td>{spectraData.results.identified_compounds}</td>
                              <td>{Math.round((spectraData.results.identified_compounds / spectraData.results.total_compounds) * 100)}%</td>
                            </tr>
                            <tr>
                              <td>Unknown Compounds</td>
                              <td>{spectraData.results.unknown_compounds}</td>
                              <td>{Math.round((spectraData.results.unknown_compounds / spectraData.results.total_compounds) * 100)}%</td>
                            </tr>
                            <tr>
                              <td>Total</td>
                              <td>{spectraData.results.total_compounds}</td>
                              <td>100%</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                    
                    <div className="analysis-section">
                      <h3>Analysis Results</h3>
                      <p>The analysis was processed with a confidence level of <strong>{spectraData.results.confidence_level}</strong> and took <strong>{spectraData.results.processing_time}</strong> to complete.</p>
                      <p>Detailed results can be found in the full report available for download.</p>
                      
                      <div className="download-button">
                        <button className="btn-main">Download Full Report</button>
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

export default MassSpecDashboard; 