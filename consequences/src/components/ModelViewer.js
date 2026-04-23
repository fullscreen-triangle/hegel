import React, { Suspense, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, useGLTF, ContactShadows } from '@react-three/drei';

function Model({ url }) {
  const { scene } = useGLTF(url);
  const ref = useRef();

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y += 0.005;
      ref.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
    }
  });

  return <primitive ref={ref} object={scene} scale={2.5} position={[0, -0.5, 0]} />;
}

const ModelViewer = ({ className = '' }) => {
  return (
    <div className={`w-full h-full ${className}`} style={{ minHeight: '400px' }}>
      <Canvas camera={{ position: [0, 1, 4], fov: 45 }} style={{ background: 'transparent' }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <pointLight position={[-5, 5, -5]} intensity={0.5} color="#58E6D9" />
        <Suspense fallback={null}>
          <Model url="/model/hydria_apothecary_vase.glb" />
          <ContactShadows position={[0, -1.5, 0]} opacity={0.4} scale={1} blur={2} />
        </Suspense>
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={1} />
      </Canvas>
    </div>
  );
};

export default ModelViewer;
