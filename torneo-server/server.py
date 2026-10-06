"""API torneo: Python standard library, SQLite, single-process transactional writes."""
import hashlib, hmac, json, os, secrets, sqlite3, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DB = os.environ.get('TORNEO_DB', 'torneo.db')
ADMIN = os.environ.get('TORNEO_ADMIN_PASSWORD', '')
ORIGIN = os.environ.get('TORNEO_ORIGIN', 'http://localhost:8000')
SESSIONS = {}

def digest(code):
    return hashlib.sha256(code.encode()).hexdigest()

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS teams(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, group_id INTEGER NOT NULL, code TEXT NOT NULL, available INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS courts(id INTEGER PRIMARY KEY, group_id INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS matches(id INTEGER PRIMARY KEY, a INTEGER, b INTEGER, leg INTEGER, status TEXT DEFAULT 'pending', court INTEGER, deadline REAL, ready_a INTEGER DEFAULT 0, ready_b INTEGER DEFAULT 0, p_a INTEGER, p_b INTEGER, UNIQUE(a,b,leg));
        CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1), paused INTEGER DEFAULT 0, closed INTEGER DEFAULT 0);
        INSERT OR IGNORE INTO settings(id) VALUES(1);
        ''')

def expire(c):
    for m in c.execute("SELECT * FROM matches WHERE status='waiting' AND deadline<?", (time.time(),)).fetchall():
        c.execute('UPDATE teams SET available=0 WHERE id IN (?,?)', (m['a'],m['b']))
        c.execute("UPDATE matches SET status='pending',court=NULL,ready_a=0,ready_b=0 WHERE id=?", (m['id'],))

def schedule(c):
    s=c.execute('SELECT * FROM settings').fetchone()
    if s['paused'] or s['closed']: return
    for court in c.execute('SELECT * FROM courts ORDER BY id').fetchall():
        if c.execute("SELECT 1 FROM matches WHERE court=? AND status IN ('waiting','playing')",(court['id'],)).fetchone(): continue
        candidates=c.execute('''SELECT m.* FROM matches m JOIN teams a ON a.id=m.a JOIN teams b ON b.id=m.b
          WHERE m.status='pending' AND m.leg=1 AND a.available=1 AND b.available=1 AND a.group_id=?
          AND NOT EXISTS(SELECT 1 FROM matches x WHERE x.status IN ('waiting','playing') AND (x.a IN(m.a,m.b) OR x.b IN(m.a,m.b)))''',(court['group_id'],)).fetchall()
        def stats(team):
            r=c.execute("SELECT COUNT(*),COALESCE(SUM(CASE WHEN (a=? AND p_a=50) OR (b=? AND p_b=50) THEN 1 ELSE 0 END),0) FROM matches WHERE status='done' AND (a=? OR b=?)",(team,team,team,team)).fetchone()
            return tuple(r)
        def rank(m):
            x,y=stats(m['a']),stats(m['b'])
            return (x[0]+y[0],2*abs(x[0]-y[0])+abs(x[1]-y[1]),m['id'])
        if candidates:
            m=min(candidates,key=rank)
            c.execute("UPDATE matches SET status='waiting',court=?,deadline=?,ready_a=0,ready_b=0 WHERE id=?",(court['id'],time.time()+180,m['id']))

def snapshot(c, team=None):
    teams=[]
    for t in c.execute('SELECT id,name,group_id,available FROM teams'):
        played=wins=points=0
        for m in c.execute("SELECT * FROM matches WHERE status='done' AND (a=? OR b=?)",(t['id'],t['id'])):
            p=m['p_a'] if m['a']==t['id'] else m['p_b']; played+=1; wins+=p==50; points+=p
        teams.append(dict(t,played=played,wins=wins,points=points))
    teams.sort(key=lambda t:(t['group_id'],-t['wins'],-t['points'],t['name']))
    matches=[dict(m) for m in c.execute('SELECT * FROM matches')]
    return dict(teams=teams,matches=matches,courts=[dict(r) for r in c.execute('SELECT * FROM courts')],settings=dict(c.execute('SELECT * FROM settings').fetchone()),team=team)

class Handler(BaseHTTPRequestHandler):
    def reply(self, data, status=200):
        raw=json.dumps(data).encode(); self.send_response(status)
        self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store')
        self.send_header('Access-Control-Allow-Origin',ORIGIN); self.send_header('Vary','Origin')
        self.end_headers(); self.wfile.write(raw)
    def do_OPTIONS(self):
        self.send_response(204); self.send_header('Access-Control-Allow-Origin',ORIGIN)
        self.send_header('Access-Control-Allow-Headers','Content-Type, Authorization'); self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS'); self.end_headers()
    def auth(self):
        token=self.headers.get('Authorization','').removeprefix('Bearer ')
        session=SESSIONS.get(token)
        return session[0] if session and session[1]>time.time() else None
    def do_GET(self):
        if self.path!='/api/state': return self.reply({'error':'Pagina non trovata'},404)
        with connect() as c:
            c.execute('BEGIN IMMEDIATE'); expire(c); schedule(c)
            self.reply(snapshot(c,self.auth()))
    def do_POST(self):
        try:
            size=int(self.headers.get('Content-Length',0))
            if size>16384: raise ValueError('Richiesta troppo grande')
            data=json.loads(self.rfile.read(size)); who=self.auth()
            with connect() as c:
                c.execute('BEGIN IMMEDIATE'); expire(c)
                if self.path=='/api/login':
                    code=str(data.get('code',''))
                    if data.get('admin'):
                        if not ADMIN or not hmac.compare_digest(code,ADMIN): raise ValueError('Password non valida')
                        who='admin'
                    else:
                        t=c.execute('SELECT id FROM teams WHERE code=?',(digest(code),)).fetchone()
                        if not t: raise ValueError('Codice squadra non valido')
                        who=t['id']
                    token=secrets.token_urlsafe(32); SESSIONS[token]=(who,time.time()+43200)
                    return self.reply(dict(token=token,team=who))
                if who is None: return self.reply({'error':'Accedi prima di continuare'},401)
                if self.path=='/api/setup':
                    if who!='admin': return self.reply({'error':'Accesso riservato'},403)
                    if c.execute('SELECT 1 FROM teams').fetchone(): raise ValueError('Torneo già configurato')
                    names=[n.strip() for n in data['names'].splitlines() if n.strip()]
                    groups=int(data['groups']); per=int(data['courts'])
                    if groups not in (2,4) or not 1<=per<=8 or len(names)<groups*2 or len(set(names))!=len(names): raise ValueError('Servono nomi diversi e almeno due squadre per girone')
                    secrets.SystemRandom().shuffle(names); codes=[]
                    for i,name in enumerate(names):
                        if len(name)>60: raise ValueError('Nome squadra troppo lungo')
                        code=secrets.token_urlsafe(9); g=i%groups+1
                        c.execute('INSERT INTO teams(name,group_id,code) VALUES(?,?,?)',(name,g,digest(code))); codes.append(dict(name=name,code=code,group=g))
                    for g in range(1,groups+1):
                        for _ in range(per): c.execute('INSERT INTO courts(group_id) VALUES(?)',(g,))
                        ids=[r[0] for r in c.execute('SELECT id FROM teams WHERE group_id=?',(g,))]
                        for i,a in enumerate(ids):
                            for b in ids[i+1:]:
                                for leg in (1,2): c.execute('INSERT INTO matches(a,b,leg) VALUES(?,?,?)',(a,b,leg))
                    return self.reply({'codes':codes})
                if self.path=='/api/control':
                    if who!='admin': return self.reply({'error':'Accesso riservato'},403)
                    action=data['action']
                    if action not in ('pause','resume','close'): raise ValueError('Azione non valida')
                    c.execute('UPDATE settings SET paused=?,closed=?',(action!='resume',action=='close'))
                elif self.path=='/api/availability':
                    if who=='admin': raise ValueError('Accedi con un codice squadra')
                    if c.execute("SELECT 1 FROM matches WHERE status IN ('waiting','playing') AND (a=? OR b=?)",(who,who)).fetchone(): raise ValueError('Hai già un incontro assegnato')
                    c.execute('UPDATE teams SET available=? WHERE id=?',(bool(data['available']),who))
                elif self.path in ('/api/ready','/api/result'):
                    m=c.execute('SELECT * FROM matches WHERE id=?',(int(data['match']),)).fetchone()
                    if not m or (who!='admin' and who not in (m['a'],m['b'])): return self.reply({'error':'Incontro non accessibile'},403)
                    if self.path=='/api/ready':
                        if m['status']!='waiting' or who=='admin': raise ValueError('Conferma non disponibile')
                        if not data['ready']:
                            c.execute('UPDATE teams SET available=0 WHERE id=?',(who,)); c.execute("UPDATE matches SET status='pending',court=NULL,ready_a=0,ready_b=0 WHERE id=?",(m['id'],))
                        else:
                            col='ready_a' if who==m['a'] else 'ready_b'; c.execute(f'UPDATE matches SET {col}=1 WHERE id=?',(m['id'],))
                            c.execute("UPDATE matches SET status='playing' WHERE id=? AND ready_a=1 AND ready_b=1",(m['id'],))
                    else:
                        correction=m['status']=='done' and who=='admin'
                        if m['status']!='playing' and not correction: raise ValueError('Risultato già registrato o set non iniziato')
                        a,b=data['a'],data['b']
                        if type(a)!=int or type(b)!=int or not 0<=a<=50 or not 0<=b<=50 or (a==50)==(b==50): raise ValueError('Una sola squadra deve avere 50 punti; l’altra da 0 a 49')
                        c.execute("UPDATE matches SET status='done',p_a=?,p_b=? WHERE id=?",(a,b,m['id']))
                        if not correction and m['leg']==1:
                            c.execute("UPDATE matches SET status='playing',court=? WHERE a=? AND b=? AND leg=2 AND status='pending'",(m['court'],m['a'],m['b']))
                else: return self.reply({'error':'Operazione non trovata'},404)
                schedule(c); self.reply(snapshot(c,who))
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
            self.reply({'error':str(e)},400)
        except Exception:
            self.reply({'error':'Errore del server'},500)

if __name__=='__main__':
    if len(ADMIN)<12: raise SystemExit('Imposta TORNEO_ADMIN_PASSWORD con almeno 12 caratteri')
    init(); HTTPServer(('0.0.0.0',int(os.environ.get('PORT','8080'))),Handler).serve_forever()
