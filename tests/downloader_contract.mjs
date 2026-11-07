import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {publicURL,chooseVersion,transfer} from '../downloader/worker.mjs';
const resolver=address=>async()=>[{address}];
for(const ip of ['127.0.0.1','10.0.0.1','169.254.169.254','::1','::ffff:127.0.0.1']) {
 await assert.rejects(publicURL('https://93.184.216.34/a',resolver(ip)),/Private/);
}
await assert.rejects(publicURL('http://example.com/a'),/HTTPS/);
await assert.rejects(publicURL('https://user:pass@example.com/a'),/HTTPS/);
assert.equal(await publicURL('https://93.184.216.34/a',resolver('93.184.216.34')),'https://93.184.216.34/a');
assert.throws(()=>chooseVersion([{text:'Demo',url:'demo'}]),/non-demo/);
assert.equal(chooseVersion([{text:'Europe',url:'eu'},{text:'USA',url:'us'}]).url,'us');
const temp=await mkdtemp(path.join(os.tmpdir(),'ps2-downloader-'));
const original=globalThis.fetch;
const seen=[];
const context={cookies:async url=>{seen.push(url);return [{name:'fixture',value:'cookie'}];}};
try {
 globalThis.fetch=async (url,options)=>{assert.equal(options.redirect,'manual');return new Response(new Uint8Array([1,2,3,4]),{headers:{'Content-Length':'4'}});};
 await transfer(context,'https://93.184.216.34/disc.iso','https://93.184.216.34/',path.join(temp,'complete'));
 assert.deepEqual([...await readFile(path.join(temp,'complete.iso'))],[1,2,3,4]);assert.equal(seen[0],'https://93.184.216.34/disc.iso');
 globalThis.fetch=async()=>new Response(new Uint8Array([1]),{headers:{'Content-Length':'5'}});
 await assert.rejects(transfer(context,'https://93.184.216.34/disc.iso','https://93.184.216.34/',path.join(temp,'short')),/Incomplete/);
 await assert.rejects(readFile(path.join(temp,'short.iso.part')),/ENOENT/);
 globalThis.fetch=async()=>new Response('',{status:302,headers:{Location:'https://127.0.0.1/private.iso'}});
 await assert.rejects(transfer(context,'https://93.184.216.34/disc.iso','https://93.184.216.34/',path.join(temp,'redirect')),/Private/);
} finally {globalThis.fetch=original;await rm(temp,{recursive:true,force:true});}
console.log('PASS: downloader URL/version/stream/completion/redirect contract');
