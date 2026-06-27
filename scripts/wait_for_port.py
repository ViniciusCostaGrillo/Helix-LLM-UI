import socket
import time
import sys

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
print(f"[Helix] Aguardando a porta {port} ficar ativa...")
for i in range(60):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect(('127.0.0.1', port))
            print(f"[Helix] Porta {port} está ativa!")
            sys.exit(0)
    except (ConnectionRefusedError, socket.timeout):
        # Print a small progress indicator every 5 seconds
        if i % 5 == 0 and i > 0:
            print(f"[Helix] Ainda aguardando a porta {port} ({i}s)...")
        time.sleep(1)

print(f"[Helix] Erro: Tempo limite esgotado aguardando a porta {port}.")
sys.exit(1)
