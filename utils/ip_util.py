import socket
import logging
import time

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

def get_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()
        sock.close()
        return ip
    except Exception as e:
        logging.error(f"Error fetching IP: {e}")
        return None

def detect_servers(max_retries=3, delay=1):
    ip = get_ip()
    if not ip:
        return []
    
    base = ip[0].split('.')[:3]
    servers = []
    for attempt in range(max_retries):
        logging.info(f"Scanning network range {'.'.join(base)}.1 to {'.'.join(base)}.50 (Attempt {attempt+1}/{max_retries})")
        for i in range(1, 256):
            test_ip = ".".join(base) + f".{i}"
            try:
                # Check DATA channel on port 5555
                sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock1.settimeout(0.05)
                sock1.connect((test_ip, 5555))
                sock1.send("PING".encode())
                sock1.close()
                # Check CTRL channel on port 5556
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2.settimeout(0.05)
                sock2.connect((test_ip, 5556))
                sock2.send("PING".encode())
                sock2.close()
                if test_ip not in servers:
                    servers.append(test_ip)
            except Exception:
                continue
        if servers:
            logging.info(f"Found servers: {servers}")
            return servers
        logging.warning("No servers found, retrying...")
        time.sleep(delay)
    logging.error("No servers found after max retries.")
    return servers
