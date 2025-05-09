import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { TrackballControls } from 'three/examples/jsm/controls/TrackballControls';
import { ConvexGeometry } from 'three/examples/jsm/geometries/ConvexGeometry';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Atom colors based on standard CPK coloring
const ATOM_COLORS = {
  H: 0xFFFFFF, // White
  C: 0x909090, // Gray
  N: 0x3050F8, // Blue
  O: 0xFF0D0D, // Red
  P: 0xFF8000, // Orange
  S: 0xFFFF30, // Yellow
  Cl: 0x1FF01F, // Green
  Na: 0x0000FF, // Blue
  K: 0x0000FF,  // Blue
  Fe: 0xFF5500, // Orange-red
  Mg: 0x00FF00, // Green
  Ca: 0x00FF00, // Green
  DEFAULT: 0xDDDDDD // Default color
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

const MoleculeViewer = ({ moleculeId, width = '100%', height = '500px', showLabels = true }) => {
  const containerRef = useRef(null);
  const rendererRef = useRef(null);
  const labelRendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [moleculeData, setMoleculeData] = useState(null);

  // Initialize the 3D scene
  useEffect(() => {
    if (!containerRef.current) return;

    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xffffff);
    sceneRef.current = scene;

    // Create camera
    const camera = new THREE.PerspectiveCamera(75, containerRef.current.clientWidth / containerRef.current.clientHeight, 0.1, 1000);
    camera.position.z = 5;
    cameraRef.current = camera;

    // Create renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Create label renderer for atom labels
    const labelRenderer = new CSS2DRenderer();
    labelRenderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    labelRenderer.domElement.style.position = 'absolute';
    labelRenderer.domElement.style.top = '0';
    labelRenderer.domElement.style.pointerEvents = 'none';
    containerRef.current.appendChild(labelRenderer.domElement);
    labelRendererRef.current = labelRenderer;

    // Add controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    controlsRef.current = controls;

    // Add lighting
    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
      labelRenderer.render(scene, camera);
    };
    animate();

    // Handle window resize
    const handleResize = () => {
      if (!containerRef.current) return;
      
      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
      labelRenderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup on unmount
    return () => {
      window.removeEventListener('resize', handleResize);
      if (containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
        containerRef.current.removeChild(labelRenderer.domElement);
      }
      scene.clear();
    };
  }, []);

  // Fetch molecule data and render
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
        
        // Render the molecule
        if (response.data.data && sceneRef.current) {
          renderMolecule(response.data.data);
        }
      } catch (err) {
        console.error('Error fetching molecule data:', err);
        setError('Failed to load molecule visualization');
      } finally {
        setLoading(false);
      }
    };
    
    fetchMoleculeData();
  }, [moleculeId]);

  // Render the molecule in the 3D scene
  const renderMolecule = (data) => {
    if (!sceneRef.current || !data || !data.atoms || !data.bonds) return;
    
    // Clear existing content
    while (sceneRef.current.children.length > 0) {
      sceneRef.current.remove(sceneRef.current.children[0]);
    }
    
    // Add lighting
    const ambientLight = new THREE.AmbientLight(0x404040);
    sceneRef.current.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(1, 1, 1);
    sceneRef.current.add(directionalLight);
    
    // Draw atoms
    const atomObjects = {};
    data.atoms.forEach(atom => {
      const color = ATOM_COLORS[atom.element] || ATOM_COLORS.DEFAULT;
      const radius = ATOM_RADII[atom.element] || ATOM_RADII.DEFAULT;
      
      const geometry = new THREE.SphereGeometry(radius, 32, 32);
      const material = new THREE.MeshPhongMaterial({ color });
      
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(atom.x, atom.y, atom.z);
      sceneRef.current.add(mesh);
      
      atomObjects[atom.id] = mesh;
      
      // Add label if enabled
      if (showLabels) {
        const labelDiv = document.createElement('div');
        labelDiv.className = 'atom-label';
        labelDiv.textContent = atom.element;
        labelDiv.style.color = '#000000';
        labelDiv.style.fontSize = '0.8em';
        
        const label = new CSS2DObject(labelDiv);
        label.position.set(0, radius + 0.1, 0);
        mesh.add(label);
      }
    });
    
    // Draw bonds
    data.bonds.forEach(bond => {
      const atom1 = data.atoms.find(a => a.id === bond.atom1_id);
      const atom2 = data.atoms.find(a => a.id === bond.atom2_id);
      
      if (!atom1 || !atom2) return;
      
      const start = new THREE.Vector3(atom1.x, atom1.y, atom1.z);
      const end = new THREE.Vector3(atom2.x, atom2.y, atom2.z);
      
      // Create a cylinder representing the bond
      const direction = new THREE.Vector3().subVectors(end, start);
      const midpoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
      
      const bondLength = direction.length();
      direction.normalize();
      
      // Create bond cylinder
      const bondGeometry = new THREE.CylinderGeometry(0.1, 0.1, bondLength, 16);
      const bondMaterial = new THREE.MeshPhongMaterial({ color: 0x999999 });
      
      const bondMesh = new THREE.Mesh(bondGeometry, bondMaterial);
      
      // Position and orient the bond
      bondMesh.position.copy(midpoint);
      
      // Orient the cylinder to align with the bond direction
      const quaternion = new THREE.Quaternion();
      quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
      bondMesh.quaternion.copy(quaternion);
      
      sceneRef.current.add(bondMesh);
    });
    
    // Center the molecule in view
    const boundingBox = new THREE.Box3().setFromObject(sceneRef.current);
    const center = boundingBox.getCenter(new THREE.Vector3());
    const size = boundingBox.getSize(new THREE.Vector3());
    
    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = cameraRef.current.fov * (Math.PI / 180);
    let distance = maxDim / (2 * Math.tan(fov / 2));
    
    // Add some margin
    distance *= 1.5;
    
    // Set camera position
    cameraRef.current.position.copy(center);
    cameraRef.current.position.z += distance;
    cameraRef.current.lookAt(center);
    
    // Update controls target
    controlsRef.current.target.copy(center);
    controlsRef.current.update();
  };

  return (
    <div style={{ width, height, position: 'relative' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      
      {loading && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
          Loading molecule...
        </div>
      )}
      
      {error && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'red' }}>
          {error}
        </div>
      )}
    </div>
  );
};

export default MoleculeViewer; 