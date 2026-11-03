// usage (run inside a job folder): node render.js stills t1,t2,...   |   node render.js chunk <startFrame> <endFrame> <out.mp4>
// CRF env var sets the quality (default 24).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const ROOT = __dirname, FPS = 30;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
async function open() {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.route('http://local/**', r => {
    const f = path.join(ROOT, decodeURIComponent(new URL(r.request().url()).pathname));
    r.fulfill({ status: 200, contentType: types[path.extname(f)] || 'application/octet-stream', body: fs.readFileSync(f) });
  });
  await page.goto('http://local/scene.html');
  await page.waitForFunction(() => window.READY === true, null, { timeout: 180000 });
  console.log('layout', JSON.stringify(await page.evaluate(() => window.LAYOUT || null)));
  return { browser, page };
}
(async () => {
  const [mode, a, b, out] = process.argv.slice(2);
  const { browser, page } = await open();
  if (mode === 'stills') {
    fs.mkdirSync(path.join(ROOT, 'stills'), { recursive: true });
    for (const t of a.split(',').map(Number)) {
      const t0 = Date.now();
      await page.evaluate(t => window.renderAt(t), t);
      await page.screenshot({ path: path.join(ROOT, 'stills', `t${t}.jpg`), type: 'jpeg', quality: 92 });
      console.log('still', t, Date.now() - t0, 'ms');
    }
  } else {
    const s = +a, e = +b, tmp = out.replace(/\.mp4$/, '.tmp.mp4');
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', String(process.env.CRF || 24), '-pix_fmt', 'yuv420p', '-r', String(FPS), tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = s; f < e; f++) {
      await page.evaluate(t => window.renderAt(t), f / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if ((f - s) % 60 === 0) console.log(out, 'frame', f);
    }
    ff.stdin.end();
    const code = await new Promise(r => ff.on('close', r));
    if (code === 0) fs.renameSync(tmp, out); else { console.error('ffmpeg failed', code); process.exitCode = 1; }
  }
  await browser.close();
})();
