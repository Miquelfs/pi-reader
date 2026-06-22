import socket

# PiSugar2 server listens on a Unix socket or TCP port 8423.
# The pisugar-server daemon must be running (installed via the PiSugar2 setup script).
_SOCKET_PATH = '/tmp/pisugar-server.sock'
_TCP_PORT = 8423


def _query_pisugar(command):
    """Send a command to pisugar-server and return the response string."""
    # Try Unix socket first, fall back to TCP
    for use_tcp in (False, True):
        try:
            if use_tcp:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                sock.connect(('127.0.0.1', _TCP_PORT))
            else:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                sock.connect(_SOCKET_PATH)
            sock.sendall((command + '\n').encode())
            response = sock.recv(256).decode().strip()
            sock.close()
            return response
        except Exception:
            continue
    return None


def read_battery_percent():
    """Return battery level 0-100, or None if PiSugar2 server is unreachable."""
    resp = _query_pisugar('get battery')
    if resp is None:
        return None
    # Response format: "battery: 87.3"
    try:
        value = resp.split(':', 1)[-1].strip()
        return int(float(value))
    except (ValueError, IndexError):
        return None
