"""Normalized-disc dedupe, safe cleanup, queue removal and static repair checks."""
import json,os,sys,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import panel,store
from install_identity import claim_disc
from translation_repair import add_entry
import struct

class Flow(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  (self.root/'games').mkdir()
 def game(self,identifier,status='building'):
  folder=self.root/'games'/identifier;folder.mkdir()
  (folder/'disc.iso').write_bytes(b'normalized disc fixture')
  (folder/'library.json').write_text(json.dumps({'id':identifier,'title':'Fixture','status':status}))
  return folder
 def test_cross_container_disc_identity_and_concurrent_claims(self):
  ids=['a'*32,'b'*32];folders=[self.game(i) for i in ids];results={}
  def run(i):results[i]=claim_disc(self.root,ids[i],folders[i]/'disc.iso')
  threads=[threading.Thread(target=run,args=(i,)) for i in range(2)]
  for t in threads:t.start()
  for t in threads:t.join()
  self.assertEqual(sum(owner is None for digest,owner in results.values()),1)
  self.assertEqual(results[0][0],results[1][0])
 def test_existing_ready_disc_is_backfilled(self):
  first=self.game('a'*32,'ready');second=self.game('b'*32)
  self.assertEqual(claim_disc(self.root,'b'*32,second/'disc.iso')[1],'a'*32)
 def test_failed_download_retry_reuses_the_same_game(self):
  identifier='a'*32;self.game(identifier,'failed');download=self.root/'downloads';download.mkdir();source=download/('b'*32+'.zip');source.write_bytes(b'fixture')
  with patch.object(panel,'ROOT',self.root),patch.object(panel,'GAMES',self.root/'games'),patch.object(panel,'enqueue') as enqueue:
   game=panel.retry_download_install({'game_id':identifier,'path':str(source),'title':'Fixture'},'known')
   self.assertEqual(game['id'],identifier);self.assertEqual(enqueue.call_args.args[1],source)
 def test_cleanup_never_deletes_originals(self):
  folder=self.root/'downloads';folder.mkdir();managed=folder/('a'*32+'.zip');managed.write_bytes(b'archive')
  original=self.root/'original.zip';original.write_bytes(b'keep')
  with patch.object(panel,'ROOT',self.root):panel.cleanup_download_source(managed);panel.cleanup_download_source(original)
  self.assertFalse(managed.exists());self.assertTrue(original.exists())
 def test_remove_build_queue_keeps_other_games_and_original_source(self):
  from collections import deque
  a,b='a'*32,'b'*32
  self.game(a,'queued');self.game(b,'queued')
  source=self.root/'original.zip';source.write_bytes(b'keep')
  queue=deque()
  queue.extend([(None,source,3600,8,None),(None,None,3600,8,None)])
  with patch.object(panel,'ROOT',self.root),patch.object(panel,'GAMES',self.root/'games'),patch.object(panel,'QUEUE',queue):
   # Read fixture metadata through the patched root.
   queue[0]=(panel.get_game(a),source,3600,8,None)
   queue[1]=(panel.get_game(b),None,3600,8,None)
   panel.game_action(a,'dequeue')
   self.assertEqual(panel.get_game(a)['status'],'cancelled')
   self.assertEqual(len(queue),1);self.assertEqual(queue[0][0]['id'],b)
   self.assertTrue(source.exists())
   with self.assertRaises(ValueError):panel.game_action(b,'cancel-active')
 def test_reexplore_reuses_installed_disc_and_runs_native_discovery(self):
  identifier='a'*32;folder=self.game(identifier,'ready')
  with patch.object(panel,'GAMES',self.root/'games'),patch.object(panel,'enqueue') as enqueue:
   panel.game_action(identifier,'reexplore')
   self.assertEqual(enqueue.call_args.args[1:],(folder/'disc.iso',3600,8))
   self.assertEqual(enqueue.call_args.args[0]['id'],identifier)
   self.assertTrue((folder/'disc.iso').is_file())
 def test_translation_repair_rejects_dynamic_and_unaligned_targets(self):
  elf=self.root/'core.elf';data=bytearray(0x200);data[:7]=b'\x7fELF\x01\x01\x01'
  struct.pack_into('<I',data,28,52);struct.pack_into('<HH',data,42,32,1)
  struct.pack_into('<8I',data,52,1,0x100,0x100000,0,0x20,0x100,5,4);elf.write_bytes(data)
  entries=self.root/'entries.txt';add_entry(elf,entries,0x100004);self.assertEqual(entries.read_text(),'100004\n')
  for address in [0x100001,0x100040,0x281360,0x6c7b50]:
   with self.assertRaises(ValueError):add_entry(elf,entries,address)
 def test_install_health_flags_missing_code_and_black_screen(self):
  from install_health import analyze_log, write_health, gate_ready
  bad=analyze_log('[gs] 2 primitives drawn\n[ee] stopped after 200 frames, 1 cycles: missing code at 0x01A5BEA4 (ra 0x1)\n')
  self.assertEqual(bad['status'],'fail')
  self.assertTrue(any(r.startswith('missing_code') for r in bad['reasons']))
  black=analyze_log('[gs] 0 primitives drawn\n[ee] WaitSema(45)\n[ee] stopped after 200 frames\n')
  self.assertEqual(black['status'],'fail')
  ok=analyze_log('[gs] 99686 primitives drawn\n[ee] stopped after 600 frames, 1 cycles: frame limit reached\n')
  self.assertEqual(ok['status'],'ok')
  folder=self.game('c'*32,'building')
  (folder/'explore.log').write_text('[gs] 2 primitives drawn\n[ee] stopped after 120 frames: missing code at 0x100000\n')
  report=write_health(folder)
  self.assertEqual(report['status'],'fail')
  self.assertTrue((folder/'health.json').is_file())
  with self.assertRaises(RuntimeError):gate_ready(report)
if __name__=='__main__':unittest.main(verbosity=2)
