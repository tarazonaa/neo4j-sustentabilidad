import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import type ThreeGlobe from 'three-globe';
import type { OrbitControls } from 'three/examples/jsm/Addons.js';

import { initializeGlobe } from './hooks/init';

import globeData from '../../assets/globe-data.json';

interface FrameData {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  renderer: THREE.WebGLRenderer;
  globe: ThreeGlobe;
}

const Globe = () => {
  const containerRef = useRef(null);
  const [frameData, setFrameData] = useState<FrameData | null>(null);

  useEffect(() => {
    const initData = initializeGlobe({
      containerRef,
      globeData,
      windowCenter: { x: window.innerWidth / 2, y: window.innerHeight / 2 },
      mousePosition: { x: 0, y: 0 },
    });

    if (!initData) return;

    const { scene, camera, controls, globe } = initData as FrameData;
    setFrameData({ scene, camera, controls, globe } as FrameData);
  }, []);

  useEffect(() => {
    if (!frameData) return;
    frameData.controls && frameData.controls.update();
  }, [frameData]);

  return (
    <div ref={containerRef} id='globe-visualizer'></div>
  )
};

export default Globe;
