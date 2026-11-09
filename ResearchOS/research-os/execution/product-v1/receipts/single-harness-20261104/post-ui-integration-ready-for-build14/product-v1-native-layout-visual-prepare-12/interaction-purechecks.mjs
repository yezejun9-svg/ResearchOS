// Pure source-extracted predicates; no runner import, browser or application.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const source=fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)),'real-electron-flow.mjs'),'utf8');
const slice=(a,b)=>{const i=source.indexOf(a),j=source.indexOf(b,i+a.length);
  if(i<0||j<0||source.indexOf(a,i+1)>=0)throw new Error('INTERACTION_SOURCE_DRIFT');return source.slice(i,j)};
const appendGate=slice('if(!inputFocused || shiftedDraft!==originalDraft', '\n    const historyControl');
const check=(x,code)=>{if(!x)throw new Error(code)};
const assess=(shiftedDraft,appendedDraft,focusedAfterSuggestion=true)=>{
  const visual={findings:[]};
  vm.runInNewContext(appendGate,{visual,inputFocused:true,originalDraft:'typed',shiftedDraft,
    appendedDraft,suggestionText:'suggested',focusedAfterSuggestion});
  return visual.findings.length===0;
};
check(assess('typed\n','typed\n\n\nsuggested'),'EXACT_APPEND_REJECTED');
check(!assess('typed\n','typed\n\nsuggested'),'LOST_SHIFT_ENTER_SUFFIX_ACCEPTED');
check(!assess('typed\n','typed\n\nother suggested'),'REPLACED_DRAFT_SUFFIX_ACCEPTED');
check(!assess('typed\n','typed\n\n\nsuggested',false),'FOCUS_LOSS_ACCEPTED');
check(source.includes("simulation:'DESKTOP_VIEWPORT_HEIGHT_ONLY_NOT_REAL_OS_KEYBOARD'"),'SIMULATION_LABEL_MISSING');
check(source.includes("page.setViewportSize({width:390,height:500})") &&
  source.includes("page.keyboard.press('Control+End')") &&
  source.includes('reduced.textarea_scroll.top>0'),'LONG_DRAFT_SCROLL_DIAGNOSTIC_MISSING');
console.log(JSON.stringify({schema:'researchos.native-layout-visual12-interaction-pure/1',
  cases:6,runner_import:0,app:0,native:0,cli:0,model:0,task:0}));
