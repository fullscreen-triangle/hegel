import React, { useEffect, useState, useRef, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html, useHelper } from '@react-three/drei';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Atom colors based on standard CPK coloring
const ATOM_COLORS = {
  H: '#FFFFFF', // White
  C: '#909090', // Gray
  N: '#3050F8', // Blue
  O: '#FF0D0D', // Red
  P: '#FF8000', // Orange
  S: '#FFFF30', // Yellow
  Cl: '#1FF01F', // Green
  Na: '#0000FF', // Blue
  K: '#0000FF',  // Blue
  Fe: '#FF5500', // Orange-red
  Mg: '#00FF00', // Green
  Ca: '#00FF00', // Green
  DEFAULT: '#DDDDDD' // Default color
};

// Relative atomic radii
const ATOM_RADII = {
  H: 0.25,
  C: 0.4,
  N: 0.38,
  O: 0.35,
  P: 0.42,
  S: 0.43,
  Cl: 0.45,
  Na: 0.6,
  K: 0.7,
  Fe: 0.5,
  Mg: 0.5,
  Ca: 0.6,
  DEFAULT: 0.4
};

// Atom component
const Atom = ({ position, element, radius, showLabel }) => {
  const color = ATOM_COLORS[element] || ATOM_COLORS.DEFAULT;
  
  return (
    <mesh position={position}>
      <sphereGeometry args={[radius, 32, 32]} />
      <meshStandardMaterial color={color} />
      {showLabel && (
        <Html distanceFactor={10} position={[0, radius + 0.1, 0]}>
          <div style={{ 
            color: '#000000', 
            fontSize: '0.8em', 
            backgroundColor: 'rgba(255,255,255,0.7)',
            padding: '2px 4px',
            borderRadius: '2px',
            userSelect: 'none'
          }}>
            {element}
          </div>
        </Html>
      )}
    </mesh>
  );
};

// Bond component
const Bond = ({ start, end }) => {
  // Calculate bond properties
  const mid = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2, (start[2] + end[2]) / 2];
  const length = Math.sqrt(
    Math.pow(end[0] - start[0], 2) + 
    Math.pow(end[1] - start[1], 2) + 
    Math.pow(end[2] - start[2], 2)
  );
  
  // Calculate rotation to align cylinder with bond
  const direction = [end[0] - start[0], end[1] - start[1], end[2] - start[2]];
  const normalizedDirection = [
    direction[0] / length, 
    direction[1] / length, 
    direction[2] / length
  ];
  
  // Calculate the rotation quaternion to align the bond
  // Default cylinder in Three.js is along the Y axis
  const yAxis = [0, 1, 0];
  const rotationAxis = [
    yAxis[1] * normalizedDirection[2] - yAxis[2] * normalizedDirection[1],
    yAxis[2] * normalizedDirection[0] - yAxis[0] * normalizedDirection[2],
    yAxis[0] * normalizedDirection[1] - yAxis[1] * normalizedDirection[0]
  ];
  
  const dot = yAxis[0] * normalizedDirection[0] + 
              yAxis[1] * normalizedDirection[1] + 
              yAxis[2] * normalizedDirection[2];
  
  // Handle special case when vectors are parallel
  if (Math.abs(dot - 1) < 0.0001) {
    // Vectors are parallel, no rotation needed
    return (
      <mesh position={mid}>
        <cylinderGeometry args={[0.1, 0.1, length, 16]} />
        <meshStandardMaterial color="#999999" />
      </mesh>
    );
  } 
  else if (Math.abs(dot + 1) < 0.0001) {
    // Vectors are anti-parallel, rotate 180° around X axis
    return (
      <mesh position={mid} rotation={[Math.PI, 0, 0]}>
        <cylinderGeometry args={[0.1, 0.1, length, 16]} />
        <meshStandardMaterial color="#999999" />
      </mesh>
    );
  }
  
  // Calculate rotation based on cross product and dot product
  const angle = Math.acos(dot);
  const rotAxisLength = Math.sqrt(
    rotationAxis[0] * rotationAxis[0] + 
    rotationAxis[1] * rotationAxis[1] + 
    rotationAxis[2] * rotationAxis[2]
  );
  
  if (rotAxisLength > 0.0001) {
    const normalizedRotAxis = [
      rotationAxis[0] / rotAxisLength,
      rotationAxis[1] / rotAxisLength,
      rotationAxis[2] / rotAxisLength
    ];
    
    return (
      <group position={mid}>
        <mesh rotation={[
          normalizedRotAxis[0] * angle,
          normalizedRotAxis[1] * angle,
          normalizedRotAxis[2] * angle
        ]}>
          <cylinderGeometry args={[0.1, 0.1, length, 16]} />
          <meshStandardMaterial color="#999999" />
        </mesh>
      </group>
    );
  }
  
  return null;
};

// Molecule Scene Component
const MoleculeScene = ({ data, showLabels }) => {
  const { camera } = useThree();
  
  // Center molecule on first render
  useEffect(() => {
    if (data && data.atoms && data.atoms.length > 0) {
      // Calculate bounding box
      let minX = Infinity, minY = Infinity, minZ = Infinity;
      let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
      
      data.atoms.forEach(atom => {
        minX = Math.min(minX, atom.x);
        minY = Math.min(minY, atom.y);
        minZ = Math.min(minZ, atom.z);
        maxX = Math.max(maxX, atom.x);
        maxY = Math.max(maxY, atom.y);
        maxZ = Math.max(maxZ, atom.z);
      });
      
      // Calculate center and size
      const center = [
        (minX + maxX) / 2,
        (minY + maxY) / 2,
        (minZ + maxZ) / 2
      ];
      
      const size = Math.max(
        maxX - minX,
        maxY - minY,
        maxZ - minZ
      );
      
      // Position camera to view entire molecule
      const fov = camera.fov * (Math.PI / 180);
      let distance = size / (2 * Math.tan(fov / 2));
      distance = Math.max(distance * 1.5, 5); // Add some margin
      
      camera.position.set(center[0], center[1], center[2] + distance);
      camera.lookAt(center[0], center[1], center[2]);
      camera.updateProjectionMatrix();
    }
  }, [data, camera]);
  
  if (!data || !data.atoms || !data.bonds) {
    return null;
  }
  
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 10]} intensity={0.5} />
      
      {/* Atoms */}
      {data.atoms.map((atom) => (
        <Atom
          key={`atom-${atom.id}`}
          position={[atom.x, atom.y, atom.z]}
          element={atom.element}
          radius={ATOM_RADII[atom.element] || ATOM_RADII.DEFAULT}
          showLabel={showLabels}
        />
      ))}
      
      {/* Bonds */}
      {data.bonds.map((bond, index) => {
        const atom1 = data.atoms.find(a => a.id === bond.atom1_id);
        const atom2 = data.atoms.find(a => a.id === bond.atom2_id);
        
        if (!atom1 || !atom2) return null;
        
        return (
          <Bond
            key={`bond-${index}`}
            start={[atom1.x, atom1.y, atom1.z]}
            end={[atom2.x, atom2.y, atom2.z]}
          />
        );
      })}
      
      <OrbitControls enableDamping dampingFactor={0.25} />
    </>
  );
};

// Main Molecule Viewer Component
const MoleculeViewer = ({ moleculeId, width = '100%', height = '500px', showLabels = true }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [moleculeData, setMoleculeData] = useState(null);
  
  // Fetch molecule data
  useEffect(() => {
    if (!moleculeId) return;
    
    const fetchMoleculeData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch visualization data from API
        const response = await axios.post(`${API_URL}/visualization/molecule`, {
          molecule_id: moleculeId,
          visualization_type: '3d'
        });
        
        setMoleculeData(response.data.data);
      } catch (err) {
        console.error('Error fetching molecule data:', err);
        setError('Failed to load molecule visualization');
      } finally {
        setLoading(false);
      }
    };
    
    fetchMoleculeData();
  }, [moleculeId]);
  
  return (
    <div style={{ width, height, position: 'relative' }}>
      {loading ? (
        <div style={{ 
          position: 'absolute', 
          top: '50%', 
          left: '50%', 
          transform: 'translate(-50%, -50%)'
        }}>
          Loading molecule...
        </div>
      ) : error ? (
        <div style={{ 
          position: 'absolute', 
          top: '50%', 
          left: '50%', 
          transform: 'translate(-50%, -50%)', 
          color: 'red' 
        }}>
          {error}
        </div>
      ) : (
        <Canvas>
          <MoleculeScene data={moleculeData} showLabels={showLabels} />
        </Canvas>
      )}
    </div>
  );
};

export default MoleculeViewer; 