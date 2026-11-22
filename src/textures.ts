import * as THREE from 'three';

export function decalTex(url: string, flip = false, rot = 0): THREE.Texture {
  const tex = new THREE.TextureLoader().load(url);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  if (flip) { tex.wrapS = THREE.RepeatWrapping; tex.repeat.x = -1; }
  if (rot) { tex.center.set(0.5, 0.5); tex.rotation = rot; }
  return tex;
}

export function canvasTex(w: number, h: number, draw: (g: CanvasRenderingContext2D) => void): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  draw(c.getContext('2d')!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

export function martText(): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 160;
  const g = c.getContext('2d')!;
  g.fillStyle = '#fff';
  g.font = 'bold 120px Arial, sans-serif';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText('Mart', 256, 84);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Pump head sign: the real roundel PNG plus an approximate "Techron" panel. */
export function pumpSignTex(): THREE.CanvasTexture {
  const t = canvasTex(1024, 353, (g) => {
    g.fillStyle = '#12505e'; g.fillRect(0, 0, 1024, 353);
    g.fillStyle = '#f4f4f2'; g.beginPath(); g.moveTo(0, 0); g.lineTo(400, 0); g.lineTo(330, 353); g.lineTo(0, 353); g.fill();
    g.fillStyle = '#fff'; g.font = 'italic bold 120px Arial, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('Techron', 710, 180);
  });
  const img = new Image();
  img.onload = () => { (t.image as HTMLCanvasElement).getContext('2d')!.drawImage(img, 20, 20, 313, 313); t.needsUpdate = true; };
  img.src = 'decals/caltex_roundel.png';
  return t;
}

/** Black/yellow kerb stripes. Side faces stripe along u, the top face along v. */
export function stripeTex(len: number, top: boolean): THREE.CanvasTexture {
  const t = canvasTex(128, 32, (g) => { g.fillStyle = '#f2c230'; g.fillRect(0, 0, 128, 32); g.fillStyle = '#1d1d1d'; g.fillRect(52, 0, 24, 32); });
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(len / 0.6, 1);
  if (top) { t.center.set(0.5, 0.5); t.rotation = Math.PI / 2; }
  return t;
}

/** Soffit underside: white field with round downlights. */
export function soffitTex(gate: boolean): THREE.CanvasTexture {
  return canvasTex(1024, 1024, (g) => {
    g.fillStyle = '#f4f1ec'; g.fillRect(0, 0, 1024, 1024);
    const nx = gate ? 4 : 3, ny = gate ? 6 : 4;
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
      const x = (i + 0.5) * 1024 / nx, y = (j + 0.5) * 1024 / ny;
      g.fillStyle = '#b8b4ae'; g.beginPath(); g.arc(x, y, 30, 0, 7); g.fill();
      g.fillStyle = '#fffdf6'; g.beginPath(); g.arc(x, y, 24, 0, 7); g.fill();
    }
  });
}

/** Emissive map for soffit underside. */
export function soffitGlowTex(gate: boolean): THREE.CanvasTexture {
  return canvasTex(1024, 1024, (g) => {
    g.fillStyle = gate ? '#000' : '#ffffff'; g.fillRect(0, 0, 1024, 1024); g.fillStyle = '#fff';
    const nx = gate ? 4 : 3, ny = gate ? 6 : 4;
    for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
      g.beginPath(); g.arc((i + 0.5) * 1024 / nx, (j + 0.5) * 1024 / ny, 24, 0, 7); g.fill();
    }
  });
}

export function numberTex(n: number): THREE.CanvasTexture {
  return canvasTex(128, 128, (g) => {
    g.fillStyle = '#fff'; g.beginPath(); g.arc(64, 64, 62, 0, 7); g.fill();
    g.strokeStyle = '#333'; g.lineWidth = 8; g.beginPath(); g.arc(64, 64, 54, 0, 7); g.stroke();
    g.fillStyle = '#222'; g.font = 'bold 72px Arial, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(String(n), 64, 68);
  });
}

export function posterTex(): THREE.CanvasTexture {
  return canvasTex(128, 576, (g) => {
    const sky = g.createLinearGradient(0, 0, 0, 576); sky.addColorStop(0, '#7cc4f0'); sky.addColorStop(1, '#e2f3fb');
    g.fillStyle = sky; g.fillRect(0, 0, 128, 576);
    g.fillStyle = '#f26b26'; g.fillRect(0, 380, 128, 196);
    g.fillStyle = '#fff'; g.beginPath(); g.arc(64, 150, 30, 0, 7); g.fill();
  });
}

export function standeeTex(): THREE.CanvasTexture {
  return canvasTex(288, 640, (g) => {
    g.fillStyle = '#fafaf8'; g.fillRect(0, 0, 288, 640);
    g.fillStyle = '#111'; g.font = 'bold 64px Arial, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('Fuel up', 144, 200);
    g.fillStyle = '#f26b26'; g.fillRect(48, 330, 90, 90); g.fillStyle = '#12505e'; g.fillRect(150, 330, 90, 90);
    g.fillStyle = '#d8372b'; g.fillRect(48, 432, 192, 40);
  });
}

export function recycleTex(bg: string): THREE.CanvasTexture {
  return canvasTex(128, 128, (g) => {
    g.fillStyle = bg; g.fillRect(0, 0, 128, 128); g.translate(64, 70); g.fillStyle = '#fff';
    for (let i = 0; i < 3; i++) {
      g.rotate(2.094); g.beginPath(); g.moveTo(-8, -34); g.lineTo(16, -34); g.lineTo(16, -42); g.lineTo(34, -24); g.lineTo(16, -6); g.lineTo(16, -14); g.lineTo(-8, -14); g.closePath(); g.fill();
    }
  });
}

/** Caltex pylon sign face: roundel, CALTEX, Techron, Havoline, Car Wash, white/red foot. */
export function pylonTex(): THREE.CanvasTexture {
  const W = 450, H = 1320, cx = W / 2;
  const t = canvasTex(W, H, (g) => {
    g.fillStyle = '#0b6b7c'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.font = 'bold 100px Arial, sans-serif'; g.fillText('CALTEX', cx, 520);
    g.font = 'italic bold 52px Arial, sans-serif'; g.fillText('with Techron', cx, 600);
    g.fillStyle = '#d8372b'; g.fillRect(30, 650, W - 60, 90);
    g.fillStyle = '#f2c230'; g.font = 'italic bold 64px Arial, sans-serif'; g.fillText('Havoline', cx, 695);
    g.fillStyle = '#fff'; g.font = 'bold 56px Arial, sans-serif'; g.fillText('Car Wash', cx, 810);
    g.fillStyle = '#d8372b'; g.beginPath(); g.moveTo(0, 960); g.lineTo(W, 1230); g.lineTo(W, 1290); g.lineTo(0, 1020); g.fill();
    g.fillStyle = '#eceae6'; g.beginPath(); g.moveTo(0, 1020); g.lineTo(W, 1290); g.lineTo(W, H); g.lineTo(0, H); g.fill();
    g.fillStyle = '#fff'; g.beginPath(); g.arc(cx, 250, 175, 0, Math.PI * 2); g.fill();
  });
  const img = new Image();
  img.onload = () => { (t.image as HTMLCanvasElement).getContext('2d')!.drawImage(img, cx - 160, 90, 320, 320); t.needsUpdate = true; };
  img.src = 'decals/caltex_roundel.png';
  return t;
}

export function martFaceTex(widthU: number, heightU: number, white: string, door: boolean): THREE.CanvasTexture {
  const px = 140, W = Math.round(widthU * px), H = Math.round(heightU * px);
  return canvasTex(W, H, (g) => {
    g.fillStyle = white; g.fillRect(0, 0, W, H);
    if (door) { g.fillStyle = '#8a8d90'; g.fillRect(W / 2 - 0.5 * px, H - 2.2 * px, 1.0 * px, 2.2 * px); }
  });
}

/** Yellow stall outlines and dashed lane lines on the +y face of concrete-top. */
export function stallTex(box: THREE.Box3, pumps: THREE.Vector3[], base: string): THREE.CanvasTexture {
  const W = 2048, H = 2048, sx = W / (box.max.x - box.min.x), sz = H / (box.max.z - box.min.z);
  return canvasTex(W, H, (g) => {
    g.fillStyle = base; g.fillRect(0, 0, W, H);
    g.strokeStyle = '#fff'; g.lineWidth = 0.05 * sx; g.setLineDash([0.8 * sz, 0.6 * sz]);
    for (const lx of [-1.1, 2.7]) { g.beginPath(); g.moveTo((lx - box.min.x) * sx, (-6.5 - box.min.z) * sz); g.lineTo((lx - box.min.x) * sx, (7 - box.min.z) * sz); g.stroke(); }
    g.setLineDash([]); g.strokeStyle = '#f2c230'; g.lineWidth = 0.05 * sx;
    for (const p of pumps) for (const side of [-1.3, 1.3]) {
      const w = 1.2, len = 4.8;
      g.strokeRect((p.x + side - w / 2 - box.min.x) * sx, (p.z - len / 2 - box.min.z) * sz, w * sx, len * sz);
    }
  });
}

/** Soil horizontal strata: 5 wavy bands in four browns, dark root layer on top, 8% fine grains. */
export function soilTex(widthU: number, heightU: number, seed: number): THREE.CanvasTexture {
  const px = 160, W = Math.round(widthU * px), H = Math.round(heightU * px);
  let r = seed; const rnd = () => ((r = (r * 1664525 + 1013904223) >>> 0) / 4294967296);
  return canvasTex(W, H, (g) => {
    const cols = ['#8A6446', '#9A7756', '#A9865F', '#7E5B3E'], cuts = [0];
    for (let i = 0; i < 5; i++) cuts.push(cuts[i] + 0.5 + rnd());
    const k = H / cuts[5], phase = rnd() * 6;
    for (let i = 0; i < 5; i++) {
      g.fillStyle = cols[i % 4]; g.beginPath(); g.moveTo(0, H);
      for (let x = 0; x <= W; x += 4) g.lineTo(x, cuts[i] * k + Math.sin(x / W * 12 + phase + i) * 0.03 * H);
      g.lineTo(W, H); g.fill();
    }
    g.fillStyle = '#6E4E34'; g.fillRect(0, 0, W, H * 0.06);
    for (let i = 0; i < W * H * 0.08 / 4; i++) {
      g.fillStyle = rnd() < 0.5 ? 'rgba(0,0,0,0.25)' : 'rgba(255,230,200,0.2)';
      g.fillRect(rnd() * W, rnd() * H, 2, 2);
    }
  });
}

export function glassTex(base: string): THREE.CanvasTexture {
  return canvasTex(512, 256, (g) => {
    const lift = (i: number) => Math.round(parseInt(base.slice(1 + 2 * i, 3 + 2 * i), 16) * 0.85 + 255 * 0.15);
    const grad = g.createLinearGradient(0, 0, 0, 256); grad.addColorStop(0, base); grad.addColorStop(1, `rgb(${lift(0)},${lift(1)},${lift(2)})`);
    g.fillStyle = grad; g.fillRect(0, 0, 512, 256);
    g.fillStyle = 'rgba(255,255,255,0.18)'; g.beginPath(); g.moveTo(300, 0); g.lineTo(380, 0); g.lineTo(200, 256); g.lineTo(120, 256); g.fill();
    g.fillStyle = 'rgba(255,255,255,0.10)'; g.beginPath(); g.moveTo(420, 0); g.lineTo(450, 0); g.lineTo(270, 256); g.lineTo(240, 256); g.fill();
  });
}

/** Caltex energy lines: three white diagonal bands in the lower corner of the red fascia. */
export function energyLinesTex(): THREE.CanvasTexture {
  return canvasTex(1024, 404, (g) => {
    const px = 1024 / 1.9, run = 404 / Math.tan(55 * Math.PI / 180), wide = 0.14 / Math.sin(55 * Math.PI / 180) * px, gap = 0.28 / Math.sin(55 * Math.PI / 180) * px;
    g.fillStyle = '#fff';
    for (let k = 0; k < 3; k++) {
      const x0 = 0.2 * px + k * gap;
      g.beginPath(); g.moveTo(x0, 404); g.lineTo(x0 + wide, 404); g.lineTo(x0 + wide + run, 0); g.lineTo(x0 + run, 0); g.fill();
    }
  });
}
