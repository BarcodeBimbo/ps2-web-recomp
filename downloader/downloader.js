// Search endpoint and PS2 link matching retained from the supplied Downloader.ts.
import https from 'node:https';

export const PS2_SLUG = 'playstation-2';
export const ORIGIN_IP = '199.127.62.112';
export const PROVIDER_HOST = 'romsfun.com';

export function catalogURL(query = '', page = 1) {
  if(typeof query !== 'string' || query.length > 120 || !Number.isInteger(page) || page < 1 || page > 500) throw new Error('Invalid catalog request.');
  if(query) return `https://romsfun.com/${page > 1 ? `page/${page}/` : ''}?s=${encodeURIComponent(query)}`;
  return `https://romsfun.com/roms/${PS2_SLUG}/${page > 1 ? `page/${page}/` : ''}`;
}

/** Fetch catalog HTML via origin IP + Host header (skips Cloudflare). */
export function fetchProvider(url) {
  const parsed = new URL(url);
  if (parsed.hostname !== PROVIDER_HOST) throw new Error('Only romsfun.com pages can use the origin bypass.');
  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: ORIGIN_IP,
      servername: PROVIDER_HOST,
      path: parsed.pathname + parsed.search,
      method: 'GET',
      rejectUnauthorized: false,
      headers: {
        Host: PROVIDER_HOST,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        Accept: 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'identity',
        Referer: `https://${PROVIDER_HOST}/`,
      },
    }, res => {
      const chunks = [];
      let total = 0;
      res.on('data', chunk => {
        total += chunk.length;
        if (total > 4 * 1024 * 1024) { req.destroy(); reject(new Error('Provider response too large')); return; }
        chunks.push(chunk);
      });
      res.on('end', () => {
        const html = Buffer.concat(chunks).toString('utf8');
        if (/just a moment|cf-turnstile/i.test(html)) reject(new Error('Cloudflare challenge still active'));
        else if ((res.statusCode || 500) >= 400) reject(new Error(`Provider HTTP ${res.statusCode}`));
        else resolve(html);
      });
    });
    req.on('error', reject);
    req.end();
  });
}

export async function searchRoms(query, {page = 1, fetchPage} = {}) {
  const html = await (fetchPage || fetchProvider)(catalogURL(query, page));
  const matches = [...html.matchAll(new RegExp(`href=["'](https://romsfun\\.com/roms/${PS2_SLUG}/([^/]+)\\.html)["']`, 'g'))];
  return {html, urls:[...new Set(matches.map(match=>match[1]))]};
}
