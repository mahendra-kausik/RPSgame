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

def detect_server(max_retries=5, delay=2):
    ip = get_ip()
    if not ip:
        return None

    base_ip = ip[0].split('.')[0:3]
    retry = 0

    while retry < max_retries:
        logging.info(f"Scanning network range {'.'.join(base_ip)}.1 to {'.'.join(base_ip)}.254 (Attempt {retry+1}/{max_retries})")
        for i in range(1, 255):
            test_ip = ".".join(base_ip) + f".{i}"

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                sock.connect((test_ip, 5555))
                sock.send("PING".encode())

                logging.info(f"Server found at {test_ip}")
                sock.close()
                return test_ip

            except socket.timeout:
                continue
            except Exception as e:
                continue
            finally:
                sock.close()

        retry += 1
        logging.warning("No server found, retrying...")
        time.sleep(delay)

    logging.error("Server not found after max retries.")
    return None
