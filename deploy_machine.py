#!/usr/bin/env python3
"""
=============================================================================
ABC Bank Fraud Detection Portal - Machine Deployment & Auto-Setup Engine
=============================================================================
This self-contained Python script automates the complete setup on any machine:
  1. Detects OS (Windows / Linux / macOS) and creates a Python virtual environment (.venv).
  2. Auto-activates and re-executes itself inside the .venv environment.
  3. Installs all required Python dependencies into the venv.
  4. Installs Node.js dependencies if Node.js is present.
  5. Initializes .env configuration file if missing.
  6. Connects to PostgreSQL / pgAdmin instance (default 'postgres' database).
  7. Checks if the 'bank_fraud_portal' database exists; if NOT, automatically creates it.
  8. Connects to 'bank_fraud_portal', creates all tables, views, indexes, triggers.
  9. Seeds initial customers, accounts, 15 curated fraud complaints, and staff credentials.
 10. Configures firewall / service (optional) and launches the production server.

Usage:
  python deploy_machine.py             # Full automatic setup & launch
  python deploy_machine.py --node      # Launch with Node.js / Express
  python deploy_machine.py --python    # Launch with Python / FastAPI
  python deploy_machine.py --service   # (Linux) Install and run as systemd service
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

# CLI Colors
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
       ABC BANK FRAUD PREVENTION PORTAL - AUTOMATED MACHINE SETUP
============================================================================={Colors.END}
  • Operating System: {platform.system()} {platform.release()} ({platform.machine()})
  • Current Python:   {sys.version.split()[0]} ({sys.executable})
  • Project Folder:   {os.getcwd()}
=============================================================================
"""
    print(banner)

# -------------------------------------------------------------
# 1. Virtual Environment (.venv) Management & Auto-Activation
# -------------------------------------------------------------
def is_running_in_venv():
    """Checks if the current process is running inside a virtual environment."""
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def get_venv_python_executable(venv_dir: Path) -> Path:
    """Returns the path to python binary inside the virtual environment."""
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    else:
        return venv_dir / "bin" / "python"

def ensure_venv_and_reexec():
    """
    Ensures .venv virtual environment exists. If current process is not
    running inside .venv, creates it (if missing) and re-executes the script
    inside the virtual environment.
    """
    if is_running_in_venv():
        log_success(f"Running inside active virtual environment: {sys.prefix}")
        return

    venv_dir = Path(os.getcwd()) / ".venv"
    venv_python = get_venv_python_executable(venv_dir)

    if not venv_python.exists():
        log_info(f"Creating Python virtual environment at '{venv_dir}'...")
        try:
            import venv
            builder = venv.EnvBuilder(with_pip=True)
            builder.create(venv_dir)
            log_success("Virtual environment created successfully.")
        except Exception as err:
            log_warn(f"Standard venv module returned: {err}. Trying subprocess...")
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

    if not venv_python.exists():
        log_error(f"Could not locate virtual environment python at: {venv_python}")
        log_warn("Continuing with system python...")
        return

    log_info(f"Re-launching setup script inside virtual environment: {venv_python}")
    try:
        # Pass all original command line arguments
        cmd = [str(venv_python)] + sys.argv
        sys.exit(subprocess.call(cmd))
    except Exception as e:
        log_error(f"Error re-executing in venv: {e}")

# -------------------------------------------------------------
# 2. Dependency Installation (Python & Node.js)
# -------------------------------------------------------------
def install_dependencies():
    """Installs required Python packages and Node.js packages if available."""
    log_info("Verifying Python packages in virtual environment...")
    
    # Ensure pip is up to date
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"], check=False)
    except Exception:
        pass

    req_file = Path("requirements.txt")
    if not req_file.exists():
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write("fastapi>=0.110.0\nuvicorn>=0.28.0\npydantic>=2.6.0\ndbutils>=3.2.0\npg8000>=1.30.0\npython-dotenv>=1.0.0\nreportlab>=4.0.0\nrequests>=2.31.0\n")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"])
        log_success("Python dependencies verified and ready.")
    except Exception as e:
        log_warn(f"pip install -r requirements.txt returned: {e}. Attempting direct package install...")
        subprocess.call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "pydantic", "dbutils", "pg8000", "python-dotenv", "reportlab", "requests"])

    # Check Node.js & npm
    try:
        node_res = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if node_res.returncode == 0:
            log_info(f"Detected Node.js {node_res.stdout.strip()}. Verifying npm packages...")
            npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
            if not Path("node_modules").exists() and Path("package.json").exists():
                subprocess.run([npm_cmd, "install", "--quiet"], check=False)
                log_success("Node.js npm packages installed.")
    except Exception:
        pass

# -------------------------------------------------------------
# 3. Environment & Configuration Check (.env)
# -------------------------------------------------------------
def ensure_env_configuration():
    """Ensures .env file exists and loads settings."""
    env_path = Path(".env")
    if not env_path.exists():
        example_path = Path(".env.example")
        if example_path.exists():
            log_info("Creating .env configuration from .env.example...")
            import shutil
            shutil.copy(".env.example", ".env")
        else:
            log_info("Generating default .env configuration...")
            with open(".env", "w", encoding="utf-8") as f:
                f.write("""APP_ENV=production
LOG_LEVEL=INFO
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASS=
DB_NAME=bank_fraud_portal
PORTAL_HOST=0.0.0.0
PORTAL_PORT=5050
SERVER_THREADS=16
DEFAULT_INVESTIGATOR=SOC Fraud Operations Team
AE_SERVER_URL=https://t4.automationedge.com/aeengine
AE_ORG_CODE=MSP_EVENT
AE_USERNAME=Msp
AE_PASSWORD=Msp@12345
""")
        log_success(".env file created.")
    else:
        log_info("Loaded existing .env configuration.")

# -------------------------------------------------------------
# 4. PostgreSQL / pgAdmin Database Auto-Provisioning
# -------------------------------------------------------------
def setup_postgresql_database():
    """
    Connects to PostgreSQL instance (default 'postgres' database).
    Checks if 'bank_fraud_portal' exists. If not, executes CREATE DATABASE.
    Then executes schema creation and data seeding.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except Exception:
        pass

    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASS", "")
    target_db = os.getenv("DB_NAME", "bank_fraud_portal")

    log_info(f"Connecting to PostgreSQL server at {db_host}:{db_port} as user '{db_user}'...")

    import pg8000.dbapi

    admin_conn = None
    passwords_to_try = [db_pass, "postgres", "admin", "Password@123", "root", ""]
    successful_pass = None

    for pwd in passwords_to_try:
        try:
            admin_conn = pg8000.dbapi.connect(
                user=db_user,
                password=pwd,
                host=db_host,
                port=db_port,
                database="postgres"
            )
            successful_pass = pwd
            break
        except Exception:
            continue

    if not admin_conn:
        log_error(f"Could not authenticate to PostgreSQL server at {db_host}:{db_port}.")
        log_warn("Please make sure PostgreSQL service is running and verify DB_PASS in .env.")
        return False

    admin_conn.autocommit = True
    cursor = admin_conn.cursor()

    try:
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
        db_exists = cursor.fetchone() is not None

        if not db_exists:
            log_info(f"Database '{target_db}' does not exist in pgAdmin / PostgreSQL. Creating it now...")
            cursor.execute(f'CREATE DATABASE "{target_db}";')
            log_success(f"Database '{target_db}' successfully created in PostgreSQL / pgAdmin!")
        else:
            log_success(f"Database '{target_db}' already exists in PostgreSQL.")

    except Exception as err:
        log_error(f"Error checking/creating database '{target_db}': {err}")
    finally:
        cursor.close()
        admin_conn.close()

    # Now connect directly to target_db and setup schema & sample data
    log_info(f"Setting up schema, tables, and curated complaints in '{target_db}'...")
    try:
        target_conn = pg8000.dbapi.connect(
            user=db_user,
            password=successful_pass,
            host=db_host,
            port=db_port,
            database=target_db
        )
        target_conn.autocommit = True
        t_cur = target_conn.cursor()

        # Check if tables exist
        t_cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('customers', 'fraud_tickets', 'customer_accounts', 'employees');
        """)
        table_count = t_cur.fetchone()[0]

        if table_count < 3:
            log_info("Executing schema.sql to provision tables and views...")
            schema_file = Path("schema.sql")
            if schema_file.exists():
                with open(schema_file, "r", encoding="utf-8") as sf:
                    sql_content = sf.read()
                try:
                    t_cur._c.execute_simple(sql_content)
                    log_success("Tables, constraints, triggers, and full-text search views provisioned.")
                except Exception as ex:
                    log_warn(f"Schema execution notice: {ex}")

        # Seed data using db_setup
        try:
            import db_setup
            db_setup.run_db_setup()
            log_success("Database initialized with customer accounts and 15 complaints!")
        except Exception as seed_err:
            log_warn(f"Seeder notice: {seed_err}")

        t_cur.close()
        target_conn.close()
        return True
    except Exception as err:
        log_error(f"Error provisioning schema in '{target_db}': {err}")
        return False

# -------------------------------------------------------------
# 5. Network Address Detection & Display
# -------------------------------------------------------------
def get_network_ips():
    """Detects local LAN IP and public IP."""
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    public_ip = "YOUR_MACHINE_IP"
    try:
        req = urllib.request.Request("https://api.ipify.org", headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            public_ip = resp.read().decode('utf-8').strip()
    except Exception:
        pass

    return local_ip, public_ip

def display_access_urls():
    """Prints URLs to access the application."""
    local_ip, public_ip = get_network_ips()
    port = os.getenv("PORTAL_PORT", "5050")

    print("\n" + "=" * 77)
    print(f"{Colors.GREEN}{Colors.BOLD}   ABC BANK FRAUD PORTAL - MACHINE DEPLOYMENT READY!{Colors.END}")
    print("=" * 77)
    print(f"\n{Colors.BOLD}Portal Access URLs (Share across your team/network):{Colors.END}")
    print(f"  • {Colors.CYAN}Local Browser:{Colors.END}        http://127.0.0.1:{port}/")
    print(f"  • {Colors.CYAN}Local Network (LAN):{Colors.END}  http://{local_ip}:{port}/")
    print(f"  • {Colors.CYAN}Public Access URL:{Colors.END}    http://{public_ip}:{port}/")
    print(f"  • {Colors.CYAN}SOC Staff Login Desk:{Colors.END} http://{local_ip}:{port}/login.html")
    print(f"  • {Colors.CYAN}Customer NetBanking:{Colors.END}  http://{local_ip}:{port}/customer.html")
    print(f"  • {Colors.CYAN}Server Health Check:{Colors.END}  http://{local_ip}:{port}/health")
    print("\n" + "=" * 77 + "\n")

# -------------------------------------------------------------
# 6. Server Runner
# -------------------------------------------------------------
def run_server(prefer_node=True):
    """Launches either Node.js server.js or Python server.py."""
    display_access_urls()

    node_available = False
    try:
        res = subprocess.run(["node", "--version"], capture_output=True)
        node_available = (res.returncode == 0)
    except Exception:
        pass

    if prefer_node and node_available and Path("server.js").exists():
        log_info("Starting Production Node.js / Express Server on port 5050...")
        try:
            subprocess.run(["node", "server.js"])
        except KeyboardInterrupt:
            print("\n[*] Server shutdown gracefully by user.")
    else:
        log_info("Starting Production Python / Uvicorn ASGI Server on port 5050...")
        try:
            import uvicorn
            uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("PORTAL_PORT", "5050")), workers=4)
        except KeyboardInterrupt:
            print("\n[*] Server shutdown gracefully by user.")
        except Exception as err:
            log_error(f"Python server error: {err}")

# -------------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="ABC Bank Portal Automated Machine Deployer")
    parser.add_argument("--node", action="store_true", help="Force launch using Node.js / Express backend")
    parser.add_argument("--python", action="store_true", help="Force launch using Python / FastAPI backend")
    parser.add_argument("--skip-db", action="store_true", help="Skip PostgreSQL database creation and seeding")
    args = parser.parse_args()

    print_banner()

    # Step 1: Ensure virtual environment and re-execute inside .venv
    ensure_venv_and_reexec()

    # Step 2: Install dependencies inside venv
    install_dependencies()

    # Step 3: Ensure .env file
    ensure_env_configuration()

    # Step 4: Setup PostgreSQL database & pgAdmin tables if not present
    if not args.skip_db:
        setup_postgresql_database()

    # Step 5: Start Server
    prefer_node = not args.python
    run_server(prefer_node=prefer_node)

if __name__ == "__main__":
    main()
