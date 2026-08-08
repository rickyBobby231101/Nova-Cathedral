#!/usr/bin/env python3
import sys,socket,os
SOCKET_PATH="/tmp/nova.sock"
BANNER="\n╔══════════════════════════════════════════════════════╗\n║          🔮  N O V A   C A T H E D R A L  🔮         ║\n║              Connected to background daemon           ║\n╚══════════════════════════════════════════════════════╝\n"
def send(message):
    if not os.path.exists(SOCKET_PATH):
        return "❌ Nova daemon is not running. Start with: sudo systemctl start nova"
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
            s.connect(SOCKET_PATH)
            s.sendall((message+"\n").encode("utf-8"))
            response=b""
            while True:
                chunk=s.recv(4096)
                if not chunk:break
                response+=chunk
                if response.endswith(b"\n"):break
            return response.decode("utf-8").strip()
    except Exception as e:return f"❌ Connection error: {e}"
def repl():
    print(BANNER)
    while True:
        try:user_input=input("you › ").strip()
        except(EOFError,KeyboardInterrupt):print("\n🌙 Farewell.");break
        if not user_input:continue
        if user_input.lower() in("quit","exit","q"):print("🌙 Farewell.");break
        print(f"\nnova › {send(user_input)}\n")
if __name__=="__main__":
    if len(sys.argv)>1:print(send(" ".join(sys.argv[1:])))
    else:repl()
