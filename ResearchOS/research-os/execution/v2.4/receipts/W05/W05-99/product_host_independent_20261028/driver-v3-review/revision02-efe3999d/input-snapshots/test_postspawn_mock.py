"""Pure mock checks for wrapper revision02. No product or native subprocess is started."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SOURCE = Path(__file__).with_name('run-owned.py')
spec = importlib.util.spec_from_file_location('native_wrapper_revision02', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeStream:
    def __init__(self, fail=False): self.fail=fail
    def close(self):
        if self.fail: raise OSError('stream close failed')


class FakeController:
    pid=12345
    def __init__(self, wait_error=None, code=0):
        self.wait_error=wait_error
        self.code=code
    def wait(self, timeout=None):
        if self.wait_error: raise self.wait_error
        return self.code
    def poll(self): return self.code


class PostspawnTests(unittest.TestCase):
    def observe(self, child, stdout=None, stderr=None):
        with tempfile.TemporaryDirectory() as raw:
            out=Path(raw)
            return module.observe_started_controller({},out,out,child,
                {'pid':child.pid},(stdout or FakeStream(),stderr or FakeStream()),
                'scope',{},{} )

    def test_spawn_receipt_failure_enters_hold_with_same_handle(self):
        child=FakeController()
        with mock.patch.object(module,'write_new',side_effect=OSError('spawn receipt failed')), \
                mock.patch.object(module,'hold_postspawn',return_value='HELD') as hold:
            self.assertEqual(self.observe(child),'HELD')
        self.assertIs(hold.call_args.args[3],child)
        self.assertIsInstance(hold.call_args.args[-1],OSError)

    def test_wait_failure_enters_hold_with_same_handle(self):
        child=FakeController(wait_error=RuntimeError('wait failed'))
        with mock.patch.object(module,'write_new'),mock.patch.object(module,'safe_print'), \
                mock.patch.object(module,'hold_postspawn',return_value='HELD') as hold:
            self.assertEqual(self.observe(child),'HELD')
        self.assertIs(hold.call_args.args[3],child)
        self.assertIn('wait failed',str(hold.call_args.args[-1]))

    def test_stream_close_failure_enters_hold(self):
        child=FakeController()
        with mock.patch.object(module,'write_new'),mock.patch.object(module,'safe_print'), \
                mock.patch.object(module,'hold_postspawn',return_value='HELD') as hold:
            self.assertEqual(self.observe(child,stdout=FakeStream(fail=True)),'HELD')
        self.assertIs(hold.call_args.args[3],child)

    def test_holder_observes_terminal_after_wait_exception(self):
        child=FakeController(wait_error=RuntimeError('transient wait'))
        polls=iter([None,0])
        child.poll=lambda: next(polls)
        writes=[]
        def retry_spawn_receipt(*_args):
            writes.append(1)
            if len(writes)==1: raise OSError('first spawn receipt write failed')
        with tempfile.TemporaryDirectory() as raw:
            out=Path(raw)
            with mock.patch.object(module,'write_or_verify',side_effect=retry_spawn_receipt), \
                    mock.patch.object(module,'safe_print'), \
                    mock.patch.object(module.time,'sleep'), \
                    mock.patch.object(module.signal,'signal'), \
                    mock.patch.object(module,'hold_failed_controller',return_value='ROOT_WAIT') as hold:
                result=module.hold_postspawn({},out,out,child,{'pid':child.pid},
                    (FakeStream(),FakeStream()),'scope',{}, {},OSError('spawn receipt failed'))
            self.assertEqual(result,'ROOT_WAIT')
            self.assertGreaterEqual(len(writes),2)
            self.assertEqual(hold.call_args.args[3],child.pid)
            self.assertEqual(hold.call_args.args[4],0)

    def test_reused_known_pid_and_exact_bundle_image_block_release(self):
        image=module.normpath('C:/owned/electron.exe')
        known=[{'pid':11,'image':image,'created_ns':'123'}]
        observation={'status':'OBSERVED','rows':[
            {'pid':11,'image':'C:/other/notepad.exe','created_ns':'999','read_error':None},
            {'pid':12,'image':'C:/owned/electron.exe','created_ns':'234','read_error':None}]}
        blocked=module.blockers(observation,known,{image:'C:/owned/electron.exe'})
        self.assertIn('KNOWN_PID_REUSED_OR_IDENTITY_UNKNOWN:11',blocked)
        self.assertIn('EXACT_BUNDLE_IMAGE_STILL_RUNNING:12',blocked)
        self.assertIn('$knownPids -notcontains [int]$item.ProcessId',module.SCAN_SCRIPT)


if __name__=='__main__': unittest.main()
