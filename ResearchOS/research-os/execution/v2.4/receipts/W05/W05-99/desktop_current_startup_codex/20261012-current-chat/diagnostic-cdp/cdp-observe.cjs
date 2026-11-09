const fs=require('node:fs'), path=require('node:path');
const pwPath='C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package';
const pw=require(pwPath); const [, , port,out]=process.argv;
const save=(n,v)=>fs.writeFileSync(path.join(out,n),JSON.stringify(v,null,2)+'\n');
let browser; const errors=[]; const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{const report={mode:'ACTUAL_NATIVE_DESKTOP_READ_ONLY_DIAGNOSIS',provider_calls:0,ui_flow_accepted:false,driver_version:require(path.join(pwPath,'package.json')).version};
try {let last; for(let i=0;i<40;i++){try{browser=await pw.chromium.connectOverCDP('http://127.0.0.1:'+port,{timeout:1000});break;}catch(e){last=String(e);await delay(250);}}
if(!browser)throw Error('CDP_UNREACHABLE:'+last);const pages=browser.contexts().flatMap(c=>c.pages());report.page_count=pages.length;report.pages=pages.map(p=>p.url());
const page=pages.find(p=>p.url().startsWith('ros-app:'))||pages[0];if(!page)throw Error('NO_BROWSER_WINDOW');
page.on('pageerror',e=>errors.push({kind:'pageerror',error:String(e)}));page.on('console',m=>{if(m.type()==='error')errors.push({kind:'console',error:m.text()});});page.on('requestfailed',r=>errors.push({kind:'requestfailed',url:r.url(),error:r.failure()?.errorText}));
try{await page.locator('body').waitFor({timeout:10000});await delay(1000);report.state=await page.evaluate(()=>({url:location.href,title:document.title,body:document.body?.innerText.slice(0,12000),headings:[...document.querySelectorAll('h1,h2,h3')].map(x=>x.textContent),root:!!document.querySelector('#root'),bridge:!!window.researchos?.desktop,model_config_controls:[...document.querySelectorAll('input,button,select')].map(e=>({tag:e.tagName,type:e.type||null,label:e.getAttribute('aria-label')||e.textContent?.slice(0,100)}))}));await page.screenshot({path:path.join(out,'desktop-current.png'),timeout:10000});report.screenshot=true;}catch(e){report.page_error=String(e);}
report.status=report.state?.root&&report.state?.bridge?'OBSERVED_CURRENT_DESKTOP':'DIAGNOSTIC_ONLY';}
catch(e){report.status='DIAGNOSTIC_FAILURE';report.error=String(e);process.exitCode=1;}
finally{report.renderer_errors=errors;save('cdp-result.json',report);if(browser)try{await browser.close();}catch{}console.log(JSON.stringify(report));}})();