import { useEffect, useContext, useRef, useState } from 'react';
import * as THREE from 'three';
import type ThreeGlobe from 'three-globe';
import type { OrbitControls } from 'three/examples/jsm/Addons.js';

import { initializeGlobe } from './hooks/init';
import { GlobeContext } from '@/App';

import globeData from '@/assets/globe-data.json';

interface FrameData {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  renderers: THREE.WebGLRenderer[];
  globe: ThreeGlobe;
}

const Globe = () => {
  const containerRef = useRef(null);
  const [frameData, setFrameData] = useState<FrameData | null>(null);
  const { setGlobe, setCamera, setRenderers } = useContext(GlobeContext);

  useEffect(() => {
    if (!containerRef.current || !setCamera || !setGlobe || !setRenderers)
      return;

    const initData = initializeGlobe({
      containerRef,
      globeData,
      windowCenter: { x: window.innerWidth / 2, y: window.innerHeight / 2 },
      mousePosition: { x: 0, y: 0 },
    });

    if (!initData) return;
    const { scene, camera, controls, globe, renderers } = initData as FrameData;
    setFrameData({ scene, camera, controls, globe, renderers } as FrameData);
    setGlobe(globe); setCamera(camera); setRenderers(renderers)
  }, [setCamera, setGlobe, setRenderers]);    

  useEffect(() => {
    if (!frameData) return;

    frameData.controls && frameData.controls.update();

    const animate = () => {
      const { scene, camera, controls, renderers } = frameData as FrameData;
      camera && camera.lookAt(scene.position);
      controls && controls.update();
      renderers?.forEach((r) => {
        r.render(scene, camera);
      });

      requestAnimationFrame(animate);
    };
    animate()
  }, [frameData]);

  return (
    <div ref={containerRef} id='globe-visualizer'></div>
  )
};

export default Globe;
