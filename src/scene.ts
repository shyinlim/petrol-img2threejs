import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export type LookState = { exposure: number; envIntensity: number; sunAz: number; sunEl: number; shadowRadius: number; bg: string; wind: number };
export type CameraRig = { azimuth: number; elevation: number; distance: number; fov: number; target: THREE.Vector3 };

/**
 * Sets up the WebGLRenderer, PerspectiveCamera, OrbitControls, and lighting for normal or gate mode.
 */
export function createSceneContext(gate: boolean) {
  document.body.classList.toggle('gate', gate);
  const stage = document.getElementById('stage')!;
  const w = () => (gate ? 1024 : stage.clientWidth);
  const h = () => (gate ? 687 : stage.clientHeight);

  // Normal mode is transparent: the page's CSS gradient is the background. Gate mode keeps the opaque grey.
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, alpha: !gate });
  renderer.setPixelRatio(gate ? 1 : Math.min(devicePixelRatio, 2));
  renderer.setSize(w(), h());
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.shadowMap.enabled = !gate;
  renderer.shadowMap.type = THREE.PCFShadowMap; // 0.187 has no PCFSoftShadowMap
  stage.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  if (gate) scene.background = new THREE.Color(0x303030);

  const camera = new THREE.PerspectiveCamera(35, 1024 / 687, 0.1, 500);
  // ?gate=1 keeps the reference camera. Normal mode starts low (under the soffit at 4.84) so the pumps read like v3.
  const cam: CameraRig = gate
    ? { azimuth: -50.89, elevation: 9.51, distance: 48.52, fov: 20, target: new THREE.Vector3(-0.21, 2.2, -0.11) }
    : { azimuth: -88, elevation: 4.5, distance: 40, fov: 30, target: new THREE.Vector3(0, 1.2, 0) };

  // Normal mode: slide the picture left so the model sits in the free area beside the right-hand panel (skipped on narrow windows).
  function applyViewOffset() {
    const panel = document.getElementById('panel');
    if (!gate && panel && w() >= 900) {
      camera.setViewOffset(w(), h(), (panel.offsetWidth + 16) / 2, 0, w(), h());
    } else {
      camera.clearViewOffset();
    }
  }

  function applyCamera() {
    const az = THREE.MathUtils.degToRad(cam.azimuth);
    const el = THREE.MathUtils.degToRad(cam.elevation);
    camera.fov = cam.fov;
    camera.aspect = w() / h();
    camera.position.set(
      cam.target.x + cam.distance * Math.sin(az) * Math.cos(el),
      cam.target.y + cam.distance * Math.sin(el),
      cam.target.z + cam.distance * Math.cos(az) * Math.cos(el),
    );
    camera.lookAt(cam.target);
    applyViewOffset();
    camera.updateProjectionMatrix();
  }
  applyCamera();

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false; // pan moves the target below the slab
  controls.maxPolarAngle = Math.PI / 2 - 0.05;
  controls.minDistance = 12;
  controls.maxDistance = 90;
  controls.target.copy(cam.target);
  controls.update();
  controls.saveState(); // the toolbar reset-view button returns here
  if (!gate) controls.cursorStyle = 'grab'; // OrbitControls swaps grab/grabbing itself

  // Lighting knobs. Gate mode keeps the v9 values untouched (pump-orange dE and interior_difference were tuned under them).
  const look: LookState = {
    exposure: gate ? 1 : 0.9,
    envIntensity: gate ? 0 : 0.3,
    sunAz: -37,
    sunEl: 40.6,
    shadowRadius: 0,
    bg: '#FFB375',
    wind: 0.14,
  };
  const hemi = gate
    ? new THREE.HemisphereLight(0xeaf0f6, 0xd8d2c8, 0.9)
    : new THREE.HemisphereLight(0xfff4e6, 0xe8d6c6, 0.7);
  const key = new THREE.DirectionalLight(0xfff6e8, 2.2);
  const rim = new THREE.DirectionalLight(0xffffff, 0.5);
  rim.position.set(8, 6, -10);
  scene.add(hemi, key, rim);

  if (!gate) {
    scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    Object.assign(key.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: 1, far: 60 });
    key.shadow.bias = -0.0005;
  }

  function applyLook() {
    const az = THREE.MathUtils.degToRad(look.sunAz);
    const el = THREE.MathUtils.degToRad(look.sunEl);
    const R = 18.44; // |(14, 12)|
    if (gate) key.position.set(Math.sin(az) * 14, 12, Math.cos(az) * 14); // v9 formula, bit-identical
    else key.position.set(Math.sin(az) * R * Math.cos(el), R * Math.sin(el), Math.cos(az) * R * Math.cos(el));
    renderer.toneMappingExposure = look.exposure;
    scene.environmentIntensity = look.envIntensity;
    key.shadow.radius = look.shadowRadius;
    document.documentElement.style.setProperty('--bg', look.bg);
  }
  applyLook();

  function resize() {
    renderer.setSize(w(), h());
    camera.aspect = w() / h();
    applyViewOffset();
    camera.updateProjectionMatrix();
  }
  if (!gate) addEventListener('resize', resize);

  return { stage, w, h, renderer, scene, camera, cam, controls, look, applyViewOffset, applyCamera, applyLook, resize };
}
