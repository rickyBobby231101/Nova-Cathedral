#!/usr/bin/env python3
import os,json,time,signal,socket,sqlite3,logging,threading,configparser,urllib.request
from datetime import datetime
from pathlib import Path
HOME=Path.home()
CFG_DEFAULTS={"log":str(HOME/"Cathedral/logs/nova.log"),"db":str(HOME/".nova/memory.db"),"sock":"/tmp/nova_socket","ollama_url":"http://localhost:11434","model":"llama3"}
def load_cfg():
    d=HOME/".nova"; d.mkdir(exist_ok=True)
    p=d/"config.ini"; c=configparser.ConfigParser()
    c.read(p)
    if not c.has_section("nova"): c.add_section("nova")
    for k,v in CFG_DEFAULTS.items():
        if not c.has_option("nova",k): c.set("nova",k,v)
    with open(p,"w") as f: c.write(f)
    return c,p
CFG,CFG_PATH=load_cfg()
def cfg(k): return CFG.get("nova",k,fallback=CFG_DEFAULTS.get(k,""))
def mem_save(txt,cat="general"):
    with sqlite3.connect(HOME/".nova/memory.db") as c: c.execute("INSERT INTO m(cat,txt)VALUES(?,?)",(cat,txt))
def mem_count():
    try:
        with sqlite3.connect(HOME/".nova/memory.db") as c: return c.execute("SELECT COUNT(*) FROM m").fetchone()[0]
    except: return 0
def mem_search(q="",cat="",n=10):
    sql="SELECT id,ts,cat,txt FROM m WHERE 1=1"; p=[]
    if q: sql+=" AND txt LIKE ?"; p.append(f"%{q}%")
    if cat: sql+=" AND cat=?"; p.append(cat)
    with sqlite3.connect(HOME/".nova/memory.db") as c:
        return [{"id":r[0],"ts":r[1],"cat":r[2],"txt":r[3]} for r in c.execute(sql+f" ORDER BY ts DESC LIMIT {n}",p)]
def init_db():
    p=Path(cfg("db")); p.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(p) as c:
        c.execute("CREATE TABLE IF NOT EXISTS m(id INTEGER PRIMARY KEY,ts TEXT DEFAULT(datetime('now')),cat TEXT,txt TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS e(id INTEGER PRIMARY KEY,ts TEXT DEFAULT(datetime('now')),ev TEXT,data TEXT)")
init_db()
def ollama_up():
    try: urllib.request.urlopen(f"{cfg('ollama_url')}/api/tags",timeout=2); return True
    except: return False
def ollama_models():
    try: return [m["name"] for m in json.loads(urllib.request.urlopen(f"{cfg('ollama_url')}/api/tags",timeout=5).read()).get("models",[])]
    except Exception as e: return str(e)
def ollama_ask(prompt):
    if not ollama_up(): return {"error":"Ollama not running - start: ollama serve"}
    sys_msg=f"You are Nova, a persistent AI agent. Memories: {mem_count()}. Time: {datetime.now().isoformat()}"
    payload={"model":cfg("model"),"messages":[{"role":"system","content":sys_msg},{"role":"user","content":prompt}],"stream":False}
    try:
        t=time.time()
        req=urllib.request.Request(f"{cfg('ollama_url')}/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method="POST")
        txt=json.loads(urllib.request.urlopen(req,timeout=120).read()).get("message",{}).get("content","(empty)")
        mem_save(f"Q:{prompt[:200]}\nA:{txt[:400]}","ollama")
        return {"response":txt,"model":cfg("model"),"latency":round(time.time()-t,2)}
    except Exception as e: return {"error":str(e)}
def files_read(rp):
    try:
        p=(HOME/rp).resolve()
        if not str(p).startswith(str(HOME)): return {"error":"outside home"}
        return {"content":p.read_text(errors="replace")} if p.is_file() else {"error":"not a file"}
    except Exception as e: return {"error":str(e)}
def files_write(rp,txt,append=False):
    try:
        p=(HOME/rp).resolve()
        if not str(p).startswith(str(HOME)): return {"error":"outside home"}
        p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,"a" if append else "w") as f: f.write(txt)
        return {"ok":True,"path":str(p)}
    except Exception as e: return {"error":str(e)}
def files_ls(rp="."):
    try:
        p=(HOME/rp).resolve()
        return {"entries":[{"n":x.name,"t":"d" if x.is_dir() else "f"} for x in sorted(p.iterdir())]}
    except Exception as e: return {"error":str(e)}
RUNNING=False
T0=None
def handle_cmd(raw):
    global RUNNING
    try: d=json.loads(raw)
    except: d={"command":raw.strip()}
    c=d.get("command","").lower()
    if c=="status": return {"name":"Nova","uptime":int(time.time()-T0) if T0 else 0,"memories":mem_count(),"ollama":ollama_up(),"model":cfg("model"),"socket":cfg("sock")}
    elif c=="ask": p=d.get("prompt",d.get("content","")); return ollama_ask(p) if p else {"error":"missing prompt"}
    elif c=="models": return {"models":ollama_models()}
    elif c=="set_model":
        m=d.get("model",""); CFG.set("nova","model",m)
        with open(CFG_PATH,"w") as f: CFG.write(f)
        return {"ok":True,"model":m}
    elif c=="remember": mem_save(d.get("content",""),d.get("cat","general")); return {"ok":True}
    elif c=="recall": return {"memories":mem_search(d.get("query",""),d.get("cat",""),int(d.get("n",10)))}
    elif c=="read": return files_read(d.get("path",""))
    elif c=="write": return files_write(d.get("path",""),d.get("content",""),d.get("append",False))
    elif c=="ls": return files_ls(d.get("path","."))
    elif c=="readask":
        path=d.get('path',''); prompt=d.get('prompt',d.get('content',''))
        if not path or not prompt: return {'error':'need path and prompt'}
        fr=files_read(path)
        if 'error' in fr: return fr
        full='FILE: '+path+'\n\nCONTENT:\n'+fr['content'][:6000]+'\n\nQUESTION: '+prompt
        return ollama_ask(full)
    elif c=="help": return {"commands":["status","ask","models","set_model","remember","recall","read","write","ls","shutdown"]}
    elif c=="shutdown": RUNNING=False; return {"ok":True}
    else: return {"error":f"unknown: {c}"}
def handle_client(conn):
    try:
        data=b""; conn.settimeout(5)
        while True:
            chunk=conn.recv(4096)
            if not chunk: break
            data+=chunk
            if data.endswith(b"\n") or len(chunk)<4096: break
        if data: conn.sendall((json.dumps(handle_cmd(data.decode().strip()),default=str)+"\n").encode())
    except Exception as e:
        try: conn.sendall((json.dumps({"error":str(e)})+"\n").encode())
        except: pass
    finally: conn.close()
def run():
    global RUNNING,T0; RUNNING=True; T0=time.time()
    Path(cfg("log")).parent.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(message)s",handlers=[logging.FileHandler(cfg("log")),logging.StreamHandler()])
    log=logging.getLogger("nova")
    signal.signal(signal.SIGTERM,lambda s,f:globals().update(RUNNING=False))
    signal.signal(signal.SIGINT,lambda s,f:globals().update(RUNNING=False))
    sock=cfg("sock")
    if os.path.exists(sock): os.unlink(sock)
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    s.bind(sock); s.listen(10); os.chmod(sock,0o666); s.settimeout(1.0)
    log.info(f"Nova online | model:{cfg('model')} | ollama:{'yes' if ollama_up() else 'NOT RUNNING'} | memories:{mem_count()}")
    while RUNNING:
        try: conn,_=s.accept(); threading.Thread(target=handle_client,args=(conn,),daemon=True).start()
        except socket.timeout: continue
        except Exception as e:
            if RUNNING: log.error(str(e))
    s.close()
    if os.path.exists(sock): os.unlink(sock)
    log.info("Nova offline.")
def send(payload,sock="/tmp/nova_socket"):
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
            s.connect(sock); s.sendall((json.dumps(payload)+"\n").encode()); s.settimeout(120)
            chunks=[]
            while True:
                d=s.recv(4096)
                if not d: break
                chunks.append(d)
                if d.endswith(b"\n"): break
            return json.loads(b"".join(chunks).decode())
    except FileNotFoundError: return {"error":"Nova not running - start: python3 ~/WorkSpace/nova_agent.py"}
    except Exception as e: return {"error":str(e)}
if __name__=="__main__":
    import argparse; p=argparse.ArgumentParser(); p.add_argument("--status",action="store_true"); p.add_argument("--cli",action="store_true"); p.add_argument("--send",metavar="JSON"); a=p.parse_args()
    if a.status: print(json.dumps(send({"command":"status"}),indent=2))
    elif a.send:
        try: pl=json.loads(a.send)
        except: pl={"command":a.send}
        print(json.dumps(send(pl),indent=2))
    elif a.cli:
        print("Nova CLI | help | exit")
        while True:
            try: line=input("nova> ").strip()
            except (EOFError,KeyboardInterrupt): print(); break
            if not line or line=="exit": break
            parts=line.split(None,1); c=parts[0]; rest=parts[1] if len(parts)>1 else ""
            if c=="ask" and rest: pl={"command":"ask","prompt":rest}
            elif c=="remember" and rest: pl={"command":"remember","content":rest}
            elif c=="recall": pl={"command":"recall","query":rest}
            elif c=="read" and rest: pl={"command":"read","path":rest}
            elif c=="ls": pl={"command":"ls","path":rest or "WorkSpace"}
            elif c=="model" and rest: pl={"command":"set_model","model":rest}
            else: pl={"command":c}
            print(json.dumps(send(pl),indent=2,default=str))
    else: run()
