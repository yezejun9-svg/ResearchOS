import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../product-v1-native-layout-visual-prepare-07/real-electron-flow.mjs',import.meta.url),'utf8');
const start=source.indexOf('visual.findings=visual.scenarios.flatMap(row => {');
const end=source.indexOf('\n    visual.status=',start);
assert(start>=0&&end>start);
const base=()=>({phase:'INITIAL_VIEWPORT',viewport:{requested_width:390,requested_height:844,inner_width:390,inner_height:844},requested_theme:'dark',actual_theme:'dark',rects:{canvas:{},transcript:{},composer:{},heading:{},actions:[{},{},{}]},horizontal_overflow:false,composer_overlaps_content:[],composer_center_in_view:false,composer_center_hit:false,heading_visible:true,heading_center_in_view:false,heading_center_hit:false,actions_center_in_view:[false,false,false],actions_center_hit:[false,false,false],action_index:null});
const classify=rows=>{const context={visual:{scenarios:rows}};vm.runInNewContext(source.slice(start,end),context);return [...context.visual.findings];};
assert.equal(classify([base()]).length,0); // Partial visibility with offscreen center is not occlusion.
const covered={...base(),heading_center_in_view:true};
assert(classify([covered]).some(x=>x.endsWith(':HEADING_COVERED_INITIAL')));
const recovered={...base(),phase:'HEADING_SCROLLED',heading_center_in_view:true,heading_center_hit:true};
assert(classify([covered,recovered]).some(x=>x.endsWith(':HEADING_COVERED_INITIAL'))); // Scroll cannot erase initial failure.
assert(classify([{...base(),composer_overlaps_content:['action_0']}]).some(x=>x.includes(':COMPOSER_OVERLAP:action_0')));
assert(classify([{...base(),phase:'HEADING_SCROLLED'}]).some(x=>x.endsWith(':HEADING_INACCESSIBLE_AFTER_SCROLL')));
assert(classify([{...base(),phase:'ACTION_SCROLLED_AND_FOCUSED',action_index:0,action_focused:true}]).some(x=>x.endsWith(':ACTION_INACCESSIBLE')));
assert(classify([{...base(),horizontal_overflow:true}]).some(x=>x.endsWith(':HORIZONTAL_OVERFLOW')));
assert(classify([{...base(),actual_theme:'light'}]).some(x=>x.endsWith(':THEME_MISMATCH')));
console.log(JSON.stringify({scope:'EXTRACTED_CLASSIFIER_ONLY',cases:8,passed:8,runner_import:0,app:0,gui:0,cli:0,model:0,formal_increment:0}));
