// Gera og.png e os ícones a partir dos SVGs fonte (scripts/og.svg, public/favicon.svg).
// Uso: npm run assets
import sharp from "sharp";

const jobs = [
  ["scripts/og.svg", "public/og.png", 1200, 630, 144],
  ["public/favicon.svg", "public/apple-touch-icon.png", 180, 180, 384],
  ["public/favicon.svg", "public/icon-192.png", 192, 192, 384],
  ["public/favicon.svg", "public/icon-512.png", 512, 512, 384],
];

for (const [src, out, w, h, density] of jobs) {
  const info = await sharp(src, { density }).resize(w, h).png().toFile(out);
  console.log(`${out} ${info.width}x${info.height} (${info.size} bytes)`);
}
