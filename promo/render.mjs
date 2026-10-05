// Renders a browser-built film to MP4: headless Chrome steps it frame by frame, ffmpeg encodes.
//
// Contract — the page (film.html, else index.html, in the film folder) draws into its first <canvas> and defines:
//   window.FILM = {
//     W, H, FPS, DURATION,                // canvas size, frame rate, length in seconds
//     ready: Promise,                     // resolves once fonts/images are loaded
//     renderTime(t),                      // draw the frame at time t (seconds) — a pure function of t
//     renderAudio?(): Promise<string>,    // optional: base64 16-bit PCM WAV of the score
//   }
//
// Setup: copy this file into the film folder, then `bun add -d puppeteer-core` (or `npm i -D puppeteer-core`).
// Needs ffmpeg and Google Chrome (set CHROME_PATH to use another Chromium).
//
//   node render.mjs                     → out/film.mp4
//   node render.mjs --stills 0.5,3,7.2  → out/still-<t>.png, for reviewing single moments
//   node render.mjs --to 8              → render only the first 8 s (quick preview)
//   node render.mjs --audio-only        → re-render the score and remux it into the existing MP4
//   --out out/name.mp4                  → output path
import puppeteer from 'puppeteer-core';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync, mkdirSync, readFileSync, renameSync, statSync, writeFileSync } from 'node:fs';
import { dirname, extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const arg = name => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : undefined; };
const mp4 = join(root, arg('--out') ?? 'out/film.mp4');
const outDir = dirname(mp4);
mkdirSync(outDir, { recursive: true });

const entry = existsSync(join(root, 'film.html')) ? 'film.html' : 'index.html';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.json': 'application/json', '.woff2': 'font/woff2', '.wav': 'audio/wav' };
const server = createServer((req, res) => {
  const path = join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname.replace(/^\/$/, '/' + entry)));
  if (!path.startsWith(root) || !existsSync(path) || statSync(path).isDirectory()) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'content-type': TYPES[extname(path)] ?? 'application/octet-stream' }).end(readFileSync(path));
});
await new Promise(r => server.listen(0, '127.0.0.1', r));

const chrome = process.env.CHROME_PATH ?? [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
].find(existsSync);
const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--force-color-profile=srgb', '--hide-scrollbars'] });
const page = await browser.newPage();
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.evaluate(() => window.FILM.ready);
const film = await page.evaluate(() => ({ W: FILM.W, H: FILM.H, FPS: FILM.FPS, DURATION: FILM.DURATION, audio: !!FILM.renderAudio }));
await page.setViewport({ width: film.W, height: film.H });

const frame = async t => Buffer.from(await page.evaluate(t => {
  FILM.renderTime(t);
  return document.querySelector('canvas').toDataURL('image/png').split(',')[1];
}, t), 'base64');
const ffmpeg = args => new Promise((resolve, reject) => {
  spawn('ffmpeg', ['-y', '-loglevel', 'error', ...args], { stdio: 'inherit' })
    .on('close', code => (code ? reject(new Error('ffmpeg exited ' + code)) : resolve()));
});
const renderWav = async () => {
  const wav = join(outDir, 'score.wav');
  writeFileSync(wav, Buffer.from(await page.evaluate(() => FILM.renderAudio()), 'base64'));
  return wav;
};
const AUDIO = ['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '192k'];

if (arg('--stills')) {
  for (const t of arg('--stills').split(',').map(Number)) {
    writeFileSync(join(outDir, `still-${t.toFixed(2)}.png`), await frame(t));
  }
  console.log('stills written to', outDir);
} else if (process.argv.includes('--audio-only')) {
  if (!film.audio) throw new Error('FILM.renderAudio is not defined');
  const wav = await renderWav(), tmp = mp4.replace(/\.mp4$/, '.remux.mp4');
  await ffmpeg(['-i', mp4, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', ...AUDIO, '-movflags', '+faststart', '-shortest', tmp]);
  renameSync(tmp, mp4);
  console.log('remuxed', mp4);
} else {
  const seconds = Math.min(Number(arg('--to') ?? film.DURATION), film.DURATION);
  const wav = film.audio ? await renderWav() : null;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(film.FPS), '-c:v', 'png', '-i', '-',
    ...(wav ? ['-i', wav] : []),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-tune', 'animation', '-pix_fmt', 'yuv420p',
    ...(wav ? AUDIO : ['-an']), '-t', String(seconds), '-movflags', '+faststart', mp4], { stdio: ['pipe', 'inherit', 'inherit'] });
  const closed = new Promise(r => ff.on('close', r));
  const total = Math.round(seconds * film.FPS), started = Date.now();
  for (let i = 0; i < total; i++) {
    if (!ff.stdin.write(await frame(i / film.FPS))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (film.FPS * 2) === 0) console.log(`frame ${i}/${total}  ${Math.round((Date.now() - started) / 1000)}s`);
  }
  ff.stdin.end();
  await closed;
  const mb = statSync(mp4).size / 1048576;
  console.log(`wrote ${mp4} (${mb.toFixed(1)} MB${mb > 10 ? ' — over GitHub’s 10 MB upload limit' : ''})`);
}

await browser.close();
server.close();
