"""An independent bounded timer owns a duplicate Job handle during callback."""
import ctypes, threading, time
from ctypes import wintypes
class JobDeadlineWatchdog:
    def __init__(self,job_handle,deadline):
        self.deadline=deadline;self.stop=threading.Event();self.thread=None;self.thread_started=False
        self.observation={"deadline_monotonic":deadline,"termination_requested":False,
                          "termination_succeeded":None,"duplicate_handle_closed":False,"errors":[]}
        k=ctypes.WinDLL("kernel32",use_last_error=True);H=ctypes.c_void_p;D=wintypes.DWORD;B=wintypes.BOOL
        self.current=k.GetCurrentProcess;self.current.argtypes=[];self.current.restype=H
        dup=k.DuplicateHandle;dup.argtypes=[H,H,H,ctypes.POINTER(H),D,B,D];dup.restype=B
        self.terminate=k.TerminateJobObject;self.terminate.argtypes=[H,wintypes.UINT];self.terminate.restype=B
        self.close=k.CloseHandle;self.close.argtypes=[H];self.close.restype=B
        handle=H();process=self.current()
        if not dup(process,job_handle,process,ctypes.byref(handle),0,False,2):
            raise ctypes.WinError(ctypes.get_last_error())
        self.handle=handle
    def start(self):
        if self.thread is not None:raise RuntimeError("watchdog already started")
        def watch():
            try:
                while not self.stop.is_set():
                    remaining=self.deadline-time.monotonic()
                    if remaining<=0:
                        self.observation["termination_requested"]=True
                        ok=bool(self.terminate(self.handle,0xE0000410))
                        self.observation["termination_succeeded"]=ok
                        self.observation["termination_monotonic"]=time.monotonic()
                        if not ok:self.observation["errors"].append("TerminateJobObject WinError "+str(ctypes.get_last_error()))
                        return
                    self.stop.wait(min(0.02,remaining))
            except BaseException as exc:self.observation["errors"].append(repr(exc))
        self.thread=threading.Thread(target=watch,daemon=True)
        try:
            self.thread.start()
            self.thread_started=True
        except BaseException as exc:
            self.observation["errors"].append("Thread.start failed: "+repr(exc))
            raise
    def stop_and_close(self):
        self.stop.set()
        if self.thread is not None and self.thread_started:
            self.thread.join(2)
            if self.thread.is_alive():
                self.observation["errors"].append("watchdog failed to stop; duplicate Job handle retained")
                return self.observation
        if self.handle is not None:
            if self.close(self.handle):self.observation["duplicate_handle_closed"]=True;self.handle=None
            else:self.observation["errors"].append("CloseHandle WinError "+str(ctypes.get_last_error()))
        return self.observation
