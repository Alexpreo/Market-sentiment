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
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "dashboard.py"
        ])
    except KeyboardInterrupt:
        print("\nDashboard stopped.")


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

