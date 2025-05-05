import React, { useEffect, useRef, useState } from "react";
import Script from "next/script";

/**
 * MoleculeViewer component for 3D visualization of molecular structures
 * Uses 3Dmol.js for interactive rendering
 */
export default function MoleculeViewer({ moleculeData, viewerOptions }) {
  const viewerRef = useRef(null);
  const containerRef = useRef(null);
  const [viewer, setViewer] = useState(null);
  const [isScriptLoaded, setIsScriptLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Default options for the viewer
  const defaultOptions = {
    backgroundColor: "white",
    width: 500,
    height: 400,
    style: "stick",
    colorScheme: "chainHetatm",
    rotatable: true,
    zoomable: true,
    showLabels: false
  };
  
  // Merge default options with provided options
  const options = { ...defaultOptions, ...viewerOptions };

  // Handle initialization once 3Dmol script is loaded
  useEffect(() => {
    if (!isScriptLoaded || !viewerRef.current || !moleculeData) return;
    
    setIsLoading(true);
    
    try {
      // Clean up previous viewer instance if exists
      if (viewer) {
        viewer.removeAllModels();
        viewer.removeAllSurfaces();
        viewer.removeAllLabels();
        viewer.clear();
      }
      
      // Create viewer instance
      const v = $3Dmol.createViewer(viewerRef.current, {
        backgroundColor: options.backgroundColor,
        defaultcolors: $3Dmol.rasmolElementColors
      });
      
      setViewer(v);
      
      // Load the molecule data
      loadMolecule(v, moleculeData, options);
      
      // Adjust container size - important for proper sizing
      if (containerRef.current) {
        containerRef.current.style.width = `${options.width}px`;
        containerRef.current.style.height = `${options.height}px`;
      }
    } catch (err) {
      console.error("Error initializing 3D molecule viewer:", err);
      setError("Failed to initialize 3D viewer");
    }
    
    return () => {
      // Clean up viewer on unmount
      if (viewer) {
        try {
          viewer.removeAllModels();
          viewer.clear();
        } catch (err) {
          console.error("Error cleaning up 3D viewer:", err);
        }
      }
    };
  }, [isScriptLoaded, moleculeData, options.backgroundColor]);
  
  // Load the molecule data into the viewer
  const loadMolecule = (v, data, opts) => {
    setIsLoading(true);
    setError(null);
    
    try {
      if (!data) {
        setIsLoading(false);
        return;
      }
      
      // Determine the source and format of the molecule data
      let source, format;
      
      if (data.pdbData) {
        source = data.pdbData;
        format = "pdb";
      } else if (data.sdfData) {
        source = data.sdfData;
        format = "sdf";
      } else if (data.molData) {
        source = data.molData;
        format = "mol";
      } else if (data.pdbUrl) {
        // For external URLs, we'll load asynchronously
        v.clear();
        $3Dmol.download(data.pdbUrl, v, {}, function() {
          applyStyles(v, opts);
          v.zoomTo();
          v.render();
          setIsLoading(false);
        });
        return;
      } else if (data.smiles) {
        // Convert SMILES to 3D using 3Dmol.js built-in functionality
        let smilesObj = {
          smiles: data.smiles,
          options: { removeHs: false }
        };
        
        v.clear();
        v.addModel(JSON.stringify(smilesObj), "csmiles");
        applyStyles(v, opts);
        v.zoomTo();
        v.render();
        setIsLoading(false);
        return;
      } else {
        // No recognized data format
        setError("Unsupported molecule data format");
        setIsLoading(false);
        return;
      }
      
      // Add the model to the viewer
      v.clear();
      v.addModel(source, format);
      applyStyles(v, opts);
      v.zoomTo();
      v.render();
      setIsLoading(false);
    } catch (err) {
      console.error("Error loading molecule:", err);
      setError("Failed to load molecule data");
      setIsLoading(false);
    }
  };
  
  // Apply visual styles to the molecule
  const applyStyles = (v, opts) => {
    // Apply the specified style
    switch (opts.style) {
      case "stick":
        v.setStyle({}, { stick: {} });
        break;
      case "line":
        v.setStyle({}, { line: {} });
        break;
      case "cross":
        v.setStyle({}, { cross: { lineWidth: 2 } });
        break;
      case "sphere":
        v.setStyle({}, { sphere: { radius: 0.8 } });
        break;
      case "cartoon":
        v.setStyle({}, { cartoon: { color: opts.colorScheme } });
        break;
      case "ball_and_stick":
        v.setStyle({}, { 
          stick: { radius: 0.15 },
          sphere: { radius: 0.35 }
        });
        break;
      default:
        // Default to stick representation
        v.setStyle({}, { stick: {} });
    }
    
    // Apply color scheme if specified
    if (opts.colorScheme) {
      switch (opts.colorScheme) {
        case "chainHetatm":
          v.setStyle({chain: "A"}, {cartoon: {color: "spectrum"}});
          v.setStyle({chain: "B"}, {cartoon: {color: "chain"}});
          v.setStyle({chain: "C"}, {cartoon: {color: "chain"}});
          v.setStyle({chain: "D"}, {cartoon: {color: "chain"}});
          v.setStyle({hetflag: true}, {stick: {colorscheme: "greenCarbon", radius: 0.15}});
          break;
        case "spectrum":
          v.setStyle({}, {cartoon: {color: "spectrum"}});
          break;
        case "element":
          // Color by element (default for stick/sphere)
          break;
        case "residue":
          v.setStyle({}, {cartoon: {colorfunc: $3Dmol.getColorByResidue()}});
          break;
        default:
          // Use default coloring
      }
    }
    
    // Add surface if requested
    if (opts.surface) {
      v.addSurface($3Dmol.SurfaceType.MS, {
        opacity: 0.85,
        colorscheme: opts.surfaceColor || {gradient: 'rwb', min: -10, max: 10}
      });
    }
    
    // Add labels if requested
    if (opts.showLabels) {
      // Add atom labels, typically for small molecules
      v.addStyle({}, {label: {
        fontSize: 12,
        fontColor: 'black',
        showBackground: false
      }});
    }
  };
  
  // Handle script loading
  const handleScriptLoad = () => {
    setIsScriptLoaded(true);
  };

  return (
    <>
      {/* Load 3Dmol.js from CDN */}
      <Script 
        src="https://3Dmol.org/build/3Dmol-min.js" 
        onLoad={handleScriptLoad}
        strategy="beforeInteractive"
      />
      <Script 
        src="https://3Dmol.org/build/3Dmol.ui-min.js" 
        strategy="beforeInteractive"
      />
      
      <div className="molecule_viewer_container" ref={containerRef}>
        {isLoading && (
          <div className="molecule_viewer_loading">
            <div className="loading_spinner"></div>
            <span>Loading molecule...</span>
          </div>
        )}
        
        {error && (
          <div className="molecule_viewer_error">
            <span>{error}</span>
          </div>
        )}
        
        <div 
          ref={viewerRef} 
          className="molecule_viewer"
          style={{ 
            width: options.width, 
            height: options.height,
            position: "relative",
            overflow: "hidden",
            border: "1px solid #ddd",
            borderRadius: "4px"
          }}
        ></div>
        
        {moleculeData && moleculeData.description && (
          <div className="molecule_description">
            <h4>Description</h4>
            <p>{moleculeData.description}</p>
          </div>
        )}
        
        {isScriptLoaded && moleculeData && (
          <div className="molecule_viewer_controls">
            <div className="control_group">
              <button 
                onClick={() => {
                  if (viewer) {
                    viewer.setStyle({}, { stick: {} });
                    viewer.render();
                  }
                }}
                className="view_control_btn"
              >
                Stick
              </button>
              <button 
                onClick={() => {
                  if (viewer) {
                    viewer.setStyle({}, { 
                      stick: { radius: 0.15 },
                      sphere: { radius: 0.35 }
                    });
                    viewer.render();
                  }
                }}
                className="view_control_btn"
              >
                Ball & Stick
              </button>
              <button 
                onClick={() => {
                  if (viewer) {
                    viewer.setStyle({}, { sphere: {} });
                    viewer.render();
                  }
                }}
                className="view_control_btn"
              >
                Sphere
              </button>
              <button 
                onClick={() => {
                  if (viewer) {
                    viewer.setStyle({}, { cartoon: {} });
                    viewer.render();
                  }
                }}
                className="view_control_btn"
              >
                Cartoon
              </button>
            </div>
            
            <div className="control_group">
              <button 
                onClick={() => {
                  if (viewer) {
                    viewer.rotate(20, {x: 1, y: 0, z: 0});
                    viewer.render();
                  }
                }}
                className="view_control_btn"
              >
                Rotate X
              </button>
              <button 
                onClick={() => {
                  if (viewer) {
                    viewer.rotate(20, {x: 0, y: 1, z: 0});
                    viewer.render();
                  }
                }}
                className="view_control_btn"
              >
                Rotate Y
              </button>
              <button 
                onClick={() => {
                  if (viewer) {
                    viewer.zoomTo();
                    viewer.render();
                  }
                }}
                className="view_control_btn"
              >
                Reset View
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
} 