// Internal BitTorrent download worker (webtorrent). JSON-lines IPC on stdout.
// After the file is written the swarm is destroyed and the chunk store deleted — no post-download seeding.
import WebTorrent from 'webtorrent';
import path from 'node:path';
import { mkdir, rename, unlink, stat, rm } from 'node:fs/promises';
import { createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
import { pathToFileURL } from 'node:url';

const MAX_BYTES = 16 * 1024 ** 3;
const emit = message => {
  process.stdout.write(JSON.stringify(message) + '\n');
};

async function main() {
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
    if (input.length > 65536) throw new Error('Request too large.');
  }
  const job = JSON.parse(input);
  if (!path.isAbsolute(job.torrent) || !path.isAbsolute(job.destination)) {
    throw new Error('Expected absolute torrent and destination paths.');
  }
  if (!Number.isInteger(job.fileIndex) || job.fileIndex < 0) {
    throw new Error('Invalid torrent file index.');
  }
  await mkdir(path.dirname(job.destination), { recursive: true });
  // Isolated store per job so leftovers cannot keep seeding after cancel/finish.
  const storePath = job.destination + '.webtorrent-store';
  await rm(storePath, { recursive: true, force: true }).catch(() => {});
  // utp-native is unstable on some Windows Node builds; TCP/WebRTC peers still work.
  const client = new WebTorrent({ utp: false });
  let torrent = null;
  let ticker = null;
  const destroyAll = async () => {
    if (ticker) {
      clearInterval(ticker);
      ticker = null;
    }
    // Stop uploading immediately, then tear the swarm down.
    try {
      client.throttleUpload(0);
    } catch {
      /* ignore */
    }
    if (torrent && !torrent.destroyed) {
      await new Promise(resolve => {
        try {
          torrent.destroy({ destroyStore: true }, () => resolve());
        } catch {
          resolve();
        }
      });
      torrent = null;
    }
    if (!client.destroyed) {
      await new Promise(resolve => client.destroy(() => resolve()));
    }
    await rm(storePath, { recursive: true, force: true }).catch(() => {});
  };
  try {
    emit({ event: 'status', message: 'Connecting to peers...' });
    torrent = await new Promise((resolve, reject) => {
      const handle = client.add(job.torrent, { path: storePath, destroyStoreOnDestroy: true });
      handle.on('error', reject);
      handle.on('ready', () => resolve(handle));
      setTimeout(() => reject(new Error('Torrent metadata timed out.')), 120000);
    });
    if (job.fileIndex >= torrent.files.length) {
      throw new Error('Torrent file index is out of range.');
    }
    // Only fetch the requested file — never select the rest of the collection.
    torrent.files.forEach((entry, index) => {
      if (index === job.fileIndex) entry.select();
      else entry.deselect();
    });
    const file = torrent.files[job.fileIndex];
    if (!file.length || file.length > MAX_BYTES) throw new Error('Invalid torrent file size.');
    const partial = job.destination + '.part';
    await unlink(partial).catch(() => {});
    await unlink(job.destination).catch(() => {});

    let lastEmit = 0;
    let lastBytes = -1;
    const started = Date.now();
    const pushProgress = (force = false) => {
      const bytes = Math.min(file.length, Math.max(0, Number(file.downloaded) || 0));
      const now = Date.now();
      if (!force && now - lastEmit < 200 && bytes === lastBytes) return;
      lastEmit = now;
      lastBytes = bytes;
      const peers = torrent.numPeers || 0;
      const speed = Math.round(torrent.downloadSpeed || (bytes / Math.max(1, (now - started) / 1000)));
      emit({
        event: 'status',
        message: peers
          ? `Downloading from ${peers} peer${peers === 1 ? '' : 's'}...`
          : 'Looking for peers...',
      });
      emit({ event: 'progress', bytes, total: file.length, speed });
    };

    emit({ event: 'status', message: 'Looking for peers...' });
    emit({ event: 'progress', bytes: 0, total: file.length, speed: 0 });
    ticker = setInterval(() => pushProgress(), 250);
    torrent.on('download', () => pushProgress());
    torrent.on('wire', () => pushProgress(true));

    const source = file.createReadStream();
    let streamed = 0;
    source.on('data', chunk => {
      streamed += chunk.length;
      if (streamed > lastBytes) {
        lastBytes = streamed;
        lastEmit = 0;
        pushProgress(true);
      }
    });
    await pipeline(source, createWriteStream(partial, { flags: 'wx' }));
    if (ticker) {
      clearInterval(ticker);
      ticker = null;
    }
    const finalBytes = Math.max(streamed, Number(file.downloaded) || 0);
    if (finalBytes < file.length * 0.99) throw new Error('Incomplete torrent download.');
    await rename(partial, job.destination);
    const info = await stat(job.destination);
    // Tear down swarm + delete chunk store BEFORE complete so we never linger as a seeder.
    await destroyAll();
    emit({ event: 'progress', bytes: info.size, total: file.length, speed: 0 });
    emit({ event: 'complete', path: job.destination, bytes: info.size, total: file.length });
  } finally {
    await destroyAll();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => {
    emit({ event: 'error', message: String(error?.message || error).slice(0, 500) });
    process.exitCode = 1;
  });
}
