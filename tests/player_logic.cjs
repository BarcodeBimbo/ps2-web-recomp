// DOM/input regressions without loading a copyrighted game or WebAssembly build.
// npm install --prefix /tmp/ps2-test-dom linkedom
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let domPackage;
try { domPackage = require(process.env.LINKEDOM_PATH || 'linkedom'); }
catch { domPackage = require('/tmp/ps2-test-dom/node_modules/linkedom'); }
const {parseHTML}=domPackage;
const source=fs.readFileSync(require('node:path').join(__dirname,'../web/shell.html'),'utf8').replace('{{{ SCRIPT }}}','<script src="ps2web.js"></script>').replaceAll('__PS2_ASYNC_MODE__',process.env.PS2_TEST_ASYNC_MODE||'jspi');
const {document,window:dom}=parseHTML(source);
const storage=new Map(),events=new Map();
Object.defineProperty(dom.HTMLSelectElement.prototype,'value',{configurable:true,get(){return this._value??this.querySelector('option')?.getAttribute('value')??'';},set(v){this._value=String(v);}});
dom.HTMLSelectElement.prototype.add=function(el){this.append(el);};
function Option(text,value){const el=document.createElement('option');el.textContent=text;el.setAttribute('value',value);return el;}
for(const el of document.querySelectorAll('dialog')){
 Object.defineProperty(el,'open',{get(){return this.hasAttribute('open');}});
 el.showModal=function(){this.setAttribute('open','');};el.close=function(){this.removeAttribute('open');this.dispatchEvent(new dom.Event('close'));};
}
for(const el of document.querySelectorAll('*')){
 el.focus=()=>{};el.setPointerCapture=()=>{};el.hasPointerCapture=()=>false;
 el.getBoundingClientRect=()=>({left:0,top:0,width:100,height:100});
}
const timers=[];
const context={document,Option,console,queueMicrotask,AbortController,URL,URLSearchParams,TextEncoder,TextDecoder,Blob,Uint8Array,Uint32Array,Int16Array,ArrayBuffer,SharedArrayBuffer,
 crypto:require('node:crypto').webcrypto, performance:{now:()=>context.now},now:100,
 setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout:()=>{},setInterval:()=>1,clearInterval:()=>{},
 requestAnimationFrame:()=>1,cancelAnimationFrame:()=>{},
 navigator:{userAgent:'TestBrowser',getGamepads:()=>[]},location:new URL('http://127.0.0.1:8620/play/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/?touch'),
 matchMedia:()=>({matches:true,addEventListener:()=>{}}),devicePixelRatio:1,innerWidth:844,innerHeight:390,
 screen:{orientation:{}},isSecureContext:true,crossOriginIsolated:true,
 WebAssembly:process.env.PS2_TEST_NO_JSPI?{validate:bytes=>!Array.from(bytes).slice(-4).every((b,i)=>b===[0,0x12,0,0x0b][i])}:WebAssembly,
 OffscreenCanvas:function(){},AudioContext:function(){},AudioWorkletNode:function(){},
 localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,String(v)),removeItem:k=>storage.delete(k)},
 fetch:async()=>({ok:true,json:async()=>({title:'Test game title',poster:true,build:{id:'test-version'}}),text:async()=> 'cdrom0:\\SCUS_971.98;1'}),
 addEventListener:(type,fn)=>{if(!events.has(type))events.set(type,[]);events.get(type).push(fn);},removeEventListener:()=>{},
};context.window=context;context.globalThis=context;
vm.createContext(context);
vm.runInContext(source.split('<script>')[1].split('</script>')[0],context,{filename:'shell.html'});
const run=code=>vm.runInContext(code,context);
if(process.env.PS2_TEST_NO_JSPI){
 const absent=Array.from(run('missing'));
 if(process.env.PS2_TEST_ASYNC_MODE==='asyncify'){assert(!absent.some(x=>/JSPI|tail calls/.test(x)),JSON.stringify(absent));}
 else{assert(absent.some(x=>/JSPI/.test(x)));assert(absent.some(x=>/tail calls/.test(x)));}
}
const emit=(type,el,properties={})=>{const event=new dom.Event(type,{bubbles:true,cancelable:true});Object.assign(event,properties);el.dispatchEvent(event);};
run(`launchOverlay.remove();Module.running=true;Module._ps2web_pad_connected=()=>{};Module._ps2web_pressure=()=>{};Module._ps2web_rumble=()=>0;Module._ps2web_pad=(...v)=>{window.output=v;};`);
const left=document.querySelector('[data-stick="left"]'),right=document.querySelector('[data-stick="right"]'),cross=document.querySelector('[data-slot="14"]');
emit('pointerdown',left,{pointerId:1,clientX:100,clientY:50,pointerType:'touch'});
emit('pointerdown',right,{pointerId:2,clientX:50,clientY:0,pointerType:'touch'});
emit('pointerdown',cross,{pointerId:3,clientX:50,clientY:50,pointerType:'touch'});
run('pollPlayer(0,null,true)');
assert.equal(context.output[1]&16384,16384);assert.equal(context.output[2],255);assert.equal(context.output[5],0);
emit('pointercancel',left,{pointerId:1});emit('pointercancel',right,{pointerId:2});emit('pointercancel',cross,{pointerId:3});
context.now=300;run('pollPlayer(0,null,true)');assert.deepEqual(Array.from(context.output.slice(1)),[0,128,128,128,128]);
// Focus loss releases all controller sources; settings suppress even gamepad input.
emit('pointerdown',left,{pointerId:4,clientX:0,clientY:50,pointerType:'touch'});
events.get('blur').forEach(fn=>fn());assert.equal(run('fingers.size'),0);
const start=document.querySelector('[data-slot="3"]');emit('pointerdown',start,{pointerId:5,clientX:50,clientY:50,pointerType:'touch'});emit('pointerup',start,{pointerId:5});
run('pollPlayer(0,null,true)');assert.equal(context.output[1]&8,8,'Start tap survives until emulation sample');
run(`clearInput();touchBindings[3]=14;renderTouchBindings();saveTouch();`);
assert.equal(start.getAttribute('aria-label'),'Cross');assert(start.querySelector('svg'));assert.equal(start.dataset.symbol,'cross');
emit('pointerdown',start,{pointerId:6,clientX:50,clientY:50,pointerType:'touch'});run('pollPlayer(0,null,true)');assert.equal(context.output[1]&16384,16384);
run(`toggleControls();pollPlayer(0,{buttons:[{pressed:true,value:1}],axes:[-1,-1,1,1]},true);`);assert.deepEqual(Array.from(context.output.slice(1)),[0,128,128,128,128]);run('controlsDialog.close()');
// Key repeats cannot repulse Start or consume remapping UI clicks.
run(`clearInput();pressInput('Enter');`);const until=run('buttonPulses.get(3)');context.now+=50;run(`pressInput('Enter');`);assert.equal(run('buttonPulses.get(3)'),until);
run(`armed=3;`);emit('mousedown',document.querySelector('#close-pc-controls'),{button:0});assert.equal(run('armed'),3);
// Mouse direction uses independent saved X/Y inversion switches.
run(`clearInput();document.pointerLockElement=mouseCanvas;mouseStick.checked=true;sensitivity.value='5';invertMouseX.checked=false;invertMouseY.checked=false;mouseX=-16;mouseY=16;pollPlayer(0,null,true);`);
assert(context.output[4]<128 && context.output[5]>128);
run(`invertMouseX.checked=true;invertMouseY.checked=true;mouseX=-16;mouseY=16;pollPlayer(0,null,true);`);assert(context.output[4]>128&&context.output[5]<128);
// Strict PNACH parsing rejects unsupported controls and out-of-RAM writes.
assert.equal(run(`parseCheats('[Health]\\npatch=1,EE,00123450,word,00000001').length`),1);
for(const code of ['patch=1,EE,FFFFFFFF,word,00000001','patch=1,EE,00100001,word,1','patch=1,EE,D0000000,extended,1','<script>alert(1)</script>'])assert.throws(()=>run(`parseCheats(${JSON.stringify(code)})`));
run('Module.lastFrameAt=0;Module.running=true');context.now=31000;run('checkFrameProgress()');
assert.equal(document.getElementById('runtime-warning').hidden,false);
run('Module.lastFrameAt=performance.now();checkFrameProgress()');assert.equal(document.getElementById('runtime-warning').hidden,true);
run('Module._ps2web_frames=()=>1801;Module._ps2web_primitives=()=>0;Module.lastFrameAt=performance.now();checkFrameProgress()');
assert.equal(document.getElementById('runtime-warning').hidden,false);assert(document.getElementById('runtime-warning').textContent.includes('drawing'));
run('Module._ps2web_primitives=()=>1;checkFrameProgress()');assert.equal(document.getElementById('runtime-warning').hidden,true);
// Halt must restore the actual removed launch screen and require a reload.
run(`Module.onHalt('test failure');`);assert(document.getElementById('overlay'));assert.equal(document.getElementById('start').textContent,'Reload player');
run("Module.onHalt('missing code at 0x00281360 (ra 0x002812B4)')");assert.equal(run('Module.missingCode.address'),0x281360);
console.log('PASS: full shell execution; dual sticks, multitouch, Start, cancellation, remapping, modal isolation, key repeat, X/Y inversion, cheat validation, halt recovery');

(async()=>{
 await run('gameMetadataReady');
 assert.equal(document.title,'CyberArcade - Test game title');assert.equal(document.getElementById('launch-title').textContent,'Test game title');
 assert.equal(document.getElementById('player-poster').hidden,false);assert(document.querySelector('link[rel="icon"]').href.endsWith('poster.image'));
 assert.equal(new URL(run("Module.locateFile('ps2web.wasm',location.href)")).searchParams.get('build'),'test-version');
 dom.HTMLCanvasElement.prototype.getContext=()=>({configure:()=>{},getCurrentTexture:()=>({createView:()=>({})})});
 context.requestAnimationFrame=fn=>{fn();return 1;};
 context.navigator.gpu={requestAdapter:async()=>({info:{},requestDevice:async()=>({lost:new Promise(()=>{}),destroy:()=>{},queue:{submit:()=>{},onSubmittedWorkDone:async()=>{}},createCommandEncoder:()=>({beginRenderPass:()=>({end:()=>{}}),finish:()=>({})})})}),getPreferredCanvasFormat:()=> 'bgra8unorm'};
 assert.equal(await run('canPresent()'),'default adapter','privacy-scrubbed adapter info still succeeds');
 run(`window.realCanPresent=canPresent;canPresent=async power=>power?null:'default adapter';Module.ENV={};`);
 assert.equal(await run('chooseGpu()'),'GPU default adapter');assert.equal(run('Module.ENV.PS2_GPU_DEFAULT'),'1');
 console.log('PASS: GPU default-adapter fallback and privacy-scrubbed adapter metadata');
 // Browser autoplay restrictions must not hold the game behind another Start click.
 context.AudioContext=class {
   constructor(){this.state='suspended';this.audioWorklet={addModule:async()=>{}};this.destination={};}
   resume(){return new Promise(()=>{});}
   createGain(){return {gain:{value:1},connect:()=>({})};}
   addEventListener(){} close(){return Promise.resolve();}
 };
 context.AudioWorkletNode=class {connect(gain){return gain;}};
 run(`missing.length=0;Module.halted=false;Module.started=false;Module.running=false;Module.discSize=100;Module.HEAPU8=new Uint8Array(64);Module._ps2web_audio_ring=()=>0;Module.callMain=()=>{window.autoStarted=true;};Module.onRuntimeInitialized();`);
 for(let i=0;i<8;i++)await new Promise(setImmediate);
 assert.equal(context.autoStarted,true);assert.equal(document.getElementById('sound-unlock').hidden,false);
 assert(document.getElementById('overlay'),'boot stays visible until drawing starts');
 run('last=performance.now();Module.onFrame()');assert(!document.getElementById('overlay'),'drawing dismisses console boot');
 console.log('PASS: automatic startup with suspended audio; first drawing dismisses boot');

})().catch(error=>{console.error(error);process.exitCode=1;});
