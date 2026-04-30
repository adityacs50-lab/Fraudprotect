import subprocess
import sys
import time
import os

def run_backend():
    print("Starting FastAPI backend...")
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--reload", "--port", "8000"])

def run_frontend():
    print("Starting Next.js frontend...")
    # Using npm run dev inside the app directory
    return subprocess.Popen(["npm", "run", "dev"], cwd=os.path.join(os.getcwd(), "app"), shell=True)

if __name__ == "__main__":
    backend_proc = None
    frontend_proc = None
    try:
        backend_proc = run_backend()
        time.sleep(2)  # Give backend a moment to start
        frontend_proc = run_frontend()
        
        print("\n" + "="*50)
        print("FraudShield Platform is running!")
        print("Backend:  http://localhost:8000")
        print("Frontend: http://localhost:3000")
        print("="*50 + "\n")
        
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping platform...")
    finally:
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
