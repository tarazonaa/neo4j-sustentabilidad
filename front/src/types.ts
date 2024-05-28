import * as THREE from 'three';
import type ThreeGlobe from 'three-globe';
import type { OrbitControls } from 'three/examples/jsm/Addons.js';

export interface FrameData {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  controls: OrbitControls;
  renderers: THREE.WebGLRenderer[];
  globe: ThreeGlobe;
}

export interface GlobeInitParams {
  containerRef: React.RefObject<HTMLDivElement>;
  globeData: any;
  windowCenter: { x: number; y: number };
  mousePosition: { x: number; y: number };
}

export interface GlobeContextProps {
  globe: null | ThreeGlobe;
  setGlobe: null | ((d: ThreeGlobe) => void);
}