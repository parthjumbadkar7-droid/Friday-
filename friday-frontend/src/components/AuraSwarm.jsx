import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame, extend } from '@react-three/fiber';
import { OrbitControls, Effects } from '@react-three/drei';
import { UnrealBloomPass } from 'three-stdlib';
import * as THREE from 'three';

extend({ UnrealBloomPass });

const ParticleSwarm = () => {
  const meshRef = useRef();
  const count = 20000;
  const speedMult = 1;
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const target = useMemo(() => new THREE.Vector3(), []);
  const pColor = useMemo(() => new THREE.Color(), []);
  const color = pColor;
  
  const positions = useMemo(() => {
     const pos = [];
     for(let i=0; i<count; i++) pos.push(new THREE.Vector3((Math.random()-0.5)*100, (Math.random()-0.5)*100, (Math.random()-0.5)*100));
     return pos;
  }, []);

  const material = useMemo(() => new THREE.MeshBasicMaterial({ color: 0xffffff }), []);
  const geometry = useMemo(() => new THREE.TetrahedronGeometry(0.25), []);

  const PARAMS = useMemo(() => ({"recall":0.56,"silence":0.2,"drift":0.82,"aScale":30,"spark":1}), []);
  const addControl = (id, l, min, max, val) => {
      return PARAMS[id] !== undefined ? PARAMS[id] : val;
  };

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.getElapsedTime() * speedMult;

    // Apply continuous 3D rotation to the entire swarm on X, Y, and Z axes
    meshRef.current.rotation.x = time * 0.04;
    meshRef.current.rotation.y = time * 0.06;
    meshRef.current.rotation.z = time * 0.02;

    if(material.uniforms && material.uniforms.uTime) {
         material.uniforms.uTime.value = time;
    }

    for (let i = 0; i < count; i++) {
        const recall  = addControl("recall",  "Memory Rising",   0,  1,   0.5);
        const silence = addControl("silence", "Erasure (Depth)", 0,  1,   0.3);
        const drift   = addControl("drift",   "Current Drift",   0,  2,   0.6);
        const aScale  = addControl("aScale",  "Scale",           8,  30,  16);
        const spark   = addControl("spark",   "Memory Flash",   0,  1,   0.7);
        
        const n       = i / count;
        const seed    = n * 6.2832 * 47.3;
        
        const memX    = Math.sin(seed * 0.17) * aScale;
        const memZ    = Math.cos(seed * 0.13) * aScale;
        const baseY   = (Math.sin(seed * 0.29) * 0.5 + 0.5) * (-aScale * 1.4) * silence;
        
        const memFreq = 0.3 + Math.abs(Math.sin(seed * 0.07)) * 0.9;
        const memPhase= seed * 0.41;
        const riseAmt = Math.sin(time * memFreq + memPhase) * 0.5 + 0.5;
        const py      = baseY + riseAmt * aScale * recall * 0.9;
        
        const driftX  = Math.sin(time * drift * 0.2 + seed * 0.11) * aScale * 0.12;
        const driftZ  = Math.cos(time * drift * 0.15+ seed * 0.09) * aScale * 0.12;
        
        // Interactive Mouse Repulsion
        // Map pointer from normalized (-1 to +1) to approximate world coords
        const mouseX = state.pointer.x * 60; 
        const mouseY = state.pointer.y * 60;
        
        let pX = memX + driftX;
        let pY = py;
        let pZ = memZ + driftZ;
        
        const dx = pX - mouseX;
        const dy = pY - mouseY;
        const dist = Math.sqrt(dx*dx + dy*dy);
        
        // If mouse is close (within radius of 20), push particle away
        if (dist < 20) {
            const force = (20 - dist) / 20; // 0 to 1
            pX += (dx / dist) * force * 8; // push out by max 8 units
            pY += (dy / dist) * force * 8;
            pZ += force * 4; // push forward slightly too
        }

        target.set(pX, pY, pZ);
        
        const surfaceN = Math.max(0, Math.min(1, (py + aScale) / (aScale + 0.001)));
        const flash    = Math.pow(Math.max(0, Math.sin(time * 2 + memPhase)), 8) * spark;
        
        // TINT: Adjusted hue to fit FRIDAY's deep purple/blue aesthetic
        // Hue 0.65 -> Blue, 0.75 -> Deep Purple. 
        const memHue   = 0.68 + surfaceN * 0.12; 
        const memSat   = 0.9  - flash * 0.6;
        const memLit   = 0.15 + surfaceN * 0.45 + flash * 0.65;
        
        color.setHSL(memHue, Math.max(0, memSat), Math.min(1, memLit));
        
        positions[i].lerp(target, 0.1);
        dummy.position.copy(positions[i]);
        dummy.updateMatrix();
        meshRef.current.setMatrixAt(i, dummy.matrix);
        meshRef.current.setColorAt(i, pColor);
    }
    meshRef.current.instanceMatrix.needsUpdate = true;
    if (meshRef.current.instanceColor) meshRef.current.instanceColor.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[geometry, material, count]} />
  );
};

export default function AuraSwarm() {
  return (
    <div className="aura-swarm-bg" style={{ position: 'absolute', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: 0 }}>
      <Canvas camera={{ position: [0, 0, 100], fov: 60 }}>
        <fog attach="fog" args={['#0a0a1a', 0.01]} />
        <ParticleSwarm />
        {/* Enabled OrbitControls rotation so user can drag to spin the 3D scene */}
        <OrbitControls autoRotate={true} autoRotateSpeed={0.5} enableZoom={false} enablePan={false} enableRotate={true} />
        <Effects disableGamma>
            <unrealBloomPass threshold={0} strength={2.2} radius={0.5} />
        </Effects>
      </Canvas>
    </div>
  );
}
