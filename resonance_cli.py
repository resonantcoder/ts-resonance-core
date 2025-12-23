import time
import numpy as np
import os
import sys
import argparse
from datetime import datetime
from resonance import SpectralDetector

# --- CONFIGURATION ---
TRIGGER_FILE = "trigger.txt"

# --- DATA GENERATION (SIMULATION) ---
def get_metrics(is_attack=False):
    if not is_attack:
        return [
            np.random.normal(15, 0.5), # CPU
            np.random.normal(5, 0.2),  # Jitter
            np.random.normal(20, 0.5)  # Memory
        ]
    else:
        return [
            np.random.normal(85, 10),  # CPU Spike
            np.random.normal(120, 30), # Jitter Chaos
            np.random.normal(60, 5)    # Memory Leak
        ]

# --- SHARED: TRAINING ---
def train_engine():
    """Trains the engine and returns the detector."""
    # We write to stderr so it doesn't mess up the --stream CSV output
    print(">>> Resonance Core: Initializing Neural Interfaces...", file=sys.stderr)
    time.sleep(1) # Dramatic pause for "loading"
    
    detector = SpectralDetector(mode='statistical', contamination=0.001)
    
    # Generate baseline data with simulated "Hardware Polling" delay
    training_data = []
    print(">>> Resonance Core: Sampling Hardware Biometrics (200 samples)...", file=sys.stderr)
    
    # Create a simple progress bar effect
    toolbar_width = 40
    sys.stderr.write("[%s]" % (" " * toolbar_width))
    sys.stderr.flush()
    sys.stderr.write("\b" * (toolbar_width + 1)) # Return to start of line, after '['

    for i in range(toolbar_width):
        # Simulate gathering a batch of data from the router
        for _ in range(5): 
            training_data.append(get_metrics(is_attack=False))
        
        # Update progress bar
        sys.stderr.write("-")
        sys.stderr.flush()
        
        # THIS IS THE THEATRICAL DELAY
        # Simulating network latency/sensor read time
        time.sleep(0.1) 

    sys.stderr.write("]\n") # End progress bar
    
    print(">>> Resonance Core: Fitting Spectral Model...", file=sys.stderr)
    detector.fit(training_data)
    time.sleep(0.5) # Slight pause for "Thinking". Remove for performance.
    
    print(f">>> Resonance Core: Baseline Established on {len(training_data)} vectors. Engine Active.", file=sys.stderr)
    return detector

# --- MODE 1: HOLLYWOOD DASHBOARD (Rich UI) ---
def run_dashboard(detector):
    from rich.live import Live
    from rich.table import Table
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich import box

    logs = []

    # Helper function to create safe, scaled bars
    def make_bar(value, max_val, color="green"):
        # Scale value to a max width of 20 characters
        width = 20
        num_blocks = int((value / max_val) * width)
        # Clamp between 1 (so it's always visible) and width
        num_blocks = max(1, min(num_blocks, width))
        
        # Use a safe block character
        char = "|" 
        return f"[{color}]{char * num_blocks}[/{color}]"

    def generate_ui(metrics, score, is_attack):
        cpu, jitter, mem = metrics
        
        # Status Logic
        if score == -1:
            status_style = "bold white on red"
            status_text = "CRITICAL THREAT DETECTED"
            border = "red"
        else:
            status_style = "bold white on green"
            status_text = "SYSTEM SECURE"
            border = "green"

        if is_attack and score == 1:
            status_text = "ANALYZING PATTERN..."
            status_style = "bold black on yellow"

        # Table
        table = Table(box=box.ROUNDED, border_style=border, expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_column("Graph", justify="left", width=25)
        
        # 1. CPU (Max expected ~100)
        cpu_c = "red" if cpu > 50 else "green"
        table.add_row("CPU Load", f"[{cpu_c}]{cpu:.1f}%[/{cpu_c}]", make_bar(cpu, 100, cpu_c))
        
        # 2. Jitter (Max expected ~150, but normal is 5. Scale based on 100 for visibility)
        jit_c = "red" if jitter > 20 else "green"
        table.add_row("Net Jitter", f"[{jit_c}]{jitter:.1f}ms[/{jit_c}]", make_bar(jitter, 100, jit_c))
        
        # 3. Memory (Max expected ~100)
        mem_c = "red" if mem > 60 else "green"
        table.add_row("Memory", f"[{mem_c}]{mem:.1f}%[/{mem_c}]", make_bar(mem, 100, mem_c))

        return Layout(
            Panel(table, title=f"[{status_style}] {status_text} [/{status_style}]", border_style=border),
            name="top"
        )

    with Live(refresh_per_second=4) as live:
        while True:
            is_attack = os.path.exists(TRIGGER_FILE)
            metrics = get_metrics(is_attack)
            score = detector.score([metrics])[0]
            
            # Simple logging for UI
            if score == -1:
                logs.append(f"[ALERT] Deviation Detected")
            
            live.update(generate_ui(metrics, score, is_attack))
            time.sleep(0.2)

# --- MODE 2: SIMPLE STREAM (Verbose STDOUT) ---
def run_stream(detector):
    """Outputs a continuous log stream to STDOUT."""
    print("timestamp,status,cpu,jitter,memory") # CSV Header
    try:
        while True:
            is_attack = os.path.exists(TRIGGER_FILE)
            metrics = get_metrics(is_attack)
            score = detector.score([metrics])[0]
            
            timestamp = datetime.now().isoformat()
            cpu, jitter, mem = metrics
            
            status = "NORMAL" if score == 1 else "ANOMALY"
            
            # Formatted line
            print(f"{timestamp},{status},{cpu:.2f},{jitter:.2f},{mem:.2f}")
            sys.stdout.flush()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

# --- MODE 3: PRODUCTION WATCHDOG (Quiet until Alert) ---
def run_production(detector, halt_on_error):
    """Silent until anomaly. Handles alerting and optional exit."""
    in_alarm_state = False
    
    try:
        while True:
            is_attack = os.path.exists(TRIGGER_FILE)
            metrics = get_metrics(is_attack)
            score = detector.score([metrics])[0]
            timestamp = datetime.now().isoformat()
            cpu, jitter, mem = metrics

            # ANOMALY DETECTED
            if score == -1:
                if not in_alarm_state:
                    # RISING EDGE (New Alarm)
                    print(f"{{'level': 'CRITICAL', 'time': '{timestamp}', 'msg': 'Anomaly Detected', 'metrics': {{'cpu': {cpu:.1f}, 'jitter': {jitter:.1f}}}}}")
                    sys.stdout.flush()
                    in_alarm_state = True
                    
                    if halt_on_error:
                        print(f"{{'level': 'FATAL', 'time': '{timestamp}', 'msg': 'Halt on Error configured. Exiting.'}}")
                        sys.exit(1)
                else:
                    # Still in alarm state... silence or heartbeat? 
                    # Usually keep quiet to reduce log spam, or log every N seconds.
                    pass

            # RECOVERY DETECTED
            elif score == 1 and in_alarm_state:
                # FALLING EDGE (Recovery)
                print(f"{{'level': 'INFO', 'time': '{timestamp}', 'msg': 'Anomaly Resolved. System Normal.'}}")
                sys.stdout.flush()
                in_alarm_state = False
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        pass

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resonance Biometric CLI")
    
    # Mode selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ui", action="store_true", help="Launch the Visual Dashboard (Default)")
    group.add_argument("--stream", action="store_true", help="Output verbose logs to STDOUT (No UI)")
    group.add_argument("--prod", action="store_true", help="Production Mode: Quiet until anomaly detected")
    
    # Options
    parser.add_argument("--halt", action="store_true", help="In Production mode, exit process immediately on detection")

    args = parser.parse_args()

    # 1. Train first (common to all modes)
    engine = train_engine()

    # 2. Dispatch
    if args.stream:
        run_stream(engine)
    elif args.prod:
        run_production(engine, args.halt)
    else:
        # Default to UI
        try:
            run_dashboard(engine)
        except ImportError:
            print("Error: 'rich' library not found. Run 'pip install rich' or use --stream mode.")
