"""Check the actual native consent text against the authorized exact scope, then click its observed button."""
import argparse,ctypes,datetime,hashlib,json,re
from ctypes import wintypes as w
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--capture',required=True);p.add_argument('--receipt',required=True);p.add_argument('--pid',required=True,type=int);p.add_argument('--core-pid',required=True,type=int);a=p.parse_args()
R=Path('D:/作品集/ResearchOS/research-os');rows=json.loads(Path(a.capture).read_text(encoding='utf8'));rows=rows if isinstance(rows,list) else [rows];children=[c for row in rows for c in row['children']]
details=[c['name'] for c in children if c['name'].startswith('主机：')];assert len(details)==1;detail=details[0]
s=json.loads((R/'execution/v2.4/receipts/W05/W05-99/own_cli_product_target_preparation_codex/20261012-current-chat/coding-scope-draft-01.json').read_text(encoding='utf8'))['intent_fields_without_live_context'];check=s['checks'][0]
required=[f'控制进程 PID {a.core_pid}；桌面进程 PID {a.pid}','项目：a7ebcf2a322c6abcf87e043f601ee804；会话：a09d4435036b2b32a0d7076bfc53fd93','当前模型：mc-079c6ca85595aaac2dd17c2d0ed77b93','路径：D:\\作品集\\ResearchOS\\research-os\\.local\\worktrees\\w05-own-cli-product-agent-20261012','工作区引用：wsref-6243c8b1dd686be2；修订：2；权限：READ_WRITE','可读：'+'、'.join(s['read_paths'])+'\n','可写：'+'、'.join(s['write_paths'])+'\n',f"检查 {check['id']}：{check['package']}，{check['test_pattern']}；源文件 "+'、'.join(check['source_paths'])+'\n','普通模型调用上限 8 次；资格验证上限 1 次模型调用、0 次工具调用；当前模型调用 0 次','单文件读取 65536 字节；单文件写入 65536 字节；工具调用上限 32；模型输出上限 8192 token','超时 120 秒；进程 32；内存 1024 MiB；文本 8192 字节','Go 工具链：D:\\作品集\\ResearchOS\\research-os\\.local\\tools\\go1.27.1\\go；离线 vendor：C:\\Users\\yqyyds\\.codex\\researchos-resource-cache\\20261012-own-cli-vendor','源文件 326 个/','确认只保存编码配置；不会调用模型或执行检查。']
assert all(x in detail for x in required),[x[:80] for x in required if x not in detail]
expiry=re.search(r'有效期至：([^\n]+)',detail).group(1);assert datetime.datetime.fromisoformat(expiry.replace('Z','+00:00'))>datetime.datetime.now(datetime.timezone.utc),'Native frozen plan expired; no confirm'
buttons=[c for c in children if c['name']=='确认保存' and c['hwnd']];assert len(buttons)==1;h=buttons[0]['hwnd']
u=ctypes.WinDLL('user32');u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int];u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
pid=w.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(pid));b=ctypes.create_unicode_buffer(100);u.GetWindowTextW(h,b,100);assert pid.value==a.pid and b.value=='确认保存'
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capture_sha256':hashlib.sha256(Path(a.capture).read_bytes()).hexdigest(),'detail_sha256':hashlib.sha256(detail.encode()).hexdigest(),'read_count':326,'write_count':2,'scope_checks':len(required),'limits_match':True,'actual_expiry':expiry,'observed_button':h,'model_calls_displayed':0,'action':'native Confirm Save click'}
with Path(a.receipt).open('x',encoding='utf8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
assert u.PostMessageW(h,0xF5,0,0);print(json.dumps({'native_confirm_save_clicked':True,'scope_checks':len(required),'expiry':expiry}))
