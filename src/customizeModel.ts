import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';
import spec from '../object-sculpt-spec.json';
import { customizePumps } from './pumpParts';
import {
  canvasTex,
  decalTex,
  energyLinesTex,
  glassTex,
  martFaceTex,
  martText,
  numberTex,
  posterTex,
  pumpSignTex,
  pylonTex,
  recycleTex,
  soffitGlowTex,
  soffitTex,
  soilTex,
  stallTex,
  standeeTex,
  stripeTex,
} from './textures';

export type CustomizedModelInfo = {
  baseColors: Map<THREE.MeshStandardMaterial, THREE.Color>;
  orangeSpec: Map<THREE.MeshStandardMaterial, string>;
  waveFlags: (t: number) => void;
  meshById: (id: string) => any;
  partById: (id: string) => THREE.Object3D | null;
};

const DECAL_FLIP = { wordmark: false, roundelRot: 0 };
const NO_SHADOW = /^(pump-(nozzle|hose|screen|sign|poster|standee)|bin-\w+-\d-wheels|flagpole-\d-(base|finial)|mart-(mullion|rail|sign|door)|column-disc|agave|wheel-stop|kerb|canopy-wordmark|flag-)/;
const CONTACT = /^(pylon-sign|pump-island-\d|bin-\w+-\d|tree-\d-trunk|bush-\d|mart|flagpole-\d)$/;

/** Merge consecutive faces sharing a material and drop invisible groups. */
function mergeGroups(mesh: THREE.Mesh): void {
  const mats = mesh.material as THREE.Material[];
  const g = mesh.geometry.clone();
  const kept: THREE.Material[] = [];
  const out: { start: number; count: number; materialIndex: number }[] = [];
  for (const grp of g.groups) {
    const m = mats[grp.materialIndex ?? 0];
    if (!m.visible) continue;
    let idx = kept.indexOf(m);
    if (idx < 0) { idx = kept.length; kept.push(m); }
    const last = out[out.length - 1];
    if (last && last.materialIndex === idx && last.start + last.count === grp.start) last.count += grp.count;
    else out.push({ start: grp.start, count: grp.count, materialIndex: idx });
  }
  g.clearGroups();
  out.forEach((o) => g.addGroup(o.start, o.count, o.materialIndex));
  mesh.geometry = g;
  mesh.material = kept;
}

/**
 * Applies rounded corners, stadium pump islands, 3D CALTEX wordmark, procedural textures,
 * shadows, clay mode, and waving flags to the generated station model.
 */
export async function customizeModel(
  model: THREE.Object3D,
  scene: THREE.Scene,
  gate: boolean,
  clay: boolean,
  getWind: () => number,
): Promise<CustomizedModelInfo> {
  // Collected before the overrides below turn single materials into arrays.
  const baseColors = new Map<THREE.MeshStandardMaterial, THREE.Color>();
  const orangeSpec = new Map<THREE.MeshStandardMaterial, string>();
  model.traverse((o: any) => {
    if (o.isMesh && /orange/.test(o.userData?.sculptComponent?.material ?? '') && o.material?.color) {
      baseColors.set(o.material, o.material.color.clone());
      orangeSpec.set(o.material, o.userData.sculptComponent.material);
    }
  });

  const hidden = new THREE.MeshBasicMaterial({ visible: false });
  const decalMat = (map: THREE.Texture) =>
    new THREE.MeshStandardMaterial({ map, transparent: true, alphaTest: 0.05, roughness: 0.55, polygonOffset: true, polygonOffsetFactor: -2 });
  const onNegX = (m: THREE.Material) => [hidden, m, hidden, hidden, hidden, hidden];
  const signTex = pumpSignTex();
  const DECALS: Record<string, () => THREE.Material[]> = {
    'canopy-wordmark': () => [hidden, hidden, hidden, hidden, hidden, hidden],
    'mart-sign': () => onNegX(decalMat(martText())),
    'flag-malaysia': () => [hidden, hidden, hidden, hidden, decalMat(decalTex('decals/flag_malaysia.png')), decalMat(decalTex('decals/flag_malaysia.png', true))],
    'flag-johor': () => [hidden, hidden, hidden, hidden, decalMat(decalTex('decals/flag_johor.png')), decalMat(decalTex('decals/flag_johor.png', true))],
  };

  model.updateMatrixWorld(true);
  const meshById = (id: string): any => {
    let hit: any = null;
    model.traverse((o: any) => { if (!hit && o.isMesh && o.userData?.sculptComponent?.id === id) hit = o; });
    return hit;
  };
  const partById = (id: string): THREE.Object3D | null => {
    let hit: THREE.Object3D | null = null;
    model.traverse((o: any) => { if (!hit && !o.isMesh && o.userData?.sculptComponent?.id === id) hit = o; });
    return hit;
  };
  const worldBox = (o: THREE.Object3D) => new THREE.Box3().setFromObject(o);

  const bevelOf = new Map<string, number>();
  for (const c of (spec as any).componentTree) {
    const r = c.geometryDescriptor?.edgeTreatment?.bevelRadius ?? 0;
    if (c.primitive === 'box' && r > 0) bevelOf.set(c.id, r);
  }
  model.traverse((o: any) => {
    const r = bevelOf.get(o.userData?.sculptComponent?.id);
    if (!o.isMesh || !r) return;
    o.geometry.computeBoundingBox();
    const s = o.geometry.boundingBox.getSize(new THREE.Vector3());
    o.geometry = new RoundedBoxGeometry(s.x, s.y, s.z, 2, r);
  });

  model.traverse((o: any) => {
    if (!o.isMesh || o.userData?.sculptComponent?.geometryDescriptor?.planShape !== 'stadium') return;
    o.geometry.computeBoundingBox();
    const b = o.geometry.boundingBox.getSize(new THREE.Vector3());
    const r = b.x / 2, h = b.z / 2 - r, shape = new THREE.Shape();
    shape.moveTo(r, -h); shape.lineTo(r, h); shape.absarc(0, h, r, 0, Math.PI, false);
    shape.lineTo(-r, -h); shape.absarc(0, -h, r, Math.PI, Math.PI * 2, false);
    const geo = new THREE.ExtrudeGeometry(shape, { depth: b.y, bevelEnabled: false, curveSegments: 12 });
    geo.rotateX(-Math.PI / 2); geo.translate(0, -b.y / 2, 0);
    o.geometry = geo;
  });

  const wordmarkBox = meshById('canopy-wordmark');
  if (wordmarkBox) {
    const svg = await new SVGLoader().loadAsync('decals/caltex_wordmark.svg');
    const geo = new THREE.ExtrudeGeometry(svg.paths.flatMap((p) => SVGLoader.createShapes(p)), { depth: 4.5, bevelEnabled: true, bevelThickness: 0.6, bevelSize: 0.4, bevelSegments: 1, curveSegments: 4 });
    geo.computeBoundingBox();
    const bb = geo.boundingBox!;
    geo.translate(-(bb.min.x + bb.max.x) / 2, -(bb.min.y + bb.max.y) / 2, 0);
    const k = 2.4 / (bb.max.x - bb.min.x);
    const letters = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5 }));
    letters.scale.set(k, -k, k);
    letters.rotation.y = -Math.PI / 2;
    wordmarkBox.geometry.computeBoundingBox();
    letters.position.x = wordmarkBox.geometry.boundingBox.min.x + 0.6 * k;
    wordmarkBox.add(letters);
  }

  model.traverse((o: any) => {
    const id: string | undefined = o.userData?.sculptComponent?.id;
    if (!o.isMesh || !id) return;
    if (id === 'roundel-logo') {
      const cap = new THREE.MeshStandardMaterial({ map: decalTex('decals/caltex_roundel.png', false, DECAL_FLIP.roundelRot), transparent: true, roughness: 0.5 });
      o.material = [new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5 }), cap, new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5 })];
    } else if (DECALS[id]) {
      o.material = DECALS[id]();
    } else if (/^bin-(blue|green)-\d$/.test(id)) {
      o.geometry = o.geometry.clone(); o.geometry.computeBoundingBox();
      const bp = o.geometry.attributes.position, minY = o.geometry.boundingBox.min.y;
      for (let i = 0; i < bp.count; i++) {
        const y = bp.getY(i);
        if (y < 0) { const f = 0.85 + 0.15 * (y - minY) / (0 - minY); bp.setX(i, bp.getX(i) * f); bp.setZ(i, bp.getZ(i) * f); }
      }
      o.geometry.computeVertexNormals(); o.geometry.computeBoundingBox();
      o.material = [o.material, o.material, o.material, o.material, o.material, new THREE.MeshStandardMaterial({ map: recycleTex('#' + o.material.color.getHexString()), roughness: o.material.roughness })];
    } else if (id === 'pylon-sign') {
      const face = new THREE.MeshStandardMaterial({ map: pylonTex(), roughness: 0.5 }), teal = new THREE.MeshStandardMaterial({ color: 0x0b6b7c, roughness: 0.5 });
      o.material = [face, face, teal, teal, teal, teal];
    } else if (/^pump-poster-/.test(id)) {
      o.material = onNegX(new THREE.MeshStandardMaterial({ map: posterTex(), roughness: 0.6 }));
    } else if (id === 'pump-standee-3') {
      o.material = onNegX(new THREE.MeshStandardMaterial({ map: standeeTex(), roughness: 0.6 }));
    } else if (/^pump-sign-/.test(id)) {
      o.material = onNegX(new THREE.MeshStandardMaterial({ map: signTex, roughness: 0.5 }));
    } else if (id === 'soffit') {
      o.material = new THREE.MeshStandardMaterial({ map: soffitTex(gate), emissiveMap: soffitGlowTex(gate), emissive: 0xffffff, emissiveIntensity: gate ? 0.6 : 1.5, roughness: 0.8 });
    } else if (id === 'kerb-mart' || /^wheel-stop-/.test(id)) {
      const len = id === 'kerb-mart' ? 8 : 1.1;
      const side = new THREE.MeshStandardMaterial({ map: stripeTex(len, false), roughness: 0.7 });
      const top = new THREE.MeshStandardMaterial({ map: stripeTex(len, id === 'kerb-mart'), roughness: 0.7 });
      o.material = [side, side, top, side, side, side];
    } else if (/^column-disc-/.test(id)) {
      const cap = new THREE.MeshStandardMaterial({ map: numberTex(Number(id.slice(-1))), roughness: 0.5 });
      o.material = [new THREE.MeshStandardMaterial({ color: 0xffffff }), cap, cap];
    } else if (id === 'mart-window') {
      o.material = [o.material, new THREE.MeshStandardMaterial({ map: glassTex('#' + o.material.color.getHexString()), roughness: o.material.roughness }), o.material, o.material, o.material, o.material];
    } else if (id === 'canopy') {
      const roof = o.material.clone(); roof.color.set(0xf3eee8);
      o.material = [o.material, o.material, roof, o.material, o.material, o.material];
      const lines = new THREE.Mesh(new THREE.PlaneGeometry(1.9, 0.75).rotateY(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: energyLinesTex(), transparent: true, alphaTest: 0.05, roughness: 0.6, polygonOffset: true, polygonOffsetFactor: -2 }));
      lines.name = 'energy-lines'; lines.castShadow = false; lines.position.set(-5.755, -0.075, -5.85); o.add(lines);
    } else if (/^pump-head-/.test(id)) {
      o.material = [new THREE.MeshStandardMaterial({ map: signTex, roughness: 0.5 }), o.material, o.material, o.material, o.material, o.material];
    } else if (id === 'mart') {
      const mb = worldBox(o), white = '#' + o.material.color.getHexString(), h = mb.max.y - mb.min.y;
      const mk = (wU: number, door: boolean) => new THREE.MeshStandardMaterial({ map: martFaceTex(wU, h, white, door), roughness: o.material.roughness });
      const side = mk(mb.max.x - mb.min.x, false);
      o.material = [mk(mb.max.z - mb.min.z, true), o.material, o.material, o.material, side, side];
    } else if (id === 'base-slab') {
      const sb = worldBox(o), mk = (wU: number, seed: number) => new THREE.MeshStandardMaterial({ map: soilTex(wU, sb.max.y - sb.min.y, seed), roughness: 0.95 });
      const sideX = mk(sb.max.z - sb.min.z, 11), sideZ = mk(sb.max.x - sb.min.x, 23);
      o.material = [sideX, sideX, o.material, o.material, sideZ, sideZ];
    } else if (id === 'concrete-top') {
      const pumps = [1, 2, 3, 4].map((n) => worldBox(meshById('pump-' + n)).getCenter(new THREE.Vector3()));
      const top = o.material.clone(); top.map = stallTex(worldBox(o), pumps, '#' + o.material.color.getHexString()); top.color.set(0xffffff);
      o.material = [o.material, o.material, top, o.material, o.material, o.material];
    }
  });

  customizePumps(model, gate);
  model.traverse((o: any) => { if (o.isMesh && Array.isArray(o.material)) mergeGroups(o); });
  model.traverse((o: any) => { if (o.isMesh && NO_SHADOW.test(o.userData?.sculptComponent?.id ?? '')) o.castShadow = false; });

  if (!gate) {
    model.traverse((o: any) => { if (o.isMesh) ([] as any[]).concat(o.material).forEach((m) => { if (m.clearcoat) m.clearcoat = 0; }); });
    const slab = worldBox(meshById('base-slab'));
    const catcher = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.ShadowMaterial({ opacity: 0.18 }));
    catcher.name = 'shadow-catcher'; catcher.rotation.x = -Math.PI / 2; catcher.position.y = slab.min.y - 0.001; catcher.receiveShadow = true;
    scene.add(catcher);

    const spots: { c: THREE.Vector3; sx: number; sz: number }[] = [];
    const spot = (b: THREE.Box3, y: number) => spots.push({ c: new THREE.Vector3((b.min.x + b.max.x) / 2, y, (b.min.z + b.max.z) / 2), sx: (b.max.x - b.min.x) * 1.3, sz: (b.max.z - b.min.z) * 1.3 });
    model.traverse((o: any) => { if (o.isMesh && CONTACT.test(o.userData?.sculptComponent?.id ?? '')) { const b = worldBox(o); spot(b, b.min.y + 0.015); } });
    spot(slab, slab.min.y + 0.005);
    const blob = canvasTex(128, 128, (g) => {
      const r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
      r.addColorStop(0, 'rgba(0,0,0,0.35)'); r.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = r; g.fillRect(0, 0, 128, 128);
    });
    const contact = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: blob, transparent: true, depthWrite: false }), spots.length);
    contact.name = 'contact-shadows';
    spots.forEach((s, i) => contact.setMatrixAt(i, new THREE.Matrix4().compose(s.c, new THREE.Quaternion(), new THREE.Vector3(s.sx, 1, s.sz))));
    scene.add(contact);
  }

  if (clay) {
    const clayMat = new THREE.MeshStandardMaterial({ color: 0xb8b8b8, roughness: 0.9 });
    model.traverse((o: any) => { if (o.isMesh) o.material = clayMat; });
  }

  const flags: { geo: THREE.BufferGeometry; orig: Float32Array; x0: number }[] = [];
  if (!gate) {
    model.traverse((o: any) => {
      if (!o.isMesh || !/^flag-/.test(o.userData?.sculptComponent?.id ?? '')) return;
      o.geometry.computeBoundingBox();
      flags.push({ geo: o.geometry, orig: Float32Array.from(o.geometry.attributes.position.array as Float32Array), x0: o.geometry.boundingBox.min.x });
    });
  }
  function waveFlags(t: number) {
    const wind = getWind();
    for (const f of flags) {
      const pos = f.geo.attributes.position as THREE.BufferAttribute;
      for (let i = 0; i < pos.count; i++) {
        const x = f.orig[3 * i];
        pos.setZ(i, f.orig[3 * i + 2] + Math.sin(x * 6 + t * 3) * wind * (x - f.x0));
      }
      pos.needsUpdate = true;
      f.geo.computeVertexNormals();
    }
  }

  return { baseColors, orangeSpec, waveFlags, meshById, partById };
}
