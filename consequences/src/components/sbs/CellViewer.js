import React, { Suspense, useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line, Html } from '@react-three/drei';
import * as THREE from 'three';
import { useSBS } from './SBSContext';

// ── Organelle geometry ──────────────────────────────────────────────

function CellMembrane() {
  const ref = useRef();
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.05;
    }
  });
  return (
    <mesh ref={ref}>
      <sphereGeometry args={[2.8, 64, 64]} />
      <meshPhysicalMaterial
        color="#e8dcc8"
        transparent
        opacity={0.12}
        roughness={0.3}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  );
}

function Nucleus() {
  const ref = useRef();
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.05;
      ref.current.rotation.z = Math.cos(state.clock.elapsedTime * 0.2) * 0.03;
    }
  });
  return (
    <group ref={ref} position={[0, 0.1, 0]}>
      <mesh>
        <sphereGeometry args={[0.9, 48, 48]} />
        <meshPhysicalMaterial
          color="#6b5b95"
          transparent
          opacity={0.25}
          roughness={0.4}
          clearcoat={0.3}
        />
      </mesh>
      <mesh>
        <sphereGeometry args={[0.35, 32, 32]} />
        <meshStandardMaterial color="#4a3f6b" transparent opacity={0.5} />
      </mesh>
    </group>
  );
}

function Mitochondrion({ position, rotation, scale = 1 }) {
  const ref = useRef();
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 0.8 + position[0]) * 0.03;
    }
  });

  const cristae = useMemo(() => {
    const curves = [];
    for (let i = 0; i < 5; i++) {
      const x = -0.25 + i * 0.12;
      curves.push(
        <mesh key={i} position={[x, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
          <planeGeometry args={[0.18, 0.08]} />
          <meshStandardMaterial color="#d4956a" transparent opacity={0.6} side={THREE.DoubleSide} />
        </mesh>
      );
    }
    return curves;
  }, []);

  return (
    <group ref={ref} position={position} rotation={rotation} scale={scale}>
      <mesh>
        <capsuleGeometry args={[0.12, 0.5, 8, 16]} />
        <meshPhysicalMaterial
          color="#e07b4c"
          transparent
          opacity={0.35}
          roughness={0.5}
          clearcoat={0.2}
        />
      </mesh>
      <mesh>
        <capsuleGeometry args={[0.09, 0.42, 8, 16]} />
        <meshPhysicalMaterial
          color="#c46838"
          transparent
          opacity={0.2}
          roughness={0.6}
        />
      </mesh>
      {cristae}
    </group>
  );
}

function EndoplasmicReticulum() {
  const ref = useRef();
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.04;
    }
  });

  const sheets = useMemo(() => {
    const items = [];
    for (let i = 0; i < 12; i++) {
      const angle = (i / 12) * Math.PI * 2;
      const r = 1.2 + Math.sin(i * 1.7) * 0.3;
      const y = Math.cos(i * 2.1) * 0.4;
      items.push(
        <mesh
          key={i}
          position={[Math.cos(angle) * r, y, Math.sin(angle) * r]}
          rotation={[Math.random() * 0.5, angle + Math.PI / 2, Math.random() * 0.3]}
        >
          <planeGeometry args={[0.6, 0.25, 4, 2]} />
          <meshPhysicalMaterial
            color="#7eb8a0"
            transparent
            opacity={0.2}
            roughness={0.7}
            side={THREE.DoubleSide}
            depthWrite={false}
          />
        </mesh>
      );
    }

    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2 + 0.4;
      const r = 1.1 + Math.sin(i * 2.3) * 0.2;
      const y = Math.cos(i * 1.5) * 0.3;
      items.push(
        <mesh
          key={`tube-${i}`}
          position={[Math.cos(angle) * r, y, Math.sin(angle) * r]}
          rotation={[0, angle, Math.PI / 2]}
        >
          <capsuleGeometry args={[0.02, 0.4, 4, 8]} />
          <meshStandardMaterial color="#5a9e80" transparent opacity={0.3} />
        </mesh>
      );
    }
    return items;
  }, []);

  return <group ref={ref}>{sheets}</group>;
}

function GolgiApparatus({ position = [1.6, -0.2, 0.8] }) {
  const stacks = useMemo(() => {
    const items = [];
    for (let i = 0; i < 5; i++) {
      items.push(
        <mesh key={i} position={[0, i * 0.07 - 0.14, 0]}>
          <boxGeometry args={[0.35, 0.02, 0.2 - i * 0.02]} />
          <meshPhysicalMaterial
            color="#c4a84d"
            transparent
            opacity={0.3 + i * 0.05}
            roughness={0.5}
          />
        </mesh>
      );
    }
    return items;
  }, []);

  return <group position={position} rotation={[0.2, 0.5, 0.1]}>{stacks}</group>;
}

function Vesicles() {
  const vesicles = useMemo(() => {
    const items = [];
    for (let i = 0; i < 15; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      const r = 1.8 + Math.random() * 0.8;
      items.push({
        pos: [
          r * Math.sin(phi) * Math.cos(theta),
          r * Math.cos(phi) * 0.6,
          r * Math.sin(phi) * Math.sin(theta),
        ],
        size: 0.03 + Math.random() * 0.04,
        color: ['#a8d8ea', '#aa96da', '#fcbad3', '#ffffd2'][Math.floor(Math.random() * 4)],
      });
    }
    return items;
  }, []);

  return (
    <group>
      {vesicles.map((v, i) => (
        <mesh key={i} position={v.pos}>
          <sphereGeometry args={[v.size, 12, 12]} />
          <meshStandardMaterial color={v.color} transparent opacity={0.5} />
        </mesh>
      ))}
    </group>
  );
}

// ── Circuit nodes projected onto cell ───────────────────────────────

const COMPARTMENT_POSITIONS = {
  cytoplasm:              { center: [0, 0, 0], radius: 2.0, yRange: [-0.8, 0.8] },
  cytosol:                { center: [0, 0, 0], radius: 2.0, yRange: [-0.8, 0.8] },
  nucleus:                { center: [0, 0.1, 0], radius: 0.7, yRange: [-0.3, 0.5] },
  mitochondria:           { center: [1.5, 0.3, -0.8], radius: 0.3, yRange: [-0.1, 0.5] },
  mitochondrial_matrix:   { center: [1.5, 0.3, -0.8], radius: 0.2, yRange: [0, 0.4] },
  endoplasmic_reticulum:  { center: [0, 0, 0], radius: 1.3, yRange: [-0.4, 0.4] },
  golgi:                  { center: [1.6, -0.2, 0.8], radius: 0.3, yRange: [-0.3, 0] },
  cell_membrane:          { center: [0, 0, 0], radius: 2.7, yRange: [-1, 1] },
  extracellular:          { center: [0, 0, 0], radius: 3.2, yRange: [-1.2, 1.2] },
  default:                { center: [0, 0, 0], radius: 1.8, yRange: [-0.6, 0.6] },
};

function getCompartmentZone(compartmentName) {
  const key = (compartmentName || 'default').toLowerCase().replace(/\s+/g, '_');
  return COMPARTMENT_POSITIONS[key] || COMPARTMENT_POSITIONS.default;
}

function CircuitNode({ position, color, name, size = 0.07, showLabel }) {
  const ref = useRef();
  useFrame((state) => {
    if (ref.current) {
      ref.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 2.5 + position[0] * 8) * 0.15);
    }
  });

  return (
    <group position={position}>
      <mesh ref={ref}>
        <sphereGeometry args={[size, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.5}
          toneMapped={false}
        />
      </mesh>
      <mesh>
        <sphereGeometry args={[size * 1.8, 16, 16]} />
        <meshBasicMaterial color={color} transparent opacity={0.08} depthWrite={false} />
      </mesh>
      {showLabel && (
        <Html distanceFactor={8} position={[0, size + 0.08, 0]} center>
          <div style={{
            background: 'rgba(0,0,0,0.7)',
            color: '#fff',
            padding: '2px 6px',
            borderRadius: 4,
            fontSize: 9,
            whiteSpace: 'nowrap',
            pointerEvents: 'none',
            fontFamily: 'monospace',
          }}>
            {name}
          </div>
        </Html>
      )}
    </group>
  );
}

function CircuitEdge({ start, end, weight, color = '#58E6D9' }) {
  const opacity = Math.min(0.6, 0.05 + weight * 0.55);
  return (
    <Line
      points={[start, end]}
      color={color}
      lineWidth={Math.max(0.5, weight * 4)}
      opacity={opacity}
      transparent
    />
  );
}

// ── Main scene ──────────────────────────────────────────────────────

function CellScene({ circuit, shaderResult, cellModelId }) {
  const { nodePositions, nodeColors, maxG } = useMemo(() => {
    if (!circuit) return { nodePositions: [], nodeColors: [], maxG: 1 };

    const positions = circuit.nodes.map((node, i) => {
      const zone = getCompartmentZone(node.compartment || node.compartmentName);
      const angle = (i / circuit.nodes.length) * Math.PI * 2 + i * 0.618;
      const spread = 0.6 + (i % 3) * 0.15;
      const r = zone.radius * spread;
      return [
        zone.center[0] + Math.cos(angle) * r,
        zone.center[1] + (zone.yRange[0] + zone.yRange[1]) / 2 + Math.sin(i * 1.3) * (zone.yRange[1] - zone.yRange[0]) * 0.3,
        zone.center[2] + Math.sin(angle) * r,
      ];
    });

    const muValues = circuit.nodes.map(n => n.mu);
    const muMin = Math.min(...muValues);
    const muMax = Math.max(...muValues);
    const muRange = muMax - muMin || 1;

    const colors = circuit.nodes.map((node, i) => {
      if (shaderResult) {
        const Se = shaderResult.texture[i * 4];
        const Sk = shaderResult.texture[i * 4 + 1];
        const St = shaderResult.texture[i * 4 + 2];
        return new THREE.Color(Se, Sk, St);
      }
      const t = (node.mu - muMin) / muRange;
      return new THREE.Color().setHSL(0.55 - t * 0.4, 0.8, 0.5);
    });

    const mg = Math.max(...circuit.edges.map(e => e.conductance));
    return { nodePositions: positions, nodeColors: colors, maxG: mg };
  }, [circuit, shaderResult]);

  if (!circuit) return null;

  const showMito = cellModelId !== 'minimal';

  return (
    <group>
      {/* Cell structure */}
      <CellMembrane />
      <Nucleus />
      {showMito && (
        <>
          <Mitochondrion position={[1.5, 0.3, -0.8]} rotation={[0.3, 0.8, 0.2]} scale={1.1} />
          <Mitochondrion position={[-1.2, -0.4, 1.0]} rotation={[-0.2, 2.1, 0.4]} scale={0.85} />
          <Mitochondrion position={[0.5, -0.6, -1.5]} rotation={[0.5, -0.5, 0.1]} scale={0.95} />
          <Mitochondrion position={[-1.8, 0.5, -0.5]} rotation={[0.1, 1.2, -0.3]} scale={0.75} />
        </>
      )}
      <EndoplasmicReticulum />
      <GolgiApparatus />
      <Vesicles />

      {/* Circuit edges */}
      {circuit.edges.map((edge, i) => (
        <CircuitEdge
          key={i}
          start={nodePositions[edge.src]}
          end={nodePositions[edge.dst]}
          weight={edge.conductance / maxG}
          color={shaderResult ? '#88ddff' : '#58E6D9'}
        />
      ))}

      {/* Circuit nodes projected onto organelles */}
      {circuit.nodes.map((node, i) => (
        <CircuitNode
          key={i}
          position={nodePositions[i]}
          color={`#${nodeColors[i].getHexString()}`}
          name={node.name}
          size={0.06 + (node.concentration / Math.max(...circuit.nodes.map(n => n.concentration))) * 0.05}
          showLabel={circuit.nodes.length <= 20}
        />
      ))}
    </group>
  );
}

export default function CellViewer() {
  const { circuit, cellModel, shaderResult } = useSBS();

  if (!circuit) {
    return (
      <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm
                      flex items-center justify-center min-h-[500px]">
        <p className="text-dark/40 dark:text-light/40 text-sm">
          Circuit will be projected onto 3D cell geometry here
        </p>
      </div>
    );
  }

  return (
    <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl overflow-hidden shadow-sm"
         style={{ minHeight: 500 }}>
      <div className="p-2 border-b border-dark/10 dark:border-light/10 flex items-center justify-between">
        <span className="text-xs text-dark/60 dark:text-light/60">
          {cellModel?.name || 'Eukaryotic Cell'} — {circuit.numNodes} nodes projected — {shaderResult ? 'S-entropy colored' : 'potential colored'}
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 dark:bg-primaryDark/10 text-primary dark:text-primaryDark">
          interactive
        </span>
      </div>
      <Canvas
        camera={{ position: [3.5, 2.5, 3.5], fov: 40 }}
        style={{ height: 470, background: '#0a0a0f' }}
        gl={{ antialias: true, alpha: false }}
      >
        <color attach="background" args={['#0a0a0f']} />
        <fog attach="fog" args={['#0a0a0f', 6, 12]} />
        <ambientLight intensity={0.3} />
        <directionalLight position={[5, 5, 5]} intensity={0.7} color="#ffffff" />
        <directionalLight position={[-3, 2, -4]} intensity={0.3} color="#58E6D9" />
        <pointLight position={[0, 3, 0]} intensity={0.4} color="#B63E96" distance={8} />
        <pointLight position={[-2, -1, 2]} intensity={0.2} color="#58E6D9" distance={6} />
        <Suspense fallback={null}>
          <CellScene circuit={circuit} shaderResult={shaderResult} cellModelId={cellModel?.id} />
        </Suspense>
        <OrbitControls
          enableZoom
          enablePan
          autoRotate
          autoRotateSpeed={0.3}
          minDistance={2}
          maxDistance={10}
        />
      </Canvas>
    </div>
  );
}
