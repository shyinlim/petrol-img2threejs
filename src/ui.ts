import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { LookState } from './scene';

export type UIHooks = {
  getCarSpeed: () => number;
  pickApi: { select: (id: string | null) => void; partCount: () => number };
};

export type SetupUIParams = {
  model: THREE.Object3D;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
  controls: OrbitControls;
  look: LookState;
  applyLook: () => void;
  gate: boolean;
  baseColors: Map<THREE.MeshStandardMaterial, THREE.Color>;
  orangeSpec: Map<THREE.MeshStandardMaterial, string>;
  partById: (id: string) => THREE.Object3D | null;
};

/**
 * Binds inspector sliders, colour pickers, raycast part picking/lifting, and toolbar buttons.
 */
export function setupUI(params: SetupUIParams): UIHooks {
  const { model, scene, camera, renderer, controls, look, applyLook, gate, baseColors, orangeSpec, partById } = params;

  const canopy = partById('canopy');
  const canopyY0 = canopy?.position.y ?? 0;
  const columns: { mesh: THREE.Object3D; y0: number; s0: number; len0: number }[] = [];
  model.traverse((o: any) => {
    if (o.isMesh && /^column-\d$/.test(o.userData?.sculptComponent?.id ?? '')) {
      o.geometry.computeBoundingBox();
      const bb = o.geometry.boundingBox;
      columns.push({ mesh: o, y0: o.position.y, s0: o.scale.y, len0: bb.max.y - bb.min.y });
    }
  });
  function stretchColumns(dy: number) {
    for (const c of columns) {
      c.mesh.scale.y = c.s0 * (c.len0 + dy) / c.len0;
      c.mesh.position.y = c.y0 - dy / 2;
    }
  }

  const resets: (() => void)[] = [];
  function setTrackFill(el: HTMLInputElement) {
    const min = +el.min, max = +el.max, val = +el.value;
    el.style.setProperty('--pct', `${max > min ? ((val - min) / (max - min)) * 100 : 0}%`);
  }

  function bind(id: string, out: string, fn: (v: number) => void) {
    const el = document.getElementById(id) as HTMLInputElement;
    const num = document.getElementById(out) as HTMLInputElement;
    const init = el.defaultValue;
    el.addEventListener('input', () => { num.value = el.value; setTrackFill(el); fn(parseFloat(el.value)); });
    const apply = () => {
      el.value = num.value;
      if (document.activeElement !== num && +num.value !== +el.value) num.value = el.value;
      setTrackFill(el);
      fn(parseFloat(el.value));
    };
    num.addEventListener('input', () => {
      const v = parseFloat(num.value);
      if (!isNaN(v) && v >= +el.min && v <= +el.max) apply();
    });
    num.addEventListener('change', () => {
      if (num.value === '') { num.value = el.value; return; }
      apply();
      num.value = el.value;
    });
    num.value = el.value;
    setTrackFill(el);
    if (!gate) fn(parseFloat(el.value));
    resets.push(() => { el.value = init; num.value = init; setTrackFill(el); fn(parseFloat(init)); });
  }

  let carSpeed = 2;
  bind('s-az', 'v-az', (v) => { look.sunAz = v; applyLook(); });
  bind('s-el', 'v-el', (v) => { look.sunEl = v; applyLook(); });
  bind('s-exp', 'v-exp', (v) => { look.exposure = v; applyLook(); });
  bind('s-sh', 'v-sh', (v) => { look.shadowRadius = v; applyLook(); });
  bind('s-env', 'v-env', (v) => { look.envIntensity = v; applyLook(); });
  bind('s-ch', 'v-ch', (v) => { if (canopy) { canopy.position.y = canopyY0 * v; stretchColumns(canopyY0 * v - canopyY0); } });
  bind('s-rot', 'v-rot', (v) => { controls.autoRotateSpeed = v; });
  bind('s-wind', 'v-wind', (v) => { look.wind = v; });
  bind('s-car', 'v-car', (v) => { carSpeed = v; });

  const dom = renderer.domElement;

  function bindColor(id: string, hexId: string, init: string, set: (hex: string) => void) {
    const el = document.getElementById(id) as HTMLInputElement;
    const label = document.getElementById(hexId)!;
    const norm = init.toLowerCase();
    el.value = norm;
    label.textContent = norm.toUpperCase();
    el.addEventListener('input', () => { label.textContent = el.value.toUpperCase(); set(el.value); });
    resets.push(() => { el.value = norm; label.textContent = norm.toUpperCase(); set(norm); });
  }
  const orangeHex = (specId: string) => {
    for (const [m, s] of orangeSpec) if (s === specId) return '#' + baseColors.get(m)!.getHexString();
    return '#ff6e2a';
  };
  const setOrange = (...specIds: string[]) => (hex: string) => orangeSpec.forEach((s, m) => {
    if (specIds.includes(s)) { const c = new THREE.Color(hex); baseColors.set(m, c); m.color.copy(c); }
  });
  const grassMats = () => {
    const s = new Set<any>();
    model.traverse((o: any) => {
      if (o.isMesh && o.userData?.sculptComponent?.material === 'grass') {
        ([] as any[]).concat(o.material).forEach((m) => m.color && s.add(m));
      }
    });
    return [...s];
  };
  const syncBgTheme = (hex: string) => {
    const c = new THREE.Color(hex);
    const lum = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
    document.body.classList.toggle('dark-bg', lum < 0.35);
  };
  syncBgTheme(look.bg);
  bindColor('c-canopy', 'h-canopy', orangeHex('fascia-orange'), setOrange('fascia-orange', 'mart-orange'));
  bindColor('c-pump', 'h-pump', orangeHex('pump-orange'), setOrange('pump-orange'));
  bindColor('c-grass', 'h-grass', '#' + (grassMats()[0]?.color.getHexString() ?? '5fb84a'), (hex) => grassMats().forEach((m) => m.color.set(hex)));
  bindColor('c-bg', 'h-bg', look.bg, (hex) => { look.bg = hex; syncBgTheme(hex); applyLook(); });

  document.getElementById('b-reset')?.addEventListener('click', () => {
    resets.forEach((fn) => fn());
  });

  if (!gate) {
    const panel = document.getElementById('panel')!;
    document.getElementById('panel-head')!.addEventListener('click', (e) => {
      const c = panel.classList.toggle('collapsed');
      (e.currentTarget as HTMLElement).setAttribute('aria-expanded', String(!c));
    });
    const btn = (id: string, fn: (b: HTMLElement) => void) => {
      const b = document.getElementById(id)!;
      b.addEventListener('click', () => fn(b));
    };
    btn('b-reset-view', () => { controls.enableDamping = false; controls.reset(); controls.reset(); controls.enableDamping = true; });
    btn('b-rotate', (b) => { controls.autoRotate = !controls.autoRotate; b.classList.toggle('on', controls.autoRotate); b.setAttribute('aria-pressed', String(controls.autoRotate)); });
    btn('b-fullscreen', () => { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen(); });
    btn('b-shot', () => {
      renderer.render(scene, camera);
      const a = document.createElement('a'); a.href = dom.toDataURL('image/png'); a.download = 'caltex-station.png'; a.click();
    });
  }

  return {
    getCarSpeed: () => carSpeed,
    pickApi: {
      select: () => {},
      partCount: () => { let c = 0; model.traverse((o: any) => { if (o.userData?.sculptComponent && !o.isMesh) c++; }); return c; },
    },
  };
}
