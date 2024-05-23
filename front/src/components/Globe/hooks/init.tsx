import {
  WebGLRenderer,
  Scene,
  PerspectiveCamera,
  AmbientLight,
  DirectionalLight,
  Color,
  MeshBasicMaterial,
} from "three";
import { CSS2DRenderer } from "three/examples/jsm/renderers/CSS2DRenderer.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import ThreeGlobe from "three-globe";

export const GLOBE_SETTINGS = {
  COLORS: {
    background: "#212121",
    globe: "#133D6D",
    ambientLight: "#0A0A0A",
    polygon: "#9BB579",
    emissionLight: "#DEFFD9",
  },
  atmosphereLevel: 0.2,
};

interface GlobeInitParams {
  containerRef: React.RefObject<HTMLDivElement>;
  globeData: any;
  windowCenter: { x: number; y: number };
  mousePosition: { x: number; y: number };
}


export const initializeGlobe = ({ 
  containerRef, 
  globeData, 
  windowCenter,
  mousePosition,
}: GlobeInitParams) => {
  const container = containerRef.current;
  if (!container) return;
  container.innerHTML = "";

  const renderers = [new WebGLRenderer(), new CSS2DRenderer()];
  renderers.forEach((r, idx) => {
    r.setSize(window.innerWidth, window.innerHeight);
    if (idx > 0) {
      r.domElement.style.position = "absolute";
      r.domElement.style.top = "0px";
      r.domElement.style.pointerEvents = "none";
    }
    container.appendChild(r.domElement);
  });

  const scene = new Scene();

  const globe = new ThreeGlobe({ waitForGlobeReady: true, animateIn: true })
    .hexPolygonsData(globeData.features)
    .hexPolygonResolution(3)
    .hexPolygonMargin(0.25)
    .hexPolygonUseDots(true)
    .hexPolygonColor(() => GLOBE_SETTINGS.COLORS.polygon)
    .atmosphereAltitude(GLOBE_SETTINGS.atmosphereLevel)

  const globeMaterial = new MeshBasicMaterial({
    color: new Color(GLOBE_SETTINGS.COLORS.globe),
  });
  globe.position.y = 0;
  globe.globeMaterial(globeMaterial);

  scene.add(globe);
  scene.add(new AmbientLight(new Color(GLOBE_SETTINGS.COLORS.ambientLight), 1));  

  const camera = new PerspectiveCamera();
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  const dLight1 = new DirectionalLight(
    new Color(GLOBE_SETTINGS.COLORS.emissionLight),
    2
  );
  dLight1.shadow.normalBias = 2;
  dLight1.position.set(-200, -100, 200);
  dLight1.castShadow = false;
  camera.add(dLight1);
  camera.position.z = 400;
  camera.position.y = 200;

  scene.add(camera);

  const controls = new OrbitControls(camera, renderers[0].domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 150;
  controls.maxDistance = 300;
  controls.rotateSpeed = 0.4;
  controls.zoomSpeed = 1;
  controls.autoRotate = true;
  controls.autoRotateSpeed = -0.05;
  globe.setPointOfView(camera.position, globe.position);
  controls.addEventListener("change", () =>
    globe.setPointOfView(camera.position, globe.position)
  );

  const onWindowResize = () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    windowCenter.x = window.innerWidth / 1.5;
    windowCenter.y = window.innerHeight / 1.5;
    renderers.forEach((r) => r.setSize(window.innerWidth, window.innerHeight));
  };

  const onMouseMove = (event: {clientX: number, clientY: number}) => {
    mousePosition.x = event.clientX - windowCenter.x;
    mousePosition.y = event.clientY - windowCenter.y;
  };

  window.addEventListener("resize", onWindowResize, false);
  document.addEventListener("mousemove", onMouseMove);

  const animate = () => {
    camera && camera.lookAt(scene.position);
    controls && controls.update();
    renderers.forEach((r) => {
      r.render(scene, camera);
    });
    requestAnimationFrame(animate);
  };

  animate();


  return { scene, camera, controls, globe };
};
