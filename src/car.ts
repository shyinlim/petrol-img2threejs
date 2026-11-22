import * as THREE from 'three';

// A silver GR Supra style coupe (real 4379 x 1854 x 1292 mm, scaled 0.754 to 3.3 x 1.4 x 0.97) drives down the
// left lane (x -4.6) between the slab edges, stops beside pump 1, then leaves. Front points to -z.
const LANE_X = -4.6, ROAD_Z = 9, END_Z = -7, STOP_Z = 4.4, GROUND_Y = 0.16, WHEEL_R = 0.27;
const IN = 4, WAIT = 4, OUT = 4, GAP = 2; // seconds
const FADE_LEN = 3; // z units: the car dissolves over the last 3 before the slab edge (in) and before z -7 (out)
const CYCLE = IN + WAIT + OUT + GAP;
const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

/** Cabin side profile as (z, y) points, extruded across x. */
function profile(pts: [number, number][], width: number) {
  const g = new THREE.ExtrudeGeometry(new THREE.Shape(pts.map(([z, y]) => new THREE.Vector2(z, y))), { depth: width, bevelEnabled: false });
  g.rotateY(-Math.PI / 2); // shape x -> world z, extrusion -> world x
  g.translate(width / 2, 0, 0);
  return g;
}

export function createCar() {
  const mats: THREE.MeshStandardMaterial[] = [];
  const mat = (p: THREE.MeshStandardMaterialParameters) => { const m = new THREE.MeshStandardMaterial(p); mats.push(m); return m; };
  const silver = mat({ color: 0xc3c7cb, metalness: 0.45, roughness: 0.32 });
  const glass = mat({ color: 0x34485a, metalness: 0.3, roughness: 0.15 });
  const black = mat({ color: 0x151515, roughness: 0.7 });
  const rim = mat({ color: 0xb8bcc0, metalness: 0.7, roughness: 0.3 });
  const head = mat({ color: 0xfff6dc, emissive: 0xfff0c0, emissiveIntensity: 0.6 });
  const tail = mat({ color: 0xd01020, emissive: 0xc00010, emissiveIntensity: 0.7 });

  const car = new THREE.Group();
  const add = (geo: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number, parent: THREE.Object3D = car) => {
    const o = new THREE.Mesh(geo, m); o.position.set(x, y, z); o.castShadow = true; parent.add(o); return o;
  };
  const box = (w: number, h: number, l: number) => new THREE.BoxGeometry(w, h, l);

  add(profile([[-1.65, 0.14], [-1.65, 0.46], [-1.3, 0.56], [-0.55, 0.64], [1.1, 0.66], [1.65, 0.62], [1.65, 0.14]], 1.4), silver, 0, 0, 0); // body with a sloped hood
  add(profile([[-0.55, 0.66], [-0.05, 0.97], [0.55, 0.97], [1.1, 0.68], [1.1, 0.66]], 1.15), silver, 0, 0, 0); // roof and pillars
  add(profile([[-0.56, 0.66], [-0.065, 0.965], [0.55, 0.965], [1.105, 0.68], [1.105, 0.66]], 1.0), glass, 0, 0, 0); // windscreen and rear glass
  add(profile([[-0.3, 0.71], [-0.02, 0.92], [0.5, 0.92], [0.88, 0.73], [0.88, 0.71]], 1.17), glass, 0, 0, 0);      // side windows
  add(box(1.2, 0.05, 0.3), silver, 0, 0.69, 1.5);                                       // duck tail
  add(box(1.36, 0.04, 0.12), black, 0, 0.15, -1.62);                                    // splitter
  add(box(0.8, 0.14, 0.02), black, 0, 0.3, -1.655);                                     // intake
  for (const s of [-1, 1]) {
    add(box(0.28, 0.07, 0.02), head, s * 0.48, 0.42, -1.655);
    add(box(0.08, 0.06, 0.12), silver, s * 0.68, 0.76, -0.08);                          // mirror
  }
  add(box(1.1, 0.07, 0.02), tail, 0, 0.58, 1.655);

  const wheels: THREE.Group[] = [];
  for (const sx of [-1, 1]) for (const z of [-1.05, 1.05]) {
    const w = new THREE.Group(); w.position.set(sx * 0.6, WHEEL_R, z);
    add(new THREE.CylinderGeometry(WHEEL_R, WHEEL_R, 0.22, 20).rotateZ(Math.PI / 2), black, 0, 0, 0, w);
    add(new THREE.CylinderGeometry(0.17, 0.17, 0.235, 12).rotateZ(Math.PI / 2), rim, 0, 0, 0, w);
    car.add(w); wheels.push(w);
  }
  car.position.set(LANE_X, GROUND_Y, ROAD_Z);

  /** t in seconds. The slab has no road beyond its edge: the car fades in at the front edge and out at z -7. */
  function update(t: number) {
    const c = t % CYCLE;
    let z: number;
    if (c < IN) z = ROAD_Z + (STOP_Z - ROAD_Z) * (1 - (1 - c / IN) ** 2);
    else if (c < IN + WAIT) z = STOP_Z;
    else if (c < IN + WAIT + OUT) z = STOP_Z + (END_Z - STOP_Z) * ((c - IN - WAIT) / OUT) ** 2;
    else z = END_Z;
    const a = c >= IN + WAIT + OUT ? 0 : clamp01(Math.min((ROAD_Z - z) / FADE_LEN, (z - END_Z) / FADE_LEN));
    car.visible = a > 0;
    for (const m of mats) { m.transparent = a < 1; m.opacity = a; }
    car.position.z = z;
    for (const w of wheels) w.rotation.x = z / WHEEL_R; // -z travel turns the wheel top towards -z
  }
  update(0);
  return { group: car, update };
}
