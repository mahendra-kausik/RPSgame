import socket

print("[!] Finding an available server....")
def get_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))
    ip = sock.getsockname()
    sock.close()
    return ip

def detect_server():
    ip = get_ip()
    base_ip = ip[0].split('.')[0:3]
    server_ip = ""
    
    print(f"[!] Scanning network range {'.'.join(base_ip)}.1 to {'.'.join(base_ip)}.254")

    for i in range(1, 255):  # scan wider range!
        test_ip = ".".join(base_ip) + f".{i}"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)  # more reasonable timeout
            sock.connect((test_ip, 5555))

            print(f"[+] Server found at {test_ip}")
            sock.send("PING".encode())  # handshake ping
            server_ip = test_ip
            sock.close()
            break  # found server, stop scanning!

        except Exception as e:
            # Uncomment below if you want to see failed IPs:
            # print(f"[-] No response from {test_ip}")
            continue

    if server_ip == "":
        print("[!] No server found, rescanning...")
        return detect_server()  # recursive retry (optional, but careful!)
    
    else:
        return server_ip
