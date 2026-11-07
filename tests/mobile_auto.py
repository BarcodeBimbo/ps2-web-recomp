"""Automatic certificates, random port, authenticated ready-game library and revocation."""
from pathlib import Path
import http.client,json,ssl,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import panel,mobile
class Automatic(unittest.TestCase):
 def test_auto_listener_uses_random_port_and_keeps_admin_private(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);games=root/'games';games.mkdir();identifier='a'*32
   folder=games/identifier;folder.mkdir();(folder/'library.json').write_text(json.dumps({'id':identifier,'title':'Fixture <safe>','status':'ready'}))
   web=root/'web';web.mkdir();(web/'mobile.html').write_bytes((Path(__file__).resolve().parents[1]/'web'/'mobile.html').read_bytes())
   with patch.object(panel,'ROOT',root),patch.object(panel,'GAMES',games),patch.object(mobile,'lan_address',return_value='127.0.0.1'):
    server,info=mobile.start_automatic()
    try:
     self.assertGreater(info['port'],0);self.assertNotEqual(info['port'],8621)
     trust=ssl.create_default_context(cafile=str(root/'tools/mobile/phone-ca.crt'))
     def get(path,cookie=None):
      c=http.client.HTTPSConnection('127.0.0.1',info['port'],context=trust,timeout=5)
      c.request('GET',path,headers={'Cookie':cookie} if cookie else {});r=c.getresponse();value=r.status,dict(r.getheaders()),r.read();c.close();return value
     self.assertEqual(get('/')[0],403)
     status,headers,_=get('/connect?key='+server.access_token);self.assertEqual(status,303);self.assertEqual(headers['Location'],'/')
     cookie=headers['Set-Cookie'].split(';')[0]
     status,_,body=get('/',cookie);self.assertEqual(status,200);self.assertIn(b'Fixture &lt;safe&gt;',body)
     self.assertIn(b'CyberArcade',body);self.assertIn(b'/play/',body);self.assertIn(b'?touch',body)
     self.assertIn(b'id="games"',body);self.assertNotIn(b'Phone access',body)
     for route in ['/api/games','/api/store/jobs','/tools/mobile/phone-ca.key']:
      self.assertEqual(get(route,cookie)[0],404)
     server.access_token='rotated';self.assertEqual(get('/',cookie)[0],403)
    finally:server.shutdown();server.server_close()
if __name__=='__main__':unittest.main(verbosity=2)
