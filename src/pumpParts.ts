import * as THREE from 'three';
import { canvasTex } from './textures';

/** Replaces blocky nozzle and straight-cylinder hose meshes with sculpted geometry. */
export function applyPumpPartGeometry(mesh: THREE.Mesh, partStyle: string): void {
  if (partStyle === 'fuel-nozzle') {
    const s = new THREE.Shape();
    s.moveTo(-0.03, -0.14); s.lineTo(0.02, -0.14); s.lineTo(0.05, 0.02);
    s.lineTo(0.13, 0.08); s.lineTo(0.14, 0.12); s.lineTo(0.04, 0.14);
    s.lineTo(-0.06, 0.09); s.lineTo(-0.08, -0.02); s.closePath();
    const geo = new THREE.ExtrudeGeometry(s, {
      depth: 0.055, bevelEnabled: true, bevelThickness: 0.008, bevelSize: 0.008, bevelSegments: 2, curveSegments: 6,
    });
    geo.translate(0, 0, -0.0275);
    mesh.geometry = geo;
    return;
  }
  if (partStyle === 'curved-hose') {
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-0.02, 0.26, 0), new THREE.Vector3(0.09, 0.08, 0),
      new THREE.Vector3(0.11, -0.18, 0), new THREE.Vector3(0.02, -0.32, 0),
      new THREE.Vector3(-0.07, -0.20, 0), new THREE.Vector3(-0.04, -0.02, 0),
    ]);
    mesh.geometry = new THREE.TubeGeometry(curve, 20, 0.024, 8, false);
  }
}

/** Top header sign: diagonal teal/white split, Caltex roundel, with TECHRON, and pump number. */
export function pumpHeadNumberTex(n: number): THREE.CanvasTexture {
  const t = canvasTex(1024, 353, (g) => {
    g.fillStyle = '#f4f4f2'; g.fillRect(0, 0, 1024, 353);
    g.fillStyle = '#0b5563'; g.beginPath(); g.moveTo(0, 0); g.lineTo(540, 0); g.lineTo(180, 353); g.lineTo(0, 353); g.fill();
    g.beginPath(); g.moveTo(555, 0); g.lineTo(1024, 0); g.lineTo(1024, 52); g.lineTo(510, 52); g.fill();
    g.strokeStyle = '#ffffff'; g.lineWidth = 6; g.beginPath(); g.moveTo(545, 0); g.lineTo(185, 353); g.stroke();
    g.fillStyle = '#1b5299'; g.textAlign = 'left'; g.textBaseline = 'middle';
    g.font = 'bold 34px Arial, sans-serif'; g.fillText('with', 540, 140);
    g.font = 'bold 82px Arial, sans-serif'; g.fillText('TECHRON', 495, 205);
    g.fillStyle = '#d8372b'; g.textAlign = 'center'; g.font = 'bold 64px Arial, sans-serif'; g.fillText(String(n), 945, 115);
    g.strokeStyle = '#c8cdd2'; g.lineWidth = 10; g.strokeRect(5, 5, 1014, 343);
  });
  const img = new Image();
  img.onload = () => { (t.image as HTMLCanvasElement).getContext('2d')!.drawImage(img, 205, 72, 210, 210); t.needsUpdate = true; };
  img.src = 'decals/caltex_roundel.png';
  return t;
}

function pumpBodyFrontTex(): THREE.CanvasTexture {
  const t = canvasTex(512, 640, (g) => {
    const grad = g.createLinearGradient(0, 76, 0, 600);
    grad.addColorStop(0, '#e52521'); grad.addColorStop(0.55, '#ff7350'); grad.addColorStop(1, '#e52521');
    g.fillStyle = grad; g.fillRect(0, 0, 512, 640);
    g.fillStyle = '#1d1d1d'; g.fillRect(0, 608, 512, 32);
    const cols = ['#1b8a3d', '#f2c230', '#b31919'], titles = ['Diesel', 'Premium 95', 'Platinum 97'], subs = ['with Techron D', 'with Techron', 'with Techron'], octs = ['B10', '95', '97'];
    for (let i = 0; i < 3; i++) {
      const x = i * 170;
      g.fillStyle = cols[i]; g.fillRect(x, 0, 172, 76);
      g.fillStyle = i === 1 ? '#111' : '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.font = 'bold 26px Arial, sans-serif'; g.fillText(titles[i], x + 85, 30);
      g.font = 'italic 15px Arial, sans-serif'; g.fillText(subs[i], x + 85, 56);
      g.fillStyle = '#f2c230'; g.fillRect(x + 124, 92, 36, 26);
      g.strokeStyle = '#111'; g.lineWidth = 2; g.strokeRect(x + 124, 92, 36, 26);
      g.fillStyle = '#111'; g.font = 'bold 16px Arial, sans-serif'; g.fillText(octs[i], x + 142, 106);
    }
    g.fillStyle = '#ffffff'; g.beginPath(); g.moveTo(310, 608); g.quadraticCurveTo(410, 520, 512, 470); g.lineTo(512, 608); g.fill();
    g.fillStyle = '#111'; g.font = 'bold 22px Arial, sans-serif'; g.textAlign = 'right'; g.fillText('TECHRON', 494, 588);
  });
  const img = new Image();
  img.onload = () => { (t.image as HTMLCanvasElement).getContext('2d')!.drawImage(img, -48, 430, 170, 170); t.needsUpdate = true; };
  img.src = 'decals/caltex_roundel.png';
  return t;
}

function pumpMeterPanelTex(): THREE.CanvasTexture {
  return canvasTex(512, 256, (g) => {
    g.fillStyle = '#22252a'; g.fillRect(0, 0, 512, 256);
    g.fillStyle = '#c8cdd2'; g.fillRect(0, 0, 512, 24);
    g.fillStyle = '#111'; g.fillRect(34, 48, 92, 120);
    g.fillStyle = '#707880';
    for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) g.fillRect(46 + c * 22, 92 + r * 18, 16, 12);
    g.fillStyle = '#111'; g.fillRect(190, 44, 150, 96);
    g.fillStyle = '#f2c230'; g.font = 'bold 20px monospace'; g.textAlign = 'right';
    g.fillText('85.00', 330, 78); g.fillStyle = '#ff6a4d'; g.fillText('41.46', 330, 118);
    const btns = ['#1b8a3d', '#f2c230', '#d8372b'];
    for (let i = 0; i < 3; i++) {
      g.fillStyle = btns[i]; g.fillRect(194 + i * 50, 154, 40, 44);
      g.strokeStyle = '#fff'; g.lineWidth = 2; g.strokeRect(194 + i * 50, 154, 40, 44);
    }
  });
}

function pumpTopperTex(): THREE.CanvasTexture {
  const t = canvasTex(512, 220, (g) => {
    g.fillStyle = '#2b2e33'; g.fillRect(0, 0, 512, 220);
    const grad = g.createLinearGradient(0, 16, 0, 204);
    grad.addColorStop(0, '#7ec8f2'); grad.addColorStop(1, '#5bb3e8');
    g.fillStyle = grad; g.fillRect(16, 16, 480, 188);
    g.fillStyle = '#1b3b5a'; g.font = 'bold 20px Arial, sans-serif'; g.textAlign = 'center'; g.fillText('CALTEX', 74, 174);
    g.font = 'italic bold 26px Arial, sans-serif'; g.textAlign = 'left'; g.fillText('BUSINESS SOLUTIONS', 146, 116, 336);
    g.fillStyle = '#d8372b'; g.beginPath(); g.moveTo(148, 134); g.lineTo(220, 134); g.lineTo(148, 154); g.fill();
  });
  const img = new Image();
  img.onload = () => { (t.image as HTMLCanvasElement).getContext('2d')!.drawImage(img, 34, 52, 80, 80); t.needsUpdate = true; };
  img.src = 'decals/caltex_roundel.png';
  return t;
}

function pumpCabinetPosterTex(): THREE.CanvasTexture {
  return canvasTex(512, 768, (g) => {
    const sky = g.createLinearGradient(0, 0, 0, 520);
    sky.addColorStop(0, '#56a3d9'); sky.addColorStop(1, '#d8ecf8');
    g.fillStyle = sky; g.fillRect(0, 0, 512, 520);
    g.fillStyle = '#fff'; g.textAlign = 'center'; g.font = 'italic bold 42px Arial, sans-serif';
    g.fillText("It's all about you.", 256, 180);
    g.font = 'italic 28px Arial, sans-serif'; g.fillText('For you. With You.', 256, 232);
    g.fillStyle = '#d8372b'; g.fillRect(0, 456, 512, 64);
    g.fillStyle = '#fff'; g.font = 'bold 24px Arial, sans-serif'; g.fillText('ENJOY THE JOURNEY  CALTEX', 256, 496);
    const bot = g.createRadialGradient(256, 690, 20, 256, 690, 240);
    bot.addColorStop(0, '#ff8855'); bot.addColorStop(1, '#e52521');
    g.fillStyle = bot; g.fillRect(0, 520, 512, 248);
  });
}

/** Applies sculpted nozzle/hose geometry (all modes) and 3-nozzle Caltex Techron details (normal mode). */
export function customizePumps(model: THREE.Object3D, gate: boolean): void {
  model.traverse((o: any) => {
    const ps = o.userData?.sculptComponent?.geometryDescriptor?.partStyle;
    if (o.isMesh && ps) applyPumpPartGeometry(o, ps);
  });
  if (gate) return;

  const meshById = (id: string): any => {
    let hit: any = null;
    model.traverse((o: any) => { if (!hit && o.isMesh && o.userData?.sculptComponent?.id === id) hit = o; });
    return hit;
  };
  const groupById = (id: string): any => {
    let hit: any = null;
    model.traverse((o: any) => { if (!hit && !o.isMesh && o.userData?.sculptComponent?.id === id) hit = o; });
    return hit;
  };
  const bodyFaceMat = new THREE.MeshStandardMaterial({ map: pumpBodyFrontTex(), roughness: 0.45 });
  const meterMat = new THREE.MeshStandardMaterial({ map: pumpMeterPanelTex(), roughness: 0.45 });
  const topperMat = new THREE.MeshStandardMaterial({ map: pumpTopperTex(), roughness: 0.45 });
  const cabPosterMat = new THREE.MeshStandardMaterial({ map: pumpCabinetPosterTex(), roughness: 0.5, polygonOffset: true, polygonOffsetFactor: -2 });
  const silverMat = new THREE.MeshStandardMaterial({ color: 0xc4c9ce, roughness: 0.35, metalness: 0.3 });
  const bayInnerMat = new THREE.MeshStandardMaterial({ color: 0x26292e, roughness: 0.7 });
  const hoseMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.8 });
  const nozzleMats = [0x1b8a3d, 0xf2c230, 0xd8372b].map((c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.4 }));
  const bayGeo = new THREE.BoxGeometry(0.53, 0.36, 0.13);
  const bayInGeo = new THREE.BoxGeometry(0.54, 0.31, 0.09);
  const nozGeo = new THREE.BoxGeometry(0.05, 0.19, 0.045);
  const hoseGeo = new THREE.CylinderGeometry(0.014, 0.014, 0.16, 8);
  const topperGeo = new THREE.BoxGeometry(0.06, 0.24, 0.44);
  const cabGeo = new THREE.PlaneGeometry(0.32, 0.62);
  const signBackGeo = new THREE.PlaneGeometry(1.38, 0.43);

  for (let n = 1; n <= 4; n++) {
    const pump = groupById(`pump-${n}`);
    const pumpMesh = meshById(`pump-${n}`);
    if (!pump || !pumpMesh) continue;
    const hiddenMat = new THREE.MeshBasicMaterial({ visible: false });
    const pm = pumpMesh.material;
    pumpMesh.material = [bodyFaceMat, bodyFaceMat, pm, pm, pm, pm];

    const panelGrp = groupById(`pump-panel-${n}`);
    const panelMesh = meshById(`pump-panel-${n}`);
    if (panelGrp && panelMesh) {
      panelMesh.scale.y = 0.36 / 0.7;
      panelGrp.position.y = 0.63;
      panelMesh.material = [meterMat, meterMat, panelMesh.material, panelMesh.material, panelMesh.material, panelMesh.material];
    }
    const screenGrp = groupById(`pump-screen-${n}`);
    if (screenGrp) { screenGrp.scale.set(0.05, 0.05, 0.05); screenGrp.position.set(0, 0, 0); }

    for (const s of ['a', 'b']) {
      const pilGrp = groupById(`pump-pillar-${n}${s}`);
      const pilMesh = meshById(`pump-pillar-${n}${s}`);
      if (pilGrp && pilMesh) { pilGrp.position.x = 0; pilMesh.scale.x = 0.48 / 0.22; pilMesh.material = silverMat; }
      for (const pfx of ['pump-nozzle-', 'pump-hose-']) {
        const old = groupById(`${pfx}${n}${s}`);
        if (old) { old.scale.set(0.05, 0.05, 0.05); old.position.set(0, 0.1, 0); }
      }
    }

    const topper = new THREE.Mesh(topperGeo, [topperMat, topperMat, silverMat, silverMat, silverMat, silverMat]);
    topper.name = `pump-topper-${n}`; topper.position.set(0, 0.94, 0); topper.castShadow = false;
    pump.add(topper);

    [-0.21, 0, 0.21].forEach((zSlot, idx) => {
      const bay = new THREE.Mesh(bayGeo, silverMat);
      bay.name = `pump-bay-${n}`; bay.position.set(0, -0.02, zSlot); bay.castShadow = false;
      const inner = new THREE.Mesh(bayInGeo, bayInnerMat);
      inner.position.set(0, -0.02, zSlot); inner.castShadow = false;
      pump.add(bay, inner);
      for (const sideX of [-1, 1]) {
        const noz = new THREE.Mesh(nozGeo, nozzleMats[sideX < 0 ? idx : 2 - idx]);
        noz.name = `pump-front-nozzle-${n}-${idx}`;
        noz.position.set(sideX * 0.27, 0.01, zSlot); noz.rotation.z = sideX * 0.25; noz.castShadow = false;
        const h = new THREE.Mesh(hoseGeo, hoseMat);
        h.position.set(sideX * 0.27, -0.10, zSlot); h.castShadow = false;
        pump.add(noz, h);
      }
    });

    const headMat = new THREE.MeshStandardMaterial({ map: pumpHeadNumberTex(n), roughness: 0.45 });
    const signMesh = meshById(`pump-sign-${n}`);
    if (signMesh) signMesh.material = [hiddenMat, headMat, hiddenMat, hiddenMat, hiddenMat, hiddenMat];
    const headMesh = meshById(`pump-head-${n}`);
    if (headMesh) {
      headMesh.material = [headMat, silverMat, silverMat, silverMat, silverMat, silverMat];
      const back = new THREE.Mesh(signBackGeo, headMat);
      back.position.set(0.305, 0, 0); back.rotation.y = Math.PI / 2; back.castShadow = false;
      headMesh.add(back);
    }

    const cabGrp = groupById(`pump-cabinet-${n}`);
    const cabMesh = meshById(`pump-cabinet-${n}`);
    if (cabGrp && cabMesh) {
      cabGrp.position.set(0, -0.08, -0.88);
      for (const sideX of [-1, 1]) {
        const poster = new THREE.Mesh(cabGeo, cabPosterMat);
        poster.position.set(sideX * 0.205, 0, 0); poster.rotation.y = sideX * Math.PI / 2; poster.castShadow = false;
        cabMesh.add(poster);
      }
    }
    const cabTopGrp = groupById(`pump-cabinet-top-${n}`);
    const cabTopMesh = meshById(`pump-cabinet-top-${n}`);
    if (cabTopGrp && cabTopMesh) {
      cabTopMesh.scale.y = 0.06 / 0.25; cabTopGrp.position.y = 0.36; cabTopMesh.material = silverMat;
    }
  }
}
