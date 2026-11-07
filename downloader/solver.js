// Optional, server-only Turnstile adapter from the supplied downloader flow.
export async function installSolver(context, key, emit) {
  if(!key) return;
  await context.route('**/turnstile/**/api.js*', async route=>{
    const onload = new URL(route.request().url()).searchParams.get('onload');
    await route.fulfill({status:200,contentType:'application/javascript',body:`
      window.turnstile={render(container,options){window.__sgTurnstile=options;return 'sg-widget';},ready(cb){cb?.();},implicit(){}};
      const callback=window[${JSON.stringify(onload)}];if(typeof callback==='function')callback();
    `});
  });
}
export async function solveIfNeeded(page, key, emit) {
  if(!key) return;
  const params = await page.evaluate(()=>{
    const p=window.__sgTurnstile;
    return p?{sitekey:p.sitekey,action:p.action,cData:p.cData,chlPageData:p.chlPageData}:null;
  });
  if(!params?.sitekey) return;
  emit({event:'status',message:'Completing provider verification…'});
  const post=async(endpoint,body)=>{
    const response=await fetch(`https://api.2captcha.com/${endpoint}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(20000)});
    if(!response.ok)throw new Error('Verification service unavailable.');
    const result=await response.json();if(result.errorId)throw new Error('Verification service rejected the request.');return result;
  };
  const task={type:'TurnstileTaskProxyless',websiteURL:page.url(),websiteKey:params.sitekey};
  if(params.action)task.action=params.action;if(params.cData)task.data=params.cData;if(params.chlPageData)task.pagedata=params.chlPageData;
  const created=await post('createTask',{clientKey:key,task});
  for(let attempt=0;attempt<30;attempt++){
    await new Promise(resolve=>setTimeout(resolve,5000));
    const result=await post('getTaskResult',{clientKey:key,taskId:created.taskId});
    if(result.status==='ready' && typeof result.solution?.token==='string'){
      if(result.solution.userAgent){
        const session=await page.context().newCDPSession(page);
        await session.send('Emulation.setUserAgentOverride',{userAgent:result.solution.userAgent});
      }
      await page.evaluate(token=>{
        for(const input of document.querySelectorAll('[name="cf-turnstile-response"]')) input.value=token;
        window.__sgTurnstile?.callback?.(token);
      },result.solution.token);return;
    }
  }
  throw new Error('Provider verification timed out.');
}
