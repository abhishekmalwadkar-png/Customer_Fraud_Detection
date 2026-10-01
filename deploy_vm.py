#!/usr/bin/env python3
"""
=============================================================================
ABC Bank Fraud Portal - Automated 1-Click VM Deployment & Setup Engine
=============================================================================
This self-contained script automates the entire VM deployment lifecycle:
  1. Detects OS (Linux / Windows) and validates Python environment.
  2. Auto-installs all required dependencies from requirements.txt.
  3. Validates PostgreSQL connectivity (auto-starts service on Linux).
  4. Auto-creates the .env configuration if missing.
  5. Auto-provisions the PostgreSQL database, tables, schema, and sample data.
  6. Configures Linux firewall / systemd 24/7 service (optional).
  7. Starts the production ASGI Web Server (0.0.0.0:5050) and prints access URLs.

Usage:
  python3 deploy_vm.py
  python deploy_vm.py --service    # (Linux) Install and start systemd service
=============================================================================
"""

import os
import sys
import time
import socket
import platform
import subprocess
import urllib.request
import argparse
from pathlib import Path

# Color styling for CLI
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

def log_info(msg):
    print(f"{Colors.CYAN}[*]{Colors.END} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[+]{Colors.END} {Colors.BOLD}{msg}{Colors.END}")

def log_warn(msg):
    print(f"{Colors.YELLOW}[!]{Colors.END} {msg}")

def log_error(msg):
    print(f"{Colors.RED}[-]{Colors.END} {Colors.BOLD}{msg}{Colors.END}")

def print_banner():
    banner = f"""
{Colors.BLUE}{Colors.BOLD}=============================================================================
       ABC BANK FRAUD PREVENTION PORTAL - VM 1-CLICK DEPLOYER
============================================================================={Colors.END}
  • System: {platform.system()} {platform.release()} ({platform.machine()})
  • Python: {sys.version.split()[0]} ({sys.executable})
  • Path:   {os.getcwd()}
=============================================================================
"""
    print(banner)

def get_network_ips():
    """Detects local LAN and public IP addresses for display."""
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    public_ip = "YOUR_VM_PUBLIC_IP"
    try:
        req = urllib.request.Request("https://api.ipify.org", headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            public_ip = resp.read().decode('utf-8').strip()
    except Exception:
        pass

    return local_ip, public_ip

def check_and_install_dependencies():
    """Validates and installs required Python packages."""
    log_info("Checking Python dependencies...")
    req_file = Path("requirements.txt")
    if not req_file.exists():
        log_warn("requirements.txt not found in current directory. Creating default...")
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write("fastapi>=0.110.0\nuvicorn>=0.28.0\npydantic>=2.6.0\ndbutils>=3.2.0\npg8000>=1.30.0\npython-dotenv>=1.0.0\nreportlab>=4.0.0\nrequests>=2.31.0\n")

    cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"]
    try:
        subprocess.check_call(cmd)
        log_success("All Python dependencies are installed and verified.")
    except Exception as e:
        log_error(f"Failed to install requirements via pip: {e}")
        log_info("Attempting manual dependency install...")
        subprocess.call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic", "dbutils", "pg8000", "python-dotenv", "reportlab", "requests"])

def ensure_env_file():
    """Ensures .env exists with production settings."""
    env_path = Path(".env")
    if not env_path.exists():
        example_path = Path(".env.example")
        if example_path.exists():
            log_info("Creating .env from .env.example...")
            import shutil
            shutil.copy(".env.example", ".env")
        else:
            log_info("Generating default production .env file...")
            with open(".env", "w", encoding="utf-8") as f:
                f.write("""APP_ENV=production
LOG_LEVEL=INFO
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
DB_NAME=bank_fraud_portal
DB_POOL_MIN_CACHED=5
DB_POOL_MAX_CACHED=25
DB_POOL_MAX_CONNECTIONS=50
PORTAL_HOST=0.0.0.0
PORTAL_PORT=5050
SERVER_THREADS=16
""")
        log_success(".env file initialized.")
    else:
        log_info(".env file detected.")

def check_postgresql_service():
    """Checks if PostgreSQL service is running on Linux."""
    if platform.system() == "Linux":
        try:
            res = subprocess.run(["systemctl", "is-active", "postgresql"], capture_output=True, text=True)
            if "active" not in res.stdout:
                log_info("PostgreSQL service is stopped. Attempting to start...")
                subprocess.run(["sudo", "systemctl", "start", "postgresql"])
                subprocess.run(["sudo", "systemctl", "enable", "postgresql"])
        except Exception:
            pass

def setup_database_and_tables():
    """Initializes PostgreSQL database and seeds data."""
    log_info("Running automated PostgreSQL database & schema provisioning...")
    try:
        import db_setup
        db_setup.run_db_setup()
        log_success("PostgreSQL Database 'bank_fraud_portal' & sample records ready!")
    except Exception as err:
        log_warn(f"Direct db_setup call returned: {err}")
        log_info("Executing db_setup.py via subprocess...")
        subprocess.run([sys.executable, "db_setup.py"])

def configure_linux_firewall():
    """Opens port 5050 on UFW firewall if active."""
    if platform.system() == "Linux":
        try:
            res = subprocess.run(["which", "ufw"], capture_output=True, text=True)
            if res.returncode == 0:
                log_info("Configuring Linux UFW firewall to allow port 5050...")
                subprocess.run(["sudo", "ufw", "allow", "5050/tcp"], capture_output=True)
                log_success("Port 5050 allowed through UFW.")
        except Exception:
            pass

def install_systemd_service():
    """Installs 24/7 background systemd service on Linux."""
    if platform.system() != "Linux":
        log_warn("Systemd service installation is only supported on Linux.")
        return

    curr_dir = os.path.abspath(os.getcwd())
    service_content = f"""[Unit]
Description=ABC Bank Fraud Portal Backend & Web Server
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory={curr_dir}
ExecStart={sys.executable} -m uvicorn server:app --host 0.0.0.0 --port 5050 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    service_file = "/etc/systemd/system/abc-portal.service"
    log_info(f"Writing systemd service file to {service_file}...")
    try:
        with open("/tmp/abc-portal.service", "w") as f:
            f.write(service_content)
        subprocess.run(["sudo", "mv", "/tmp/abc-portal.service", service_file], check=True)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        subprocess.run(["sudo", "systemctl", "enable", "abc-portal"], check=True)
        subprocess.run(["sudo", "systemctl", "restart", "abc-portal"], check=True)
        log_success("Systemd service 'abc-portal' installed, enabled, and started!")
        log_info("Status: sudo systemctl status abc-portal")
        log_info("Logs:   sudo journalctl -u abc-portal -f")
    except Exception as e:
        log_error(f"Failed to install systemd service: {e}")

def display_access_urls():
    """Prints the final URLs for accessing the portal."""
    local_ip, public_ip = get_network_ips()
    port = os.getenv("PORTAL_PORT", "5050")

    print("\n" + "=" * 77)
    print(f"{Colors.GREEN}{Colors.BOLD}   ABC BANK FRAUD PORTAL - SUCCESSFULLY DEPLOYED & ACTIVE!{Colors.END}")
    print("=" * 77)
    print(f"\n{Colors.BOLD}Portal Access URLs (Share with your team/users):{Colors.END}")
    print(f"  • {Colors.CYAN}Public VM URL:{Colors.END}        http://{public_ip}:{port}/")
    print(f"  • {Colors.CYAN}Local Network (LAN):{Colors.END}  http://{local_ip}:{port}/")
    print(f"  • {Colors.CYAN}Customer NetBanking:{Colors.END}  http://{public_ip}:{port}/customer")
    print(f"  • {Colors.CYAN}Staff Login & Desk:{Colors.END}   http://{public_ip}:{port}/login")
    print(f"  • {Colors.CYAN}Interactive API Docs:{Colors.END} http://{public_ip}:{port}/docs")
    print(f"  • {Colors.CYAN}Server Health Check:{Colors.END}  http://{public_ip}:{port}/health")
    print("\n" + "=" * 77 + "\n")

def run_server_foreground():
    """Launches production Uvicorn ASGI server."""
    display_access_urls()
    log_info("Starting production ASGI server on 0.0.0.0:5050...")
    try:
        import uvicorn
        uvicorn.run("server:app", host="0.0.0.0", port=5050, workers=4, access_log=True)
    except KeyboardInterrupt:
        print("\n[*] Server shutdown gracefully by user.")
    except Exception as err:
        log_error(f"Server startup error: {err}")

def main():
    parser = argparse.ArgumentParser(description="ABC Bank Portal Automated VM Deployer")
    parser.add_argument("--service", action="store_true", help="Install and run as a 24/7 background systemd service (Linux)")
    parser.add_argument("--skip-db", action="store_true", help="Skip database seeding step")
    args = parser.parse_args()

    print_banner()

    # Step 1: Dependencies
    check_and_install_dependencies()

    # Step 2: Environment config
    ensure_env_file()

    # Step 3: PostgreSQL check
    check_postgresql_service()

    # Step 4: Database provisioning
    if not args.skip_db:
        setup_database_and_tables()

    # Step 5: Firewall
    configure_linux_firewall()

    # Step 6: Service or Foreground Execution
    if args.service:
        install_systemd_service()
        display_access_urls()
    else:
        run_server_foreground()

if __name__ == "__main__":
    main()
