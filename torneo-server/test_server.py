import json, os, tempfile, threading, unittest, urllib.error, urllib.request
import server

class TournamentTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();server.DB=os.path.join(self.tmp.name,'test.db');server.ADMIN='test-password-long';server.SESSIONS.clear();server.init()
        self.http=server.HTTPServer(('127.0.0.1',0),server.Handler)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start();self.base='http://127.0.0.1:'+str(self.http.server_port)+'/api/'
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,path,data=None,token=None):
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+token} if token else {})})
        try:
            with urllib.request.urlopen(req) as r:return r.status,json.load(r)
        except urllib.error.HTTPError as e:return e.code,json.load(e)
    def setup_tournament(self):
        _,r=self.request('login',{'admin':True,'code':server.ADMIN});self.admin=r['token']
        status,r=self.request('setup',{'names':'Uno\nDue\nTre\nQuattro','groups':2,'courts':1},self.admin);self.assertEqual(status,200)
        self.tokens={}
        for t in r['codes']:
            _,login=self.request('login',{'code':t['code']});self.tokens[t['name']]=login['token']
        _,state=self.request('state');self.ids={t['id']:self.tokens[t['name']] for t in state['teams']}
        return state
    def start_match(self):
        self.setup_tournament()
        for token in self.tokens.values():self.request('availability',{'available':True},token)
        _,state=self.request('state');m=next(m for m in state['matches'] if m['status']=='waiting')
        self.request('ready',{'match':m['id'],'ready':True},self.ids[m['a']]);self.request('ready',{'match':m['id'],'ready':True},self.ids[m['b']]);return m
    def test_full_match_correction_and_authorization(self):
        m=self.start_match();outsider=next(t for i,t in self.ids.items() if i not in (m['a'],m['b']))
        self.assertEqual(self.request('result',{'match':m['id'],'a':50,'b':20},outsider)[0],403)
        self.assertEqual(self.request('result',{'match':m['id'],'a':50,'b':50},self.ids[m['a']])[0],400)
        status,state=self.request('result',{'match':m['id'],'a':50,'b':20},self.ids[m['a']]);self.assertEqual(status,200)
        second=next(x for x in state['matches'] if x['a']==m['a'] and x['b']==m['b'] and x['leg']==2);self.assertEqual(second['status'],'playing');self.assertEqual(second['court'],m['court'])
        self.assertEqual(self.request('result',{'match':m['id'],'a':50,'b':20},self.ids[m['b']])[0],400)
        _,state=self.request('result',{'match':second['id'],'a':10,'b':50},self.ids[m['b']])
        t=next(t for t in state['teams'] if t['id']==m['a']);self.assertEqual((t['played'],t['wins'],t['points']),(2,1,60))
        _,state=self.request('result',{'match':m['id'],'a':25,'b':50},self.admin)
        t=next(t for t in state['teams'] if t['id']==m['a']);self.assertEqual((t['played'],t['wins'],t['points']),(2,0,35))
        self.assertFalse(any(x['status'] in ('playing','waiting') and x['court']==m['court'] for x in state['matches']))
    def test_timeout_and_pause(self):
        self.setup_tournament()
        for token in self.tokens.values():self.request('availability',{'available':True},token)
        _,state=self.request('state');m=next(m for m in state['matches'] if m['status']=='waiting')
        with server.connect() as c:c.execute('UPDATE matches SET deadline=0 WHERE id=?',(m['id'],))
        _,state=self.request('state');self.assertEqual(next(x for x in state['matches'] if x['id']==m['id'])['status'],'pending')
        self.assertTrue(all(not t['available'] for t in state['teams'] if t['id'] in (m['a'],m['b'])))
        self.request('control',{'action':'pause'},self.admin)
        for i in (m['a'],m['b']):self.request('availability',{'available':True},self.ids[i])
        _,state=self.request('state');self.assertFalse(any(x['status']=='waiting' and x['id']==m['id'] for x in state['matches']))
        _,state=self.request('control',{'action':'resume'},self.admin);self.assertEqual(next(x for x in state['matches'] if x['id']==m['id'])['status'],'waiting')
    def test_restart_preserves_data(self):
        self.setup_tournament();server.init();_,state=self.request('state');self.assertEqual(len(state['teams']),4);self.assertEqual(len(state['matches']),4)

if __name__=='__main__':unittest.main()
