import * as THREE from 'three';
import { createCar } from './car';
import { customizeModel } from './customizeModel';
import { createSceneContext } from './scene';
import { setupUI } from './ui';

const params = new URLSearchParams(location.search);
const gate = params.get('gate') === '1';
const clay = params.get('clay') === '1';

const { renderer, scene, camera, cam, controls, look, applyCamera, applyLook } = createSceneContext(gate);

// Factory: real one if src/createCaltexStationModel.ts exists, else a placeholder box.
const found = import.meta.glob('./createCaltexStationModel.ts');
let model: THREE.Object3D;
const loader = found['./createCaltexStationModel.ts'];
if (loader) {
  const mod: any = await loader();
  model = mod.createCaltexStationModel({});
} else {
  model = new THREE.Mesh(new THREE.BoxGeometry(14, 1, 20), new THREE.MeshStandardMaterial({ color: 0x8a6a4a }));
  model.name = 'placeholder';
}
scene.add(model);

// The car is not part of the model: no picking, no gate renders. __CAR_T__ freezes its clock for screenshots.
const car = gate ? null : createCar();
if (car) scene.add(car.group);

const { baseColors, orangeSpec, waveFlags, partById } = await customizeModel(
  model,
  scene,
  gate,
  clay,
  () => look.wind,
);

const { getCarSpeed, pickApi } = setupUI({
  model,
  scene,
  camera,
  renderer,
  controls,
  look,
  applyLook,
  gate,
  baseColors,
  orangeSpec,
  partById,
});

(window as any).__IMG2THREEJS_PICK__ = pickApi;
(window as any).__IMG2THREEJS_VIEWER__ = { renderer, scene, camera, controls };
(window as any).__IMG2THREEJS_CAPTURE__ = {
  setCamera(s: any) {
    Object.assign(cam, {
      azimuth: s.azimuth ?? cam.azimuth,
      elevation: s.elevation ?? cam.elevation,
      distance: s.distance ?? cam.distance,
      fov: s.fov ?? cam.fov,
    });
    if (s.target) cam.target.set(s.target[0], s.target[1], s.target[2]);
    applyCamera();
    controls.target.copy(cam.target);
    controls.update();
    renderer.render(scene, camera);
  },
  setReferenceMode: () => ({ ok: true }),
};

let carClock = 0;
let carLast = performance.now() / 1000;
function loop() {
  controls.update();
  waveFlags(performance.now() / 1000);
  if (car) {
    const now = performance.now() / 1000;
    carClock += (now - carLast) * getCarSpeed();
    carLast = now;
    car.update((window as any).__CAR_T__ ?? carClock);
  }
  renderer.render(scene, camera);
  requestAnimationFrame(loop);
}

renderer.render(scene, camera);
requestAnimationFrame(() => {
  (window as any).__IMG2THREEJS_READY__ = true;
  loop();
});
