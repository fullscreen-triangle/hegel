import React, { Suspense, useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line } from '@react-three/drei';
import * as THREE from 'three';
import { useSBS } from './SBSContext';

function CircuitNode({ position, color, name, size = 0.08 }) {
  const ref = useRef();
  useFrame((state) => {
    if (ref.current) {
      ref.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 2 + position[0] * 10) * 0.1);
    }
  });

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[size, 16, 16]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.3} />
    </mesh>
  );
}

function CircuitEdge({ start, end, weight }) {
  const opacity = Math.min(0.8, 0.1 + weight * 0.7);
  return (
    <Line
      points={[start, end]}
      color="#58E6D9"
      lineWidth={Math.max(0.5, weight * 3)}
      opacity={opacity}
      transparent
    />
  );
}

function ProceduralCircuit({ circuit, shaderResult }) {
  const { nodePositions, colorScale } = useMemo(() => {
    if (!circuit) return { nodePositions: [], colorScale: () => '#ffffff' };

    const muValues = circuit.nodes.map(n => n.mu);
    const muMin = Math.min(...muValues);
    const muMax = Math.max(...muValues);
    const muRange = muMax - muMin || 1;

    const positions = circuit.nodes.map((node, i) => {
      const angle = (i / circuit.nodes.length) * Math.PI * 2;
      const radius = 1.5 + (node.mu - muMin) / muRange * 0.5;
      return [
        Math.cos(angle) * radius,
        (node.mu - muMin) / muRange - 0.5,
        Math.sin(angle) * radius,
      ];
    });

    const scale = (mu) => {
      const t = (mu - muMin) / muRange;
      const r = Math.floor(lerp(46, 255, t));
      const g = Math.floor(lerp(204, 127, t));
      const b = Math.floor(lerp(113, 0, t));
      return `rgb(${r},${g},${b})`;
    };

    return { nodePositions: positions, colorScale: scale };
  }, [circuit]);

  if (!circuit) return null;

  const maxG = Math.max(...circuit.edges.map(e => e.conductance));

  return (
    <group>
      {circuit.edges.map((edge, i) => (
        <CircuitEdge
          key={i}
          start={nodePositions[edge.src]}
          end={nodePositions[edge.dst]}
          weight={edge.conductance / maxG}
        />
      ))}
      {circuit.nodes.map((node, i) => (
        <CircuitNode
          key={i}
          position={nodePositions[i]}
          color={shaderResult
            ? entropyColor(shaderResult.texture[i * 4], shaderResult.texture[i * 4 + 1], shaderResult.texture[i * 4 + 2])
            : colorScale(node.mu)}
          name={node.name}
          size={0.06 + (node.concentration / Math.max(...circuit.nodes.map(n => n.concentration))) * 0.06}
        />
      ))}
    </group>
  );
}

function lerp(a, b, t) { return a + (b - a) * t; }

function entropyColor(Se, Sk, St) {
  const r = Math.floor(Se * 255);
  const g = Math.floor(Sk * 255);
  const b = Math.floor(St * 255);
  return `rgb(${r},${g},${b})`;
}

export default function CellViewer() {
  const { circuit, cellModel, shaderResult } = useSBS();

  if (!circuit) {
    return (
      <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl p-6 shadow-sm
                      flex items-center justify-center min-h-[400px]">
        <p className="text-dark/40 dark:text-light/40 text-sm">
          Circuit will be visualized here
        </p>
      </div>
    );
  }

  return (
    <div className="bg-light dark:bg-dark border border-dark/10 dark:border-light/10 rounded-xl overflow-hidden shadow-sm"
         style={{ minHeight: 400 }}>
      <div className="p-2 border-b border-dark/10 dark:border-light/10">
        <span className="text-xs text-dark/60 dark:text-light/60">
          {cellModel?.name || 'Procedural'} — {shaderResult ? 'S-entropy colored' : 'Chemical potential colored'}
        </span>
      </div>
      <Canvas camera={{ position: [0, 2, 4], fov: 45 }} style={{ height: 380, background: 'transparent' }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={0.8} />
        <pointLight position={[-3, 3, -3]} intensity={0.4} color="#58E6D9" />
        <Suspense fallback={null}>
          <ProceduralCircuit circuit={circuit} shaderResult={shaderResult} />
        </Suspense>
        <OrbitControls enableZoom enablePan autoRotate autoRotateSpeed={0.5} />
      </Canvas>
    </div>
  );
}
