// Extract candidate 09 geometry functions only; no runner import or browser.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const source=fs.readFileSync(path.join(here,'real-electron-flow.mjs'),'utf8');
const slice=(a,b)=>{const x=source.indexOf(a),y=source.indexOf(b,x+a.length);
  if(x<0||y<0||source.indexOf(a,x+1)>=0)throw new Error('CLIP_SOURCE_MARKER_DRIFT');return source.slice(x,y)};
const funcs=slice('const rect = e =>','\n        const mainArea=')+
  slice('const intersects=(a,b)=>','\n        const hc=')+
  slice('const hit=e=>','\n        const centerIn=');
const box=(x,y,w,h)=>({x,y,right:x+w,bottom:y+h,width:w,height:h});
const element=(r,parent=null,overflowX='visible',overflowY='visible',name='node')=>({
  parentElement:parent,style:{overflowX,overflowY},tagName:'DIV',className:name,
  clientLeft:0,clientTop:0,clientWidth:r.width,clientHeight:r.height,
  getBoundingClientRect:()=>r,querySelectorAll:()=>[]});
let topElement=null;
const context={innerWidth:390,innerHeight:844,getComputedStyle:e=>e.style,
  document:{elementFromPoint:()=>topElement}};
const {clipFor,hit}=vm.runInNewContext(`(()=>{${funcs};return {clipFor,hit}})()`,context);
const check=(value,code)=>{if(!value)throw new Error(code)};
const nav=element(box(0,780,390,64),null,'visible','visible','nav');
const grid=element(box(0,0,390,844),null,'visible','visible','grid');
const mainAuto=element(box(0,0,390,780),grid,'visible','auto','main');
const transcriptAuto=element(box(0,0,390,820),mainAuto,'auto','auto','transcript');
const buttonClipped=element(box(10,780,120,22),transcriptAuto,'visible','visible','button');
check(clipFor(buttonClipped).rect===null,'MAIN_AUTO_DID_NOT_CLIP_AT_780');
check(clipFor(buttonClipped).chain.some(x=>x.class_name==='main'&&x.y_applied&&x.client_bounds.bottom===780),'MAIN_CLIPCHAIN_MISSING');
const mainVisible=element(box(0,0,390,780),grid,'visible','visible','main');
const transcriptVisible=element(box(0,0,390,820),mainVisible,'visible','visible','transcript');
const buttonVisible=element(box(10,780,120,22),transcriptVisible,'visible','visible','button');
check(!!clipFor(buttonVisible).rect,'OVERFLOW_VISIBLE_WRONGLY_CLIPPED');
topElement=nav;
check(!hit(buttonVisible),'VISIBLE_NAV_OCCLUSION_NOT_FOUND');
const buttonScrolled=element(box(10,700,120,44),transcriptAuto,'visible','visible','button');
topElement=buttonScrolled;
check(!!clipFor(buttonScrolled).rect&&hit(buttonScrolled),'SCROLLED_ACCESSIBLE_CONTROL_REJECTED');
topElement=nav;
check(!hit(buttonScrolled),'SCROLLED_OCCLUSION_NOT_FOUND');
const composerClipped=element(box(10,780,300,44),mainAuto,'visible','visible','composer');
check(clipFor(composerClipped).rect===null,'COMPOSER_NOT_ANCESTOR_CLIPPED');
const xOnly=element(box(0,0,300,780),grid,'hidden','visible','xonly');
check(!!clipFor(element(box(10,780,100,22),xOnly)).rect,'X_ONLY_WRONGLY_CLIPPED_Y');
const yOnly=element(box(0,0,300,780),grid,'visible','auto','yonly');
check(!!clipFor(element(box(310,100,30,22),yOnly)).rect,'Y_ONLY_WRONGLY_CLIPPED_X');
const inset=element(box(0,0,390,780),grid,'hidden','hidden','inset');
inset.clientLeft=5;inset.clientTop=7;inset.clientWidth=280;inset.clientHeight=500;
const insetClip=clipFor(element(box(2,5,10,10),inset)).rect;
check(insetClip?.x===5&&insetClip?.y===7&&insetClip?.right===12&&insetClip?.bottom===15,'CLIENT_INSET_BOUNDS_WRONG');
check(source.includes('actions_center_in_view:ac.map')&&source.includes('actions_center_hit:actions.map(hit)')&&source.includes('row.action_focused'),'SCROLLED_ACTION_GATES_DRIFT');
console.log(JSON.stringify({schema:'researchos.native-layout-visual09-ancestor-clip-pure/1',cases:['main_auto_780_clips','main_clipchain','overflow_visible_preserves','visible_nav_occlusion','scrolled_accessible','scrolled_occlusion','composer_clipped','x_only_preserves_y','y_only_preserves_x','client_inset_bounds','action_gates'],runner_import:0,app:0,native:0,cli:0,model:0,task:0}));
