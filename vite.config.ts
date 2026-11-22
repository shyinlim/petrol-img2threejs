import { defineConfig } from 'vite';
// Generated factory loads reference PBR maps by bare file name (for example soil_albedo.png).
export default defineConfig({
  base: '/petrol-img2threejs/',
  publicDir: 'material-evidence',
});
