// Source-extracted pure geometry checks. Never imports or launches the runner.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(here, 'real-electron-flow.mjs'), 'utf8');
const start = source.indexOf('const initialScrollReset = row =>');
const end = source.indexOf('    visual.status=', start);
if (start < 0 || end < 0 || source.indexOf('const initialScrollReset = row =>', start + 1) >= 0)
  throw new Error('REV11_GEOMETRY_SOURCE_DRIFT');
const gate = source.slice(start, end);
const box = (x,y,width,height) => ({x,y,right:x+width,bottom:y+height,width,height});
const base = () => ({
  viewport:{requested_width:390,requested_height:844,inner_width:390,inner_height:844},
  requested_theme:'light',actual_theme:'light',phase:'INITIAL_VIEWPORT',action_index:null,
  document:{scroll_y:0},transcript_scroll:{scroll_top:0},
  main_area_scroll:{scroll_top:0,scroll_width:390,client_width:390,rect:box(0,56,390,724)},
  grid_scroll:{scroll_width:390,client_width:390},horizontal_overflow:false,
  rects:{grid:box(0,56,390,724),topbar:box(0,0,390,56),main:box(0,56,390,724),
    bottom_nav:box(0,780,390,64),canvas:box(10,200,370,500),transcript:box(10,210,370,320),
    composer:box(10,540,370,150),input:box(20,580,350,50),send:box(270,645,100,40),
    heading:box(20,220,200,40),actions:[box(20,300,100,40),box(140,300,100,40),box(260,300,100,40)],
    context:box(10,700,370,70),activity:box(10,710,370,50),activity_empty:box(20,725,340,25),
    workspace_row:box(10,90,370,50),history_summary:box(10,150,370,40),
    harness_select:box(20,100,200,44),readiness:box(10,500,370,40),
    readonly_status:box(20,502,350,16),permission_summary:box(20,520,350,8),permission_reason:box(20,529,350,8)},
  clipped_rects:{composer:box(10,540,370,150),input:box(20,580,350,50),send:box(270,645,100,40)},
  heading_center_in_view:true,heading_center_hit:true,actions_center_in_view:[true,true,true],
  actions_center_hit:[true,true,true],composer_center_in_view:true,composer_center_hit:true,
  input_center_in_view:true,input_center_hit:true,send_center_in_view:true,send_center_hit:true,
  history_collapsed:true,history_center_in_view:true,history_center_hit:true,
  readiness_visible:true,readiness_text:'只读任务 · 执行 UNVERIFIED · 范围 UNVERIFIED',
  permission_text:'暂不可提交只读任务',permission_visible:true,
  readonly_status_clip:box(20,502,350,16),readonly_status_hit:true,
  permission_summary_clip:box(20,520,350,8),permission_summary_hit:true,
  permission_reason_clip:box(20,529,350,8),permission_reason_hit:true,
  workspace_row_clip:box(10,90,370,50),context_clip:box(10,700,370,70),
  history_empty_text:'暂无已记录任务',activity_empty_text:'每一步，都有迹可循',activity_record_count:0,
  activity_empty_center_in_view:true,activity_empty_center_hit:true,
  task_record_count:0,input_value:'',nav_visible:true,harness_select_center_hit:true,selected_harness:'codex',
  composer_overlaps_content:[]
});
const findings = row => {
  const visual = {scenarios:[row],findings:[]};
  vm.runInNewContext(gate, {visual});
  return Array.from(visual.findings);
};
const check = (value,code) => { if (!value) throw new Error(code); };
const caseOf = (mutate, expected) => {
  const row=base(); mutate(row);
  check(findings(row).some(item=>item.endsWith(':'+expected)), 'MISSING_'+expected);
};
check(findings(base()).length===0,'BASELINE_FALSE_POSITIVE');
caseOf(r=>{r.rects.composer.y=790;r.rects.composer.bottom=940},'FIRST_SCREEN_COMPOSER_REQUIRES_SCROLL_OR_IS_COVERED');
caseOf(r=>{r.clipped_rects.input.bottom=610},'FIRST_SCREEN_COMPOSER_REQUIRES_SCROLL_OR_IS_COVERED');
caseOf(r=>{r.send_center_hit=false},'FIRST_SCREEN_COMPOSER_REQUIRES_SCROLL_OR_IS_COVERED');
caseOf(r=>{r.history_collapsed=false},'HISTORY_NOT_COLLAPSED_AND_ACCESSIBLE');
caseOf(r=>{r.readiness_text='Ready'},'UNVERIFIED_PERMISSION_OR_BLOCKER_NOT_NEAR_INPUT');
caseOf(r=>{r.rects.readiness.y=0;r.rects.readiness.bottom=40},'UNVERIFIED_PERMISSION_OR_BLOCKER_NOT_NEAR_INPUT');
caseOf(r=>{r.permission_reason_clip.height=1;r.permission_reason_clip.bottom=r.permission_reason_clip.y+1},'UNVERIFIED_PERMISSION_OR_BLOCKER_NOT_NEAR_INPUT');
caseOf(r=>{r.permission_reason_hit=false},'UNVERIFIED_PERMISSION_OR_BLOCKER_NOT_NEAR_INPUT');
caseOf(r=>{r.permission_visible=false},'UNVERIFIED_PERMISSION_OR_BLOCKER_NOT_NEAR_INPUT');
caseOf(r=>{r.task_record_count=1},'FRESH_EMPTY_STATE_OR_REAL_RECORDS_MISMATCH');
caseOf(r=>{r.activity_record_count=1},'FRESH_EMPTY_STATE_OR_REAL_RECORDS_MISMATCH');
caseOf(r=>{r.history_empty_text=''},'FRESH_EMPTY_STATE_OR_REAL_RECORDS_MISMATCH');
caseOf(r=>{r.workspace_row_clip.height=2;r.workspace_row_clip.bottom=r.workspace_row_clip.y+2},'WORKSPACE_OR_HISTORY_NOT_COMPACT_ACCESSIBLE');
caseOf(r=>{r.input_value='unexpected'},'FRESH_DRAFT_NOT_EMPTY');
caseOf(r=>{r.rects.main.bottom=810},'MOBILE_NAV_OR_SAFE_AREA_OVERLAP');
caseOf(r=>{r.main_area_scroll.scroll_width=400},'ROOT_OR_MAIN_HORIZONTAL_OVERFLOW');
caseOf(r=>{r.document.scroll_y=2},'INITIAL_SCROLL_NOT_RESET');
caseOf(r=>{r.transcript_scroll.scroll_top=2},'INITIAL_SCROLL_NOT_RESET');
caseOf(r=>{r.main_area_scroll.scroll_top=2},'INITIAL_SCROLL_NOT_RESET');
caseOf(r=>{r.harness_select_center_hit=false},'HARNESS_CONTROL_INACCESSIBLE');
caseOf(r=>{r.phase='MOBILE_CONTEXT_SCROLLED';r.activity_empty_center_hit=false},'MOBILE_CONTEXT_ACTIVITY_UNREACHABLE');
caseOf(r=>{r.phase='REDUCED_VIEWPORT_SIMULATED_KEYBOARD';r.send_center_hit=false},'REDUCED_VIEWPORT_INPUT_OR_NAV_OVERLAP');
console.log(JSON.stringify({schema:'researchos.native-layout-visual12-pure/1',
  cases:23,runner_import:0,app:0,native:0,cli:0,model:0,task:0}));
