import time
import logging
from backend.knowledge.watchdog import KnowledgeWatchdog

logging.basicConfig(level=logging.INFO)
print("Iniciando Watchdog do Helix...")
w = KnowledgeWatchdog()
w.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Watchdog finalizado.")
    w.stop()
