"""Read-only mobile HTTPS authentication and range integration with a trusted test cert."""
from pathlib import Path
import http.client
import json
import ssl
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import panel
from mobile import MobilePlayer,MobileServer
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);cert=root/'cert.pem';key=root/'key.pem'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=127.0.0.1','-addext','subjectAltName=IP:127.0.0.1','-keyout',str(key),'-out',str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    original_root,original_games=panel.ROOT,panel.GAMES
    panel.ROOT=root;panel.GAMES=root/'games';game_id='a'*32
    game=panel.GAMES/game_id;game.mkdir(parents=True);(game/'disc.iso').write_bytes(b'abcdefgh')
    (game/'library.json').write_text(json.dumps({'id':game_id,'title':'Fixture','status':'ready'}))
    output=root/'build'/f'web-{game_id}';output.mkdir(parents=True);(output/'ps2web.html').write_text('ready');(output/'build.json').write_text(json.dumps({'id':'fixture','async_mode':'asyncify'}))
    (root/'web').mkdir()
    (root/'web'/'shell.html').write_bytes((ROOT/'web'/'shell.html').read_bytes())
    (root/'web'/'mobile.html').write_bytes((ROOT/'web'/'mobile.html').read_bytes())
    tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain(cert,key)
    client=ssl.create_default_context(cafile=str(cert))
    try:
        with MobileServer(('127.0.0.1',0),MobilePlayer) as server:
            server.tls=tls;server.scheme='https';server.game_id=game_id;server.access_token='test-session'
            server.allowed_hosts={f'127.0.0.1:{server.server_port}'}
            threading.Thread(target=server.serve_forever,daemon=True).start()
            def request(path,headers=None,method='GET'):
                c=http.client.HTTPSConnection('127.0.0.1',server.server_port,context=client,timeout=5)
                c.request(method,path,headers=headers or {});r=c.getresponse();result=r.status,dict(r.getheaders()),r.read();c.close();return result
            assert request(f'/play/{game_id}/disc.iso')[0]==403
            status,headers,_=request('/connect?key=test-session');assert status==303
            assert headers['Location']==f'/play/{game_id}/?touch'
            cookie={'Cookie':headers['Set-Cookie'].split(';')[0]}
            status,headers,body=request(f'/play/{game_id}/?touch',cookie);assert status==200 and b'Touch controls' in body
            assert b'id="touch"' in body and b'id="open-pc-controls"' in body
            assert b'CyberArcade' in body
            assert b'__PS2_ASYNC_MODE__' not in body and b"const browserAsyncMode='asyncify'" in body
            assert headers['Cross-Origin-Opener-Policy']=='same-origin'
            assert headers['Cross-Origin-Embedder-Policy']=='require-corp'
            # Library mode: themed ready-game grid with touch play links.
            server.game_id=None
            status,_,body=request('/',cookie);assert status==200
            assert b'Fixture' in body and b'/?touch' in body and b'id="games"' in body
            assert b'Phone access' not in body
            server.game_id=game_id
            # Legacy builds omit async_mode; infer JSPI from Suspending glue.
            (output/'build.json').write_text(json.dumps({'id':'legacy'}))
            (output/'ps2web.js').write_text('var Module={}; WebAssembly.Suspending = function(){};')
            assert panel.resolve_async_mode(game_id)=='jspi'
            status,_,body=request(f'/play/{game_id}/',cookie)
            assert status==200 and b"const browserAsyncMode='jspi'" in body
            (output/'ps2web.js').write_text('var Module={}; var Asyncify={};')
            (output/'build.json').unlink()
            assert panel.resolve_async_mode(game_id)=='asyncify'
            status,_,body=request(f'/play/{game_id}/disc.iso',{**cookie,'Range':'bytes=2-4'});assert status==206 and body==b'cde'
            assert request('/api/games',cookie)[0]==404
            assert request('/api/games',cookie,'POST')[0]==405
            assert request('/play/'+'b'*32+'/',cookie)[0]==404
            server.access_token='rotated';assert request(f'/play/{game_id}/',cookie)[0]==403
            server.shutdown()
    finally:panel.ROOT,panel.GAMES=original_root,original_games
print('PASS: HTTPS trust, authentication, secure cookie, live shell, async-mode inference, COOP/COEP, disc ranges, blocked admin/other games, token rotation')
