import assert from 'node:assert/strict';
import {catalogURL,searchRoms} from '../downloader/downloader.js';
import {installSolver,solveIfNeeded} from '../downloader/solver.js';
assert.equal(catalogURL('',1),'https://romsfun.com/roms/playstation-2/');
assert.equal(catalogURL('',2),'https://romsfun.com/roms/playstation-2/page/2/');
assert.equal(catalogURL('God of War',1),'https://romsfun.com/?s=God%20of%20War');
const search=await searchRoms('God of War',{fetchPage:async url=>'<a href="https://romsfun.com/roms/playstation-2/god-of-war.html">God of War</a>'});
assert.deepEqual(search.urls,['https://romsfun.com/roms/playstation-2/god-of-war.html']);
let routes=0;await installSolver({route(){routes++;}},'',()=>{});assert.equal(routes,0);
const originalFetch=globalThis.fetch,originalTimeout=globalThis.setTimeout;const calls=[];let evaluated=0,agent=null;
const page={url:()=> 'https://romsfun.com/roms/playstation-2/fixture.html',
 evaluate:async(fn,arg)=>{if(evaluated++===0)return {sitekey:'site',action:'managed',cData:'data',chlPageData:'page'};assert.equal(arg,'fixture-token');},
 context:()=>({newCDPSession:async()=>({send:async(method,values)=>{assert.equal(method,'Emulation.setUserAgentOverride');agent=values.userAgent;}})})};
try{
 globalThis.setTimeout=fn=>{fn();return 1;};
 globalThis.fetch=async(url,options)=>{calls.push({url,body:JSON.parse(options.body)});return {ok:true,json:async()=>url.endsWith('createTask')?{errorId:0,taskId:1}:{errorId:0,status:'ready',solution:{token:'fixture-token',userAgent:'FixtureAgent'}}};};
 await solveIfNeeded(page,'fixture-key',()=>{});
 assert.equal(calls.length,2);assert.equal(calls[0].body.task.type,'TurnstileTaskProxyless');assert.equal(calls[0].body.task.data,'data');assert.equal(calls[0].body.task.pagedata,'page');assert.equal(agent,'FixtureAgent');
 const before=calls.length;await solveIfNeeded(page,'',()=>{});assert.equal(calls.length,before);
}finally{globalThis.fetch=originalFetch;globalThis.setTimeout=originalTimeout;}
console.log('PASS: supplied search endpoint/PS2 matching, pagination and optional solver task/callback/user-agent contract; no paid API calls');
