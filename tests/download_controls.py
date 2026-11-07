"""Transfer state transitions with deterministic HTTP byte-range fixtures."""
import io
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import store

DIRECT = 'direct'

class Response(io.BytesIO):
    def __init__(self, data, status=200, headers=None, first=None):
        super().__init__(data)
        self.status = status
        self.headers = {'Content-Length':str(len(data)), 'ETag':'"fixture-v1"', **(headers or {})}
        self.first = first
    def read(self, size=-1):
        if self.first:
            first,self.first=self.first,None
            result=super().read(min(size,3)); first(); return result
        return super().read(size)

def run_download(identifier, url, ext, password, root, importer):
    return store.download(identifier, DIRECT, {'url': url}, ext, password, root, importer)

class Transfers(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        with store.TURN:
            store.JOBS.clear();store.CONTROLS.clear();store.ACTIVE=None
            store.JOBS['a']={'id':'a','title':'Fixture','status':'queued','bytes':0}
            store.CONTROLS['a']={'paused':False,'cancelled':False}
    def wait(self, predicate):
        deadline=time.monotonic()+3
        while not predicate():
            if time.monotonic()>deadline:self.fail('Transfer failed to reach expected state')
            time.sleep(.005)
    def run_resume(self, second, expected, failed=False):
        received=[];requests=[]
        first=Response(b'abcdef',first=lambda:store.control('a','pause'))
        def opener(url,headers=None):
            requests.append(headers)
            return first if len(requests)==1 else second
        with patch.object(store,'open_url',side_effect=opener),patch.object(store.shutil,'disk_usage',return_value=SimpleNamespace(free=1<<40)):
            worker=threading.Thread(target=run_download,args=('a','https://example.com/a.iso','.iso',None,self.root,lambda data:received.append(Path(data['path']).read_bytes()) or {'id':'b'*32}))
            worker.start()
            self.wait(lambda:store.JOBS['a']['status']=='paused' and store.ACTIVE is None)
            self.assertEqual(store.JOBS['a']['bytes'],3)
            store.control('a','resume')
            worker.join(3);self.assertFalse(worker.is_alive())
        self.assertEqual(requests[1].get('Range'),'bytes=3-')
        self.assertEqual(requests[1].get('If-Range'),'"fixture-v1"')
        self.assertIn('Referer', requests[1])
        self.assertEqual(store.JOBS['a']['status'],'failed' if failed else 'complete')
        self.assertEqual(received,[] if failed else [expected])
        self.assertFalse(list(self.root.rglob('*.part')))
        if failed:self.assertFalse(list(self.root.rglob('*.iso')))
    def test_pause_resume_validates_range_and_preserves_bytes(self):
        self.run_resume(Response(b'def',206,{'Content-Range':'bytes 3-5/6'}),b'abcdef')
    def test_server_ignoring_range_restarts_instead_of_appending(self):
        self.run_resume(Response(b'updated'),b'updated')
    def test_changed_validator_never_imports(self):
        self.run_resume(Response(b'def',206,{'Content-Range':'bytes 3-5/6','ETag':'"other"'}),None,True)
    def test_wrong_range_never_imports(self):
        self.run_resume(Response(b'def',206,{'Content-Range':'bytes 2-4/6'}),None,True)
    def test_cancel_queued_never_opens_network_or_imports(self):
        store.control('a','cancel')
        with patch.object(store,'open_url') as opener:
            run_download('a','https://example.com/a.iso','.iso',None,self.root,lambda _:self.fail('Cancelled transfer imported'))
        opener.assert_not_called();self.assertEqual(store.JOBS['a']['status'],'cancelled')
    def test_cancel_in_read_deletes_files(self):
        with patch.object(store,'open_url',return_value=Response(b'abcdef',first=lambda:store.control('a','cancel'))),patch.object(store.shutil,'disk_usage',return_value=SimpleNamespace(free=1<<40)):
            run_download('a','https://example.com/a.iso','.iso',None,self.root,lambda _:self.fail('Cancelled transfer imported'))
        self.assertFalse(list(self.root.rglob('*.iso*')))
    def test_paused_transfer_releases_queue_for_next_download(self):
        received=[]
        responses=[Response(b'abcdef',first=lambda:store.control('a','pause')),Response(b'second'),Response(b'def',206,{'Content-Range':'bytes 3-5/6'})]
        def importer(data):
            received.append(Path(data['path']).read_bytes());return {'id':'c'*32}
        with patch.object(store,'open_url',side_effect=responses),patch.object(store.shutil,'disk_usage',return_value=SimpleNamespace(free=1<<40)):
            first=threading.Thread(target=run_download,args=('a','https://example.com/a.iso','.iso',None,self.root,importer))
            first.start();self.wait(lambda:store.JOBS['a']['status']=='paused' and store.ACTIVE is None)
            with store.TURN:
                store.JOBS['b']={'id':'b','title':'Second','status':'queued','bytes':0}
                store.CONTROLS['b']={'paused':False,'cancelled':False}
            second=threading.Thread(target=run_download,args=('b','https://example.com/b.iso','.iso',None,self.root,importer))
            second.start();second.join(3);self.assertFalse(second.is_alive())
            self.assertEqual(received,[b'second'])
            store.control('a','resume');first.join(3);self.assertFalse(first.is_alive())
        self.assertEqual(received,[b'second',b'abcdef'])
    def test_resume_without_entity_validator_restarts_safely(self):
        first=Response(b'abcdef',headers={'ETag':''},first=lambda:store.control('a','pause'))
        received=[]
        with patch.object(store,'open_url',side_effect=[first,Response(b'changed')]) as opener,patch.object(store.shutil,'disk_usage',return_value=SimpleNamespace(free=1<<40)):
            worker=threading.Thread(target=run_download,args=('a','https://example.com/a.iso','.iso',None,self.root,lambda data:received.append(Path(data['path']).read_bytes()) or {'id':'b'*32}))
            worker.start();self.wait(lambda:store.JOBS['a']['status']=='paused' and store.ACTIVE is None)
            store.control('a','resume');worker.join(3);self.assertFalse(worker.is_alive())
        self.assertEqual(received,[b'changed'])
        # Resume without a validator restarts from byte 0 (no Range header).
        self.assertNotIn('Range', opener.call_args.args[1] if len(opener.call_args.args) > 1 else {})
    def test_connection_uses_validated_address_instead_of_reresolving_host(self):
        answers=[(2,1,6,'',('93.184.216.34',443))]
        with patch.object(store.socket,'getaddrinfo',return_value=answers),patch.object(store.socket,'create_connection') as connect:
            store.connect_public(('example.com',443),10)
            connect.assert_called_once_with(('93.184.216.34',443),10,None)
        with patch.object(store.socket,'getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',443))]),patch.object(store.socket,'create_connection') as connect:
            with self.assertRaises(ValueError):store.connect_public(('example.com',443))
            connect.assert_not_called()
    def test_malformed_control_is_a_useful_error(self):
        with self.assertRaises(ValueError):store.control([], 'cancel')
    def test_terminal_errors_auto_expire_and_install_cannot_be_cancelled(self):
        store.JOBS['a'].update(status='failed',finished_at=time.monotonic()-16)
        self.assertEqual(store.jobs(),[])
        store.JOBS['b']={'id':'b','status':'importing'}
        with self.assertRaises(ValueError):store.control('b','cancel')

if __name__=='__main__':unittest.main(verbosity=2)
