import { chromium } from 'phantomwright';
import * as fs from 'fs';
import * as https from 'https';
import * as path from 'path';
import * as readline from 'readline';

const PS2_SLUG = 'playstation-2';
const PS2_FOLDER = 'PS2';
const WAIT_SECONDS = 20;
const ORIGIN_IP = '199.127.62.112';
const PROVIDER_HOST = 'romsfun.com';

const TWOCAPTCHA_API_KEY = "30fa9ce989c7f43c15d28e1e0f1a8264";
const TWOCAPTCHA_CREATE_URL = "https://api.2captcha.com/createTask";
const TWOCAPTCHA_RESULT_URL = "https://api.2captcha.com/getTaskResult";

const US_RE = /\b(?:usa|u\.s\.a\.?|us)\b|\(us\)|\(u\)|\bntsc\b(?![- ]?[je])/i;
const DEMO_RE = /\b(demo|prototype|proto|sample|beta|alpha|pre[- ]?alpha|prealpha|kiosk|preview|trial|pilot)\b/i;

const args = process.argv.slice(2);
const isHeaded = args.includes('--headed') || args.includes('--debug');

interface GameResult { title: string; url: string; }
interface VersionLink { text: string; url: string; }

function log(msg: string) {
    console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
}

function cleanFilenameForR36s(filename: string, cleanTags = false): string {
    let name = path.parse(filename).name;
    const ext = path.parse(filename).ext.toLowerCase();
    name = name.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
    name = name.replace(/[:?*"<>|/\\#%{}@!~$&']/g, '');
    if (cleanTags) name = name.replace(/\([^)]*\)/g, '').replace(/\[[^\]]*\]/g, '');
    name = name.replace(/\s+/g, ' ').trim().replace(/-+/g, '-').replace(/^[-\s]+|[-\s]+$/g, '');
    return `${name || 'ROM_Game'}${ext}`;
}

async function solveTurnstile2Captcha(sitekey: string, pageUrl: string, action?: string, cdata?: string, pagedata?: string): Promise<string> {
    const task: any = { type: "TurnstileTaskProxyless", websiteURL: pageUrl, websiteKey: sitekey };
    if (action) task.action = action;
    if (cdata) task.data = cdata;
    if (pagedata) task.pagedata = pagedata;

    log(`   🔄 [2CAPTCHA] Sending Turnstile to 2Captcha...`);
    const createRes = await fetch(TWOCAPTCHA_CREATE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientKey: TWOCAPTCHA_API_KEY, task })
    });
    const createData: any = await createRes.json();
    
    if (createData.errorId !== 0) throw new Error(`2Captcha Error: ${JSON.stringify(createData)}`);
    const taskId = createData.taskId;

    log(`   ⏳ [2CAPTCHA] Waiting for solution (Task ID: ${taskId})...`);
    for (let i = 0; i < 30; i++) {
        await new Promise(r => setTimeout(r, 5000));
        const resultRes = await fetch(TWOCAPTCHA_RESULT_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clientKey: TWOCAPTCHA_API_KEY, taskId })
        });
        const resultData: any = await resultRes.json();
        
        if (resultData.errorId !== 0) throw new Error(`2Captcha Error: ${JSON.stringify(resultData)}`);
        if (resultData.status === 'ready') {
            log(`   ✅ [2CAPTCHA] Token received!`);
            return resultData.solution.token;
        }
    }
    throw new Error("2Captcha timed out");
}

/** Fetch romsfun HTML via origin IP + Host header to skip Cloudflare. */
function fetchProvider(url: string): Promise<string> {
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
        }, (res) => {
            const chunks: Buffer[] = [];
            let total = 0;
            res.on('data', (chunk: Buffer) => {
                total += chunk.length;
                if (total > 4 * 1024 * 1024) {
                    req.destroy();
                    reject(new Error('Provider response too large'));
                    return;
                }
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

async function searchRoms(query: string, page = 1): Promise<GameResult[]> {
    const url = query
        ? `https://${PROVIDER_HOST}/${page > 1 ? `page/${page}/` : ''}?s=${encodeURIComponent(query)}`
        : `https://${PROVIDER_HOST}/roms/${PS2_SLUG}/${page > 1 ? `page/${page}/` : ''}`;
    const html = await fetchProvider(url);
    const matches = [...html.matchAll(new RegExp(`href="(https://romsfun\\.com/roms/${PS2_SLUG}/([^/]+)\\.html)"`, 'g'))];
    const results: GameResult[] = [];
    const seen = new Set<string>();
    for (const match of matches) {
        if (!seen.has(match[1])) {
            seen.add(match[1]);
            results.push({ title: match[2].replace(/-/g, ' ').toUpperCase(), url: match[1] });
        }
    }
    return results;
}

async function processDownload(item: GameResult, outputDir: string, cleanTags: boolean) {
    const outDir = path.join(outputDir, PS2_FOLDER);
    fs.mkdirSync(outDir, { recursive: true });

    log(`🔍 Processing: ${item.title}`);
    const launchArgs = ['--disable-blink-features=AutomationControlled', '--test-type'];
    if (!isHeaded) launchArgs.push('--headless=new');

    const userDataDir = path.join(process.cwd(), '.chrome_profile');
    log(`   Mode: ${isHeaded ? 'HEADED (Visible)' : 'HEADLESS (Invisible)'}`);

    const context = await chromium.launchPersistentContext(userDataDir, {
        headless: false, 
        args: launchArgs,
        acceptDownloads: true,
        viewport: { width: 1440, height: 900 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    // Origin-IP rewrite for romsfun HTML (skips edge CF). Leave CDN hosts on Chromium.
    await context.route('**/*', async (route) => {
        const reqUrl = route.request().url();
        const adDomains = ['google-analytics.com', 'googletagmanager.com', 'doubleclick.net', 'cloudfront.net', 'crowbarrinds.com', 'propellerads.com', 'popads.net', 'adsterra.com', 'onclickads.net', 'revcontent.com'];
        if (adDomains.some(domain => reqUrl.includes(domain))) {
            await route.abort();
            return;
        }
        try {
            const current = new URL(reqUrl);
            if (current.hostname === PROVIDER_HOST || current.hostname === `www.${PROVIDER_HOST}`) {
                await route.continue({
                    url: `https://${ORIGIN_IP}${current.pathname}${current.search}`,
                    headers: { ...route.request().headers(), Host: PROVIDER_HOST },
                });
                return;
            }
        } catch { /* fall through */ }
        await route.continue();
    });

    // 2. INTERCEPT AND MOCK CLOUDFLARE'S API.JS TO CAPTURE PARAMETERS
    await context.route('**/turnstile/**/api.js*', async (route) => {
        const url = new URL(route.request().url());
        const onload = url.searchParams.get('onload');
        
        // This mock replaces Cloudflare's real script. It hijacks turnstile.render and passes the data back.
        const mockScript = `
            window.turnstile = {
                render: function(container, options) {
                    window._cf_turnstile_params = options;
                    window._cf_turnstile_ready = true;
                },
                ready: function(cb) { if (cb) cb(); },
                implicit: function() {}
            };
            ${onload ? `if (typeof window["${onload}"] === 'function') window["${onload}"]();` : ''}
        `;
        
        await route.fulfill({
            status: 200,
            contentType: 'application/javascript',
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            body: mockScript
        });
    });

    const pages = context.pages();
    const page = pages.length > 0 ? pages[0] : await context.newPage();

    await context.addInitScript(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.open = () => null;
        window.close = () => {}; 
    });

    page.on('popup', async (popup) => {
        log('   🛑 Blocked a pop-up tab');
        await popup.close().catch(() => {});
    });

    try {
        log('🌐 Loading game page...');
        await page.goto(item.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await page.waitForTimeout(3000);

        const title = await page.title();
        if (title.includes("Just a moment") || await page.locator('input[name="cf-turnstile-response"]').count() > 0) {
            log('   ⚠️ Cloudflare Challenge detected in Headless mode!');
            
            log('   ⏳ Waiting for Turnstile parameters...');
            await page.waitForFunction(() => (window as any)._cf_turnstile_ready, { timeout: 15000 });
            
            const params = await page.evaluate(() => {
                const opts = (window as any)._cf_turnstile_params;
                if (!opts) return null;
                return {
                    websiteKey: opts.sitekey,
                    action: opts.action,
                    data: opts.cData,
                    pagedata: opts.chlPageData
                };
            });

            if (params && params.websiteKey) {
                log(`   🎯 Intercepted Turnstile (Sitekey: ${params.websiteKey})`);
                const token = await solveTurnstile2Captcha(params.websiteKey, item.url, params.action, params.data, params.pagedata);
                log('   ✅ Injecting token into DOM and executing callback...');
                
                await page.evaluate((t) => {
                    const input = document.querySelector('input[name="cf-turnstile-response"]') as HTMLInputElement;
                    if (input) input.value = t;
                    if ((window as any)._cf_turnstile_params && typeof (window as any)._cf_turnstile_params.callback === 'function') {
                        (window as any)._cf_turnstile_params.callback(t);
                    }
                }, token);
                
                log('   ⏳ Waiting for Cloudflare verification to clear...');
                await page.waitForSelector('a:has-text("Download ROM")', { timeout: 30000 }).catch(() => {});
            } else {
                log('   ✗ Could not extract Turnstile parameters.');
                return;
            }
        }

        log('🌐 Looking for Download ROM button...');
        await page.waitForSelector('a:has-text("Download ROM")', { timeout: 15000 }).catch(() => {});

        const dlButton = page.locator('a:has-text("Download ROM")');
        if (await dlButton.count() === 0) {
            log('✗ No Download ROM button found.');
            return;
        }

        const indexUrl = await dlButton.first().getAttribute('href');
        if (!indexUrl) return;

        log('🌐 Fetching download index table...');
        await page.goto(indexUrl, { waitUntil: 'domcontentloaded' });
        await page.waitForSelector('table tbody tr a', { timeout: 15000 });

        const versionLinks = await page.$$eval('table tbody tr a', (anchors) => {
            return anchors.map(a => ({
                text: (a.textContent || '').replace(/\s+/g, ' ').trim(),
                url: (a as HTMLAnchorElement).href
            }));
        }) as VersionLink[];

        if (versionLinks.length === 0) {
            log('✗ No download links found.');
            return;
        }

        const validLinks = versionLinks.filter(l => !DEMO_RE.test(l.text));
        let target = validLinks.find(l => US_RE.test(l.text));
        
        if (target) {
            log(`   🎯 USA Priority found: ${target.text}`);
        } else {
            target = validLinks[0];
            log(`   ⚠️ No USA version found. Falling back to: ${target.text}`);
        }

        log(`   🔗 Navigating to: ${target.url}`);
        await page.goto(target.url, { waitUntil: 'domcontentloaded' });

        log(`   ⏳ Waiting ${WAIT_SECONDS}s for hotlink protection to expire...`);
        await new Promise(r => setTimeout(r, WAIT_SECONDS * 1000));

        log('   🔗 Parsing the download link from the DOM...');
        await page.waitForSelector('#download-link', { timeout: 15000 });
        let downloadUrl = await page.locator('#download-link').getAttribute('href');
        
        if (!downloadUrl) return;

        downloadUrl = downloadUrl.replace(/&amp;/g, '&');

        log(`   📥 Parsed Link: ${downloadUrl.split('?')[0]}`);
        log('   📥 Downloading inside Chromium (CF session / TLS bypass)...');

        const rawFilename = decodeURIComponent(downloadUrl.split('/').pop()?.split('?')[0] || 'download.zip');
        const safeName = cleanFilenameForR36s(rawFilename, cleanTags);
        const savePath = path.join(outDir, safeName);

        const [download] = await Promise.all([
            page.waitForEvent('download', { timeout: 4 * 3600 * 1000 }),
            page.locator('#download-link').click({ timeout: 60000 }),
        ]);
        const failure = await download.failure();
        if (failure) {
            log(`   ✗ Browser download failed: ${failure}`);
            return;
        }
        await download.saveAs(savePath);
        const stats = fs.statSync(savePath);
        log(`   ✅ Saved ${(stats.size / 1024 / 1024).toFixed(2)} MB to ${savePath}`);

    } catch (e) {
        log(`   ✗ Error: ${e}`);
    } finally {
        await context.close();
    }
}

async function main() {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const ask = (q: string) => new Promise<string>(resolve => rl.question(q, resolve));

    log('🎮 ROMSFUN PS2 DOWNLOADER (TypeScript)');
    if (isHeaded) log('🔧 Debug/Headed mode enabled');

    const query = await ask('Search PS2 games: ');
    const results = await searchRoms(query);

    if (results.length === 0) {
        log('No results found.');
        rl.close();
        return;
    }

    results.slice(0, 15).forEach((r, i) => console.log(`${i + 1}. ${r.title}`));
    const choice = await ask('Select number to download: ');
    const idx = parseInt(choice) - 1;

    if (idx >= 0 && idx < results.length) {
        rl.close();
        await processDownload(results[idx], './downloads', false);
    } else {
        rl.close();
    }
}

main().catch(console.error);