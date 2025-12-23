"""
Main Application Entry Point
Starts both the background tracker and Streamlit dashboard.
Run this file to start the entire application.
"""

import threading
import subprocess
import sys
import time
import signal
import os
from tracker import main as tracker_main

tracker_thread = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\nShutting down application...")
    sys.exit(0)


def run_tracker():
    """Run the tracker in a background thread."""
    try:
        tracker_main()
    except Exception as e:
        print(f"Tracker error: {e}")


def run_dashboard():
    """Run the Streamlit dashboard."""
    try:
        import webbrowser
        import socket
        import threading
        
        def wait_for_server(port=8501, timeout=60):
            """Wait for Streamlit server to be ready."""
            start_time = time.time()
            print(f"Waiting for Streamlit to start (timeout: {timeout}s)...")
            while time.time() - start_time < timeout:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    if result == 0:
                        print(f"✓ Streamlit server is ready on port {port}")
                        return True
                except:
                    pass
                elapsed = int(time.time() - start_time)
                if elapsed % 5 == 0 and elapsed > 0:
                    print(f"  Still waiting... ({elapsed}s elapsed)")
                time.sleep(1)
            print(f"⚠ Streamlit did not start within {timeout} seconds")
            return False
        
        def open_browser():
            if wait_for_server(timeout=60):
                time.sleep(2)
                try:
                    webbrowser.open("http://localhost:8501")
                    print("\n✓ Browser opened at http://localhost:8501")
                except Exception as e:
                    print(f"\nCould not open browser automatically: {e}")
                    print("Please manually open: http://localhost:8501")
            else:
                print("\n⚠ Streamlit server did not start in time.")
                print("Please manually open: http://localhost:8501")
                print("Or check the terminal for Streamlit error messages.")
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        print("Starting Streamlit server on http://localhost:8501...")
        print("(This may take 10-30 seconds on first run)")
        
        env = os.environ.copy()
        env['STREAMLIT_SERVER_PORT'] = '8501'
        env['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        env['STREAMLIT_SERVER_HEADLESS'] = 'true'
        
        process = subprocess.Popen(
            [
                sys.executable, "-m", "streamlit", "run", "dashboard.py",
                "--server.port", "8501",
                "--server.address", "localhost",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"Streamlit process started (PID: {process.pid})")
        print("\n" + "="*60)
        print("Streamlit is starting in headless mode...")
        print("="*60 + "\n")
        
        def print_output():
            """Print Streamlit output in real-time."""
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        line = line.strip()
                        if line and not line.startswith('Email:'):
                            print(f"[Streamlit] {line}")
            except:
                pass
        
        output_thread = threading.Thread(target=print_output, daemon=True)
        output_thread.start()
        
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping Streamlit...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    except Exception as e:
        print(f"Error running dashboard: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function that starts both processes."""
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("Starting Market Sentiment Analysis Application")
    print("=" * 60)
    print("\nStarting background tracker...")
    
    global tracker_thread
    tracker_thread = threading.Thread(target=run_tracker, daemon=True)
    tracker_thread.start()
    
    print("✓ Tracker started in background")
    print("\nStarting Streamlit dashboard...")
    print("The dashboard will open in your browser automatically.")
    print("\nPress Ctrl+C to stop both processes.\n")
    print("-" * 60)
    
    time.sleep(2)
    
    try:
        run_dashboard()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()

