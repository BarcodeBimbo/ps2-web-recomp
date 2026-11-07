// Provider flow: origin-IP page load → wait → parse #download-link → stream CDN.
// No click. CDN uses the system VPN tunnel. On IP block → torrent fail-safe.
import { chromium } from 'phantomwright';
import { searchRoms, catalogURL } from './downloader.js';
import { installSolver, solveIfNeeded } from './solver.js';
import { lookup } from 'node:dns/promises';
import ipaddr from 'ipaddr.js';
import { createWriteStream } from 'node:fs';
import { mkdir, rename, unlink } from 'node:fs/promises';
import path from 'node:path';
import { pipeline } from 'node:stream/promises';
import { Transform, Readable } from 'node:stream';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { fetch as undiciFetch } from 'undici';

const ORIGIN_IP = '199.127.62.112';
const PROVIDER_HOST = 'romsfun.com';
const CDN_HOST_RE = /(^|\.)romsfast\.com$/i;
const MAX_BYTES = 16 * 1024 ** 3;
const WAIT_SECONDS = 8;
const extensions = new Set(['.iso','.bin','.img','.chd','.zip','.7z','.rar','.gz','.xz','.bz2','.zst']);
const AD_DOMAINS = ['google-analytics.com', 'googletagmanager.com', 'doubleclick.net', 'crowbarrinds.com', 'propellerads.com', 'popads.net', 'adsterra.com', 'onclickads.net', 'revcontent.com'];
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
const emit = message => process.stdout.write(JSON.stringify(message) + '\n');
const ROOT = path.dirname(fileURLToPath(import.meta.url));

export async function publicURL(value, resolve = lookup) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443')) throw new Error('Only public HTTPS URLs are allowed.');
  const host = url.hostname.replace(/^\[|\]$/g, '');
  if (host === ORIGIN_IP || host === PROVIDER_HOST || host === `www.${PROVIDER_HOST}` || CDN_HOST_RE.test(host)) return url.href;
  const addresses = await resolve(host, {all: true});
  if (!addresses.length || addresses.some(({address}) => ipaddr.process(address).range() !== 'unicast')) throw new Error('Private download destinations are blocked.');
  return url.href;
}

export function chooseVersion(links) {
  const eligible = links.filter(link => !/\b(demo|prototype|proto|sample|beta|alpha|preview|trial|kiosk)\b/i.test(link.text));
  const selected = eligible.find(link => /\b(usa|u\.s\.a|us)\b|\(u\)|\bntsc\b(?![- ]?[je])/i.test(link.text)) || eligible[0];
  if (!selected) throw new Error('No non-demo versions were found.');
  return selected;
}

function isProviderHost(hostname) {
  return hostname === PROVIDER_HOST || hostname === `www.${PROVIDER_HOST}`;
}

function isCdnHost(hostname) {
  return CDN_HOST_RE.test(hostname || '');
}

function isBlockedBody(status, type, snippet = '') {
  if (status === 401 || status === 403 || status === 429) return true;
  if (/text\/html/i.test(type || '') && /invalid|abuse|limit|bot|expired|download link/i.test(snippet)) return true;
  return false;
}

async function streamResponse(response, url, destination) {
  if (!response.body) throw new Error('Provider did not return a file body.');
  const ext = path.extname(decodeURIComponent(new URL(url).pathname)).toLowerCase();
  if (!extensions.has(ext)) {
    await response.body.cancel?.();
    throw new Error('Unsupported download extension.');
  }
  const total = Number(response.headers.get('content-length')) || null;
  if (total !== null && (!Number.isSafeInteger(total) || total < 1 || total > MAX_BYTES)) {
    await response.body.cancel?.();
    throw new Error('Invalid download size.');
  }
  const target = destination + ext;
  const partial = target + '.part';
  await unlink(partial).catch(() => {});
  await unlink(target).catch(() => {});
  let bytes = 0;
  let last = 0;
  const started = Date.now();
  const meter = new Transform({
    transform(chunk, encoding, callback) {
      bytes += chunk.length;
      if (bytes > MAX_BYTES || (total && bytes > total)) return callback(new Error('Download exceeds its size limit.'));
      const now = Date.now();
      if (now - last >= 400) {
        emit({event: 'progress', bytes, total, speed: Math.round(bytes / Math.max(1, (now - started) / 1000))});
        last = now;
      }
      callback(null, chunk);
    },
  });
  try {
    await pipeline(Readable.fromWeb(response.body), meter, createWriteStream(partial, {flags: 'wx'}));
    if (!bytes || (total !== null && total !== bytes)) throw new Error('Incomplete download.');
    await rename(partial, target);
    emit({event: 'complete', path: target, bytes, total});
    return target;
  } catch (error) {
    await unlink(partial).catch(() => {});
    throw error;
  }
}

async function waitForBrowserDownload(dir, before, timeoutMs = 4 * 3600 * 1000) {
  const { readdir } = await import('node:fs/promises');
  const started = Date.now();
  let lastBytes = 0;
  let lastEmit = 0;
  while (Date.now() - started < timeoutMs) {
    const entries = await readdir(dir).catch(() => []);
    const fresh = entries.filter(name => !before.has(name));
    const partial = fresh.find(name => /\.(crdownload|tmp|part)$/i.test(name));
    const done = fresh.find(name => !/\.(crdownload|tmp|part)$/i.test(name));
    if (done) {
      const full = path.join(dir, done);
      const info = await (await import('node:fs/promises')).stat(full);
      if (info.size > 0) return { path: full, bytes: info.size };
    }
    if (partial) {
      const full = path.join(dir, partial);
      const info = await (await import('node:fs/promises')).stat(full).catch(() => null);
      if (info) {
        const now = Date.now();
        if (now - lastEmit >= 400) {
          emit({
            event: 'progress',
            bytes: info.size,
            total: null,
            speed: Math.round((info.size - lastBytes) / Math.max(0.4, (now - lastEmit) / 1000)),
          });
          lastBytes = info.size;
          lastEmit = now;
        }
      }
    }
    await new Promise(r => setTimeout(r, 400));
  }
  throw new Error('Browser CDN download timed out.');
}

/**
 * Fetch the already-parsed CDN URL inside Chromium (no #download-link click).
 * Visit the romsfun referer first so the CDN sees an official session/TLS fingerprint.
 */
export async function transferCdnViaBrowserSession(cdnUrl, referer, destination) {
  cdnUrl = await publicURL(cdnUrl);
  referer = referer || `https://${PROVIDER_HOST}/`;
  const guessed = path.extname(decodeURIComponent(new URL(cdnUrl).pathname)).toLowerCase();
  const downloadDir = destination + '.browser-dl';
  await mkdir(downloadDir, {recursive: true});
  const { readdir } = await import('node:fs/promises');
  const before = new Set(await readdir(downloadDir).catch(() => []));

  emit({event: 'status', message: 'Opening romsfun session for CDN (no click)...'});
  const context = await launchContext({allowCdn: true});
  try {
    const page = context.pages()[0] || await context.newPage();
    page.on('popup', popup => popup.close().catch(() => {}));
    await page.goto(referer, {waitUntil: 'domcontentloaded', timeout: 60000});
    await page.waitForTimeout(1500);

    const client = await context.newCDPSession(page);
    await client.send('Page.setDownloadBehavior', {behavior: 'allow', downloadPath: downloadDir});

    emit({event: 'status', message: 'Fetching parsed CDN URL in browser session...'});
    // Navigate to the parsed link — not a DOM click on #download-link.
    const navigation = page.goto(cdnUrl, {waitUntil: 'commit', timeout: 120000}).catch(() => null);
    const file = await Promise.race([
      waitForBrowserDownload(downloadDir, before),
      navigation.then(async () => {
        // Some CDNs render the "invalid" FAQ page instead of downloading.
        const body = await page.content().catch(() => '');
        if (/request is invalid|Download FAQ/i.test(body)) {
          throw new Error('CDN invalid request in browser session');
        }
        return waitForBrowserDownload(downloadDir, before, 180000);
      }),
    ]);

    const ext = path.extname(file.path).toLowerCase() || guessed;
    if (!extensions.has(ext)) throw new Error('Unsupported download extension.');
    const target = destination + ext;
    await unlink(target).catch(() => {});
    await rename(file.path, target);
    emit({event: 'progress', bytes: file.bytes, total: file.bytes, speed: 0});
    emit({event: 'complete', path: target, bytes: file.bytes, total: file.bytes});
    return target;
  } finally {
    await context.close().catch(() => {});
  }
}

/** Direct CDN GET with official Referer; on block → browser session → SSL proxies. */
export async function transferCdn(url, referer, destination, { cookies = '', userAgent = UA } = {}) {
  url = await publicURL(url);
  if (!isCdnHost(new URL(url).hostname)) throw new Error('Expected a sto.romsfast.com CDN URL.');
  const headers = {
    Referer: referer || `https://${PROVIDER_HOST}/`,
    'User-Agent': userAgent,
    Accept: 'application/octet-stream,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'identity',
    ...(cookies ? { Cookie: cookies } : {}),
  };

  emit({event: 'status', message: 'Downloading signed CDN link...'});
  let response = await undiciFetch(url, {
    headers,
    redirect: 'manual',
    signal: AbortSignal.timeout(60000),
  });

  for (let redirects = 0; redirects < 5 && [301, 302, 303, 307, 308].includes(response.status); redirects++) {
    const location = response.headers.get('location');
    await response.body?.cancel?.();
    if (!location) throw new Error('Invalid CDN redirect.');
    url = await publicURL(new URL(location, url).href);
    response = await undiciFetch(url, {
      headers,
      redirect: 'manual',
      signal: AbortSignal.timeout(60000),
    });
  }

  const type = response.headers.get('content-type') || '';
  const okFile = response.ok && response.body && !/text\/(html|plain)/i.test(type);
  if (okFile) return streamResponse(response, url, destination);

  const snippet = await response.text().catch(() => '');
  await response.body?.cancel?.().catch?.(() => {});
  const why = /invalid/i.test(snippet) ? 'invalid request / IP limited' : `HTTP ${response.status}`;
  emit({event: 'status', message: `CDN direct blocked (${why}); trying browser session...`});

  try {
    return await transferCdnViaBrowserSession(url, referer, destination);
  } catch (browserError) {
    emit({
      event: 'status',
      message: `CDN blocked (${browserError.message}). Connect your VPN app for a fresh IP, or falling back to torrent...`,
    });
    throw new Error('CDN blocked this IP. Connect a VPN, or falling back to torrent.');
  }
}

/** Cookie-aware transfer kept for unit tests / non-CDN hosts. */
export async function transfer(context, url, referer, destination, userAgent = UA) {
  url = await publicURL(url);
  if (isCdnHost(new URL(url).hostname)) {
    const cookies = (await context.cookies(url)).map(c => `${c.name}=${c.value}`).join('; ');
    return transferCdn(url, referer, destination, { cookies, userAgent });
  }
  const cookies = await context.cookies(url);
  const response = await undiciFetch(url, {
    redirect: 'manual',
    signal: AbortSignal.timeout(4 * 3600 * 1000),
    headers: {
      Cookie: cookies.map(c => `${c.name}=${c.value}`).join('; '),
      Referer: referer,
      'User-Agent': userAgent,
      'Accept-Encoding': 'identity',
    },
  });
  if (!response.ok || !response.body || /text\/html/i.test(response.headers.get('content-type') || '')) {
    await response.body?.cancel?.();
    throw new Error(`Provider did not return a file (HTTP ${response.status}).`);
  }
  return streamResponse(response, url, destination);
}

async function launchContext({allowCdn = false} = {}) {
  const userDataDir = path.join(ROOT, '.chrome_profile');
  await mkdir(userDataDir, {recursive: true});
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: true,
    args: ['--disable-blink-features=AutomationControlled', '--test-type'],
    acceptDownloads: true,
    ignoreHTTPSErrors: true,
    viewport: {width: 1440, height: 900},
    userAgent: UA,
    serviceWorkers: 'block',
  });
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    window.open = () => null;
    window.close = () => {};
  });
  await context.route('**/*', async route => {
    const request = route.request();
    const reqUrl = request.url();
    if (AD_DOMAINS.some(domain => reqUrl.includes(domain))) {
      await route.abort();
      return;
    }
    try {
      const current = new URL(reqUrl);
      if (isProviderHost(current.hostname)) {
        await route.continue({
          url: `https://${ORIGIN_IP}${current.pathname}${current.search}`,
          headers: {...request.headers(), Host: PROVIDER_HOST},
        });
        return;
      }
      // When only parsing HTML, block CDN. When fetching the parsed URL, allow it.
      if (isCdnHost(current.hostname)) {
        if (allowCdn) await route.continue();
        else await route.abort();
        return;
      }
      await publicURL(reqUrl);
      await route.continue();
    } catch {
      await route.abort();
    }
  });
  return context;
}

/** Wait for countdown, then parse #download-link href from the DOM (no click). */
async function parseDownloadHref(page) {
  await page.waitForSelector('#download-link', {timeout: 180000});
  emit({event: 'status', message: `Waiting ${WAIT_SECONDS}s for hotlink protection...`});
  await page.waitForTimeout(WAIT_SECONDS * 1000);
  // Re-read after wait — some pages inject the signed URL late.
  await page.waitForFunction(() => {
    const node = document.querySelector('#download-link');
    const href = node && (node.getAttribute('href') || node.href || '');
    return href && /^https?:\/\//i.test(href) && !/#$/.test(href);
  }, {timeout: 60000});
  const href = await page.locator('#download-link').first().evaluate(node => node.getAttribute('href') || node.href || '');
  if (!href) throw new Error('Provider returned no download link.');
  return href.replace(/&amp;/g, '&');
}

async function main() {
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
    if (input.length > 32768) throw new Error('Request too large.');
  }
  const job = JSON.parse(input);
  if (!path.isAbsolute(job.destination) && job.mode !== 'catalog') throw new Error('Expected an absolute managed destination.');

  // CDN-only job: signed URL already resolved (Python origin-IP parse, no click).
  if (job.mode === 'cdn') {
    await transferCdn(job.url, job.referer || `https://${PROVIDER_HOST}/`, job.destination, {
      cookies: job.cookies || '',
    });
    return;
  }

  const context = await launchContext();
  try {
    // Key from Settings localStorage → panel request → job JSON stdin (never process.env).
    const key = String(job.twocaptcha_api_key || '').trim();
    await installSolver(context, key, emit);
    const pages = context.pages();
    const page = pages.length > 0 ? pages[0] : await context.newPage();
    page.on('popup', popup => popup.close().catch(() => {}));

    async function navigate(target) {
      const absolute = await publicURL(target);
      await page.goto(absolute, {waitUntil: 'domcontentloaded', timeout: 60000});
      await page.waitForTimeout(1500);
      await solveIfNeeded(page, key, emit);
    }

    if (job.mode === 'catalog') {
      const url = new URL(catalogURL(job.query, job.page));
      if (url.origin !== 'https://romsfun.com') throw new Error('Expected a PS2 provider page.');
      const result = await searchRoms(job.query || '', {
        page: job.page || 1,
        fetchPage: async target => {
          await navigate(target);
          await page.waitForSelector('a[href*="/roms/playstation-2/"]', {timeout: 180000});
          const html = await page.content();
          if (Buffer.byteLength(html) > 4 * 1024 * 1024) throw new Error('Catalog too large.');
          return html;
        },
      });
      emit({event: 'catalog', html: result.html});
      return;
    }

    const url = new URL(job.url);
    if (url.origin !== 'https://romsfun.com' || !/^\/(roms\/playstation-2|download)\//.test(url.pathname)) {
      throw new Error('Expected a PS2 provider page.');
    }

    emit({event: 'status', message: 'Opening provider via origin IP...'});
    await navigate(job.url);
    if (url.pathname.startsWith('/roms/')) {
      const button = page.getByRole('link', {name: /Download ROM/i}).first();
      await button.waitFor({timeout: 180000});
      const href = await button.getAttribute('href');
      await navigate(new URL(href, page.url()).href);
    }
    if (!(await page.locator('#download-link').count())) {
      await page.waitForSelector('table tbody tr a', {timeout: 180000});
      const links = await page.locator('table tbody tr a').evaluateAll(nodes => nodes.map(a => ({text: a.textContent || '', url: a.href})));
      const selected = chooseVersion(links);
      emit({event: 'status', message: 'Selected version: ' + selected.text.slice(0, 200)});
      await navigate(selected.url);
    }

    const referer = page.url();
    const href = await parseDownloadHref(page);
    const absolute = await publicURL(new URL(href, referer).href);
    emit({event: 'status', message: 'Parsed CDN link; fetching in same browser session...'});

    // Same session that waited out hotlink protection — do NOT click #download-link.
    // Navigate to the parsed href with CDP downloads enabled.
    const downloadDir = job.destination + '.browser-dl';
    await mkdir(downloadDir, {recursive: true});
    const { readdir } = await import('node:fs/promises');
    const before = new Set(await readdir(downloadDir).catch(() => []));
    const client = await context.newCDPSession(page);
    await client.send('Page.setDownloadBehavior', {behavior: 'allow', downloadPath: downloadDir});

    // Allow CDN host for this navigation (route was blocking it during HTML parse).
    await context.unroute('**/*').catch(() => {});
    await context.route('**/*', async route => {
      const request = route.request();
      const reqUrl = request.url();
      if (AD_DOMAINS.some(domain => reqUrl.includes(domain))) { await route.abort(); return; }
      try {
        const current = new URL(reqUrl);
        if (isProviderHost(current.hostname)) {
          await route.continue({
            url: `https://${ORIGIN_IP}${current.pathname}${current.search}`,
            headers: {...request.headers(), Host: PROVIDER_HOST},
          });
          return;
        }
        await route.continue();
      } catch { await route.abort(); }
    });

    const nav = page.goto(absolute, {waitUntil: 'commit', timeout: 120000}).catch(() => null);
    try {
      const file = await Promise.race([
        waitForBrowserDownload(downloadDir, before),
        nav.then(async () => {
          const body = await page.content().catch(() => '');
          if (/request is invalid|Download FAQ/i.test(body)) {
            throw new Error('CDN invalid request in browser session');
          }
          return waitForBrowserDownload(downloadDir, before, 180000);
        }),
      ]);
      const guessed = path.extname(decodeURIComponent(new URL(absolute).pathname)).toLowerCase();
      const ext = path.extname(file.path).toLowerCase() || guessed;
      if (!extensions.has(ext)) throw new Error('Unsupported download extension.');
      const target = job.destination + ext;
      await unlink(target).catch(() => {});
      await rename(file.path, target);
      emit({event: 'progress', bytes: file.bytes, total: file.bytes, speed: 0});
      emit({event: 'complete', path: target, bytes: file.bytes, total: file.bytes});
      return;
    } catch (sessionError) {
      emit({event: 'status', message: `Same-session CDN failed (${sessionError.message})`});
      await context.close().catch(() => {});
      throw new Error('CDN blocked this IP. Connect a VPN, or falling back to torrent.');
    }
  } finally {
    await context.close().catch(() => {});
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => {
    emit({
      event: 'error',
      message: /executable.*exist|browserType.launch/i.test(error.message)
        ? 'Browser unavailable. Run Setup.cmd on the desktop.'
        : (error.message || 'Download failed.'),
    });
    process.exitCode = 1;
  });
}
