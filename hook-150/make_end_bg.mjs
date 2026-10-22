// node hook-150/make_end_bg.mjs (from ~/motion-design): the last scene's background, rebuilt from the user's reference
// still (assets/end/reference.webp) with the text, pills and discs taken out: the frame is averaged in 20px cells
// leaving those out, the gaps filled in from around them, smoothed, scaled back up and given a fine grain like the
// reference. -> hook-150/assets/end/bg.png (end.html; find.html uses it too)
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
const png = await p.evaluate(async (data) => {
  const im = new Image(); im.src = data; await im.decode();
  const W = 1920, H = 1080, C = 20, GW = W / C, GH = H / C;
  const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'); x.drawImage(im, 0, 0, W, H);
  const D = x.getImageData(0, 0, W, H).data;
  const boxes = [[105, 255, 800, 525], [90, 550, 815, 725], [1258, 438, 1598, 542], [1532, 768, 1872, 872], [1130, 866, 1480, 972]];
  const discs = [[1390, 15, 118], [1226, 196, 78], [1340, 305, 68], [1475, 255, 118], [1658, 270, 76], [1832, 288, 118], [1708, 435, 118],
    [1392, 585, 165], [1607, 725, 165], [1342, 815, 165], [1890, 590, 95], [1900, 760, 110], [1772, 1010, 104]];
  const masked = (i, j) => boxes.some(([a, b2, c2, d]) => i >= a && i <= c2 && j >= b2 && j <= d) || discs.some(([cx, cy, r]) => (i - cx) ** 2 + (j - cy) ** 2 < r * r);
  const grid = [], known = [];
  for (let gy = 0; gy < GH; gy++) for (let gx = 0; gx < GW; gx++) {
    let s = [0, 0, 0], n = 0;
    for (let j = gy * C; j < gy * C + C; j += 2) for (let i = gx * C; i < gx * C + C; i += 2) {
      if (masked(i, j)) continue;
      const k = (j * W + i) * 4; if (D[k] + D[k + 1] + D[k + 2] > 600) continue;
      s[0] += D[k]; s[1] += D[k + 1]; s[2] += D[k + 2]; n++;
    }
    grid.push(n > 10 ? s.map((v) => v / n) : [0, 0, 0]); known.push(n > 10);
  }
  const at = (gx, gy) => grid[Math.min(GH - 1, Math.max(0, gy)) * GW + Math.min(GW - 1, Math.max(0, gx))];
  for (let it = 0; it < 600; it++) for (let gy = 0; gy < GH; gy++) for (let gx = 0; gx < GW; gx++) {
    const i = gy * GW + gx; if (known[i]) continue;
    const ns = [at(gx - 1, gy), at(gx + 1, gy), at(gx, gy - 1), at(gx, gy + 1)];
    grid[i] = [0, 1, 2].map((ch) => ns.reduce((a, v) => a + v[ch], 0) / 4);
  }
  for (let pass = 0; pass < 3; pass++) {
    const g2 = grid.map((_, i) => { const gx = i % GW, gy = (i / GW) | 0; let s = [0, 0, 0]; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const v = at(gx + dx, gy + dy); s[0] += v[0]; s[1] += v[1]; s[2] += v[2]; } return s.map((v) => v / 9); });
    g2.forEach((v, i) => { grid[i] = v; });
  }
  const sm = document.createElement('canvas'); sm.width = GW; sm.height = GH; const sx = sm.getContext('2d'); const sd = sx.createImageData(GW, GH);
  grid.forEach((v, i) => { sd.data[i * 4] = v[0]; sd.data[i * 4 + 1] = v[1]; sd.data[i * 4 + 2] = v[2]; sd.data[i * 4 + 3] = 255; });
  sx.putImageData(sd, 0, 0);
  // scale up smoothly in two steps, then a fine grain
  const mid = document.createElement('canvas'); mid.width = GW * 4; mid.height = GH * 4; const mx = mid.getContext('2d');
  mx.imageSmoothingQuality = 'high'; mx.filter = 'blur(2px)'; mx.drawImage(sm, 0, 0, mid.width, mid.height);
  x.clearRect(0, 0, W, H); x.imageSmoothingQuality = 'high'; x.filter = 'blur(12px)'; x.drawImage(mid, -40, -40, W + 80, H + 80); x.filter = 'none';
  const o = x.getImageData(0, 0, W, H); let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (let k = 0; k < o.data.length; k += 4) { const g = (rnd() - 0.5) * 14; o.data[k] += g; o.data[k + 1] += g; o.data[k + 2] += g; }
  x.putImageData(o, 0, 0);
  return c.toDataURL('image/png');
}, 'data:image/webp;base64,' + readFileSync('hook-150/assets/end/reference.webp').toString('base64'));
writeFileSync('hook-150/assets/end/bg.png', Buffer.from(png.split(',')[1], 'base64'));
await b.close();
console.log('saved hook-150/assets/end/bg.png');
