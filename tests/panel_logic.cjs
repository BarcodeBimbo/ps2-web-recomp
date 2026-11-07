// Functional panel regression with a DOM and synthetic API responses.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let pkg;try{pkg=require(process.env.LINKEDOM_PATH||'linkedom');}catch{pkg=require('/tmp/ps2-test-dom/node_modules/linkedom');}
const {parseHTML}=pkg,source=fs.readFileSync(require('node:path').join(__dirname,'../web/panel.html'),'utf8');
const {document,window}=parseHTML(source);
Object.defineProperty(window.HTMLSelectElement.prototype,'value',{configurable:true,get(){return this._value??this.querySelector('option')?.value??'';},set(v){this._value=String(v);}});
for(const form of document.querySelectorAll('form')){
 const elements={};for(const input of form.querySelectorAll('[name]'))elements[input.name]=input;
 const defaults=new Map(Object.values(elements).map(input=>[input,input.getAttribute('value')||'']));
 form.elements=elements;form.reset=()=>{for(const input of Object.values(elements))input.value=defaults.get(input);};
}
for(const el of document.querySelectorAll('dialog')){
 Object.defineProperty(el,'open',{get(){return this.hasAttribute('open');}});
 el.showModal=()=>el.setAttribute('open','');el.close=()=>{el.removeAttribute('open');el.dispatchEvent(new window.Event('close'));};
}
for(const el of document.querySelectorAll('*')){el.focus=()=>{};el.getBoundingClientRect=()=>({left:0,bottom:0});}
class FormData{constructor(form){this.form=form;}*[Symbol.iterator](){for(const [name,input]of Object.entries(this.form.elements))yield[name,input.value];}}
let failure=true,received=null,downloadReceived=null;
const game={id:'a'.repeat(32),title:'Test game',status:'ready',poster:true};
const context={document,console,FormData,URL,URLSearchParams,FileReader:class{},innerWidth:1280,innerHeight:900,setTimeout:()=>1,addEventListener:()=>{},confirm:()=>true,
 fetch:async(path,options)=>{
  let result=[],status=200;
  if(path==='/api/games'&&!options?.method)result=[game];
  if(path==='/api/archive-check')result={archive:true,needs_password:true};
  if(path==='/api/games'&&options?.method){received=JSON.parse(options.body);if(failure){status=400;result={error:'Synthetic request failure'};}else result={id:'b'.repeat(32)};}
  if(path==='/api/store/download'){downloadReceived=JSON.parse(options.body);result={id:'download'};}
  if(path==='/api/store/versions')result=[{filename:'Fixture.zip',title:'Fixture',url:'https://example.com/fixture.zip'}];
  if(String(path).startsWith('/api/store/catalog')){
    const source=String(path).includes('source=web')?'web':'torrent';
    result=source==='torrent'
      ?{games:[{title:'Torrent game',url:'torrent:0',poster:'',downloads:'',size:'1.2 G',source:'torrent'}],page:1,pages:2,query:'',source:'torrent',total:1}
      :{games:[{title:'Catalog game',url:'https://romsfun.com/roms/playstation-2/game.html',poster:'',downloads:'',size:'',source:'web'}],page:1,pages:3,query:'',source:'web'};
  }
  return{ok:status<400,status,headers:{get:()=> 'application/json'},json:async()=>result};
 }};context.window=context;vm.createContext(context);
vm.runInContext(source.split('<script>')[1].split('</script>')[0],context);
const run=code=>vm.runInContext(code,context),flush=async()=>{for(let i=0;i<8;i++)await new Promise(setImmediate);};
(async()=>{
 await flush();assert.equal(document.title,'CyberArcade - Home');assert.equal(document.querySelectorAll('#games article').length,1);
 const poster=document.querySelector('#games .cover img'),link=document.querySelector('#games .poster-open');
 assert.equal(link.getAttribute('aria-label'),'Play Test game');assert.equal(link.href,'/play/'+game.id+'/');assert(!document.querySelector('#games .badge.ready'));assert(!document.querySelector('#game-info').open);
 assert(!document.querySelector('#games .card-body a'));
 game.progress={step:1,total:6,count:100,done:1};await run('refresh()');
 assert.equal(document.querySelector('#games .cover img'),poster,'progress preserves ready posters');
 game.status='building';await run('refresh()');
 const card=document.querySelector('#games article'),buildingPoster=card.querySelector('img'),progress=card.querySelector('progress');
 game.progress.done=50;await run('refresh()');
 assert.equal(document.querySelector('#games article'),card);assert.equal(card.querySelector('img'),buildingPoster);assert.equal(card.querySelector('progress'),progress);assert.equal(progress.value,.5);
 game.status='ready';await run('refresh()');
 run("selectView('store')");await flush();assert(!document.querySelector('#store-view').hidden);assert(document.querySelector('#store-search'));assert(document.querySelector('#store-next'));
 assert.equal(document.title,'CyberArcade - Store');
 assert(!document.querySelector('#open-direct'));
 assert.equal(document.querySelectorAll('#store-games article').length,1);
 assert.equal(document.querySelector('#store-games h3').textContent,'Torrent game');
 document.querySelector('#store-games button').click();await flush();
 assert.equal(downloadReceived.url,'torrent:0');
 assert.equal(document.title,'CyberArcade - Downloads');
 run("selectView('library');setAddMode('network')");await flush();
 assert(document.querySelector('#add-network') && !document.querySelector('#add-network').hidden);
 assert(document.querySelector('#add-local').hidden);
 run("selectView('store')");await flush();
 run("selectView('downloads')");await flush();assert(!document.querySelector('#downloads-view').hidden);
 run("selectView('library');addDialog.showModal();form.elements.path.value='/tmp/game.zip';form.elements.password.value='known password';form.elements.frames.value='3600';form.elements.rounds.value='0';");
 assert(!document.querySelector('#password-field').hidden);
 document.querySelector('#add').dispatchEvent(new window.Event('submit',{bubbles:true,cancelable:true}));await flush();
 assert.equal(received.password,'known password');assert.equal(run('form.elements.password.value'),'known password');assert(document.querySelector('#add-dialog').open);
 failure=false;document.querySelector('#add').dispatchEvent(new window.Event('submit',{bubbles:true,cancelable:true}));await flush();
 assert.equal(received.password,'known password');assert.equal(run('form.elements.password.value'),'');assert(!document.querySelector('#add-dialog').open);
 assert.equal(document.title,'CyberArcade - Library');
 run("setAddMode('network')");document.querySelector('#network-url').value='https://example.com/fixture.zip';document.querySelector('#network-password').value='custom-secret';
 document.querySelector('#network-submit').click();await flush();
 assert.equal(downloadReceived.password,'custom-secret');assert.equal(downloadReceived.url,'https://example.com/fixture.zip');
 assert.equal(document.title,'CyberArcade - Downloads');
 console.log('PASS: panel execution; library/store/downloads navigation, torrent store, add-game network mode, encrypted-password entry, request-failure retry and successful submission clearing');
})().catch(e=>{console.error(e);process.exitCode=1;});
