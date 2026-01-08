import time
import numpy as np
import os
import sys
import argparse
import logging
from resonance import SpectralDetector, ResonanceEvent
from resonance.filters import Debouncer

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

TRIGGER_FILE = "trigger.txt"

_last_net_io = 0
_last_disk_io = 0
_first_run_io = True

# --- DATA GENERATION ---
def get_metrics(is_attack=False, use_real=False, invert_sim=False):
    """
    Returns a vector of 3 metrics.
    Mode REAL: [CPU%, Net_IO_KB, Disk_IO_KB]
    Mode SIM:  [CPU%, Jitter, Memory%]
    """
    global _last_net_io, _last_disk_io, _first_run_io
    
    if use_real and PSUTIL_AVAILABLE:
        real_cpu = psutil.cpu_percent(interval=None)
        
        net_counters = psutil.net_io_counters()
        curr_net = net_counters.bytes_sent + net_counters.bytes_recv
        
        disk_counters = psutil.disk_io_counters()
        curr_disk = disk_counters.read_bytes + disk_counters.write_bytes
        
        if _first_run_io:
            _last_net_io = curr_net
            _last_disk_io = curr_disk
            _first_run_io = False
            return [real_cpu, 0.0, 0.0]

        net_delta = (curr_net - _last_net_io) / 1024.0
        disk_delta = (curr_disk - _last_disk_io) / 1024.0
        
        _last_net_io = curr_net
        _last_disk_io = curr_disk

        if is_attack:
            net_delta += np.random.normal(5000, 1000)

        return [real_cpu, net_delta, disk_delta]
    
    else:
        low_profile = [
            np.random.normal(15, 0.5), # Low CPU
            np.random.normal(5, 0.2),  # Low Jitter
            np.random.normal(20, 0.5)  # Low Mem
        ]
        high_profile = [
            np.random.normal(85, 5),   # High CPU
            np.random.normal(120, 30), # High Jitter
            np.random.normal(80, 5)    # High Mem
        ]

        if invert_sim:
            return low_profile if is_attack else high_profile
        else:
            return high_profile if is_attack else low_profile

# --- SHARED: TRAINING ---
def train_engine(quiet=False, use_real=False, sensitivity=0.02, invert=False):
    if quiet:
        logging.getLogger("resonance").setLevel(logging.ERROR)
    else:
        print(">>> Resonance Core v0.2.0: Initializing...", file=sys.stderr)
        time.sleep(1) 
    
    if use_real and PSUTIL_AVAILABLE:
        check_cpu = psutil.cpu_percent(interval=1.0)
        if check_cpu > 25.0:
             if not quiet:
                print(f"!!! WARNING: High CPU Load detected ({check_cpu}%).", file=sys.stderr)
                print("!!! Training on a busy system will mark high load as 'Normal'.", file=sys.stderr)
                time.sleep(2)

    detector = SpectralDetector(mode='statistical', contamination=sensitivity)
    training_data = []
    
    get_metrics(use_real=use_real, invert_sim=invert)
    time.sleep(0.1)

    if not quiet:
        mode_str = "REAL SENSORS" if use_real else "SIMULATED SENSORS"
        print(f">>> Resonance Core: Sampling {mode_str} (200 samples)...", file=sys.stderr)
        toolbar_width = 40
        sys.stderr.write("[%s]" % (" " * toolbar_width))
        sys.stderr.flush()
        sys.stderr.write("\b" * (toolbar_width + 1)) 

    if quiet:
        for _ in range(200):
            training_data.append(get_metrics(use_real=use_real, invert_sim=invert))
            if use_real: time.sleep(0.05)
    else:
        for i in range(40):
            for _ in range(5): 
                training_data.append(get_metrics(use_real=use_real, invert_sim=invert))
                if use_real: time.sleep(0.05)
            sys.stderr.write("-")
            sys.stderr.flush()
        sys.stderr.write("]\n") 

    detector.fit(training_data)
    
    if not quiet:
        time.sleep(0.5) 
        print(f">>> Resonance Core: Baseline Established. Engine Active.", file=sys.stderr)
    
    return detector

# --- MODE 1: HOLLYWOOD DASHBOARD ---
def run_dashboard(detector, debouncer, use_real, invert):
    try:
        from rich.live import Live
        from rich.table import Table
        from rich.layout import Layout
        from rich.panel import Panel
        from rich import box
    except ImportError:
        print("Error: 'rich' library required for UI.")
        sys.exit(1)

    def make_bar(value, max_val, color="green"):
        width = 20
        draw_val = min(value, max_val)
        num_blocks = int((draw_val / max_val) * width)
        num_blocks = max(1, min(num_blocks, width))
        char = "|" 
        return f"[{color}]{char * num_blocks}[/{color}]"

    def generate_ui(metrics, raw_score, is_alert):
        cpu = metrics[0]
        if use_real:
            mid_val, mid_label = metrics[1], "Net I/O (KB)"
            bot_val, bot_label = metrics[2], "Disk I/O (KB)"
            mid_max, bot_max = 5000.0, 5000.0 
        else:
            mid_val, mid_label = metrics[1], "Net Jitter"
            bot_val, bot_label = metrics[2], "Memory"
            mid_max, bot_max = 100.0, 100.0

        if is_alert:
            status_style = "bold white on red"
            status_text = "CRITICAL THREAT DETECTED"
            border = "red"
        else:
            if raw_score == -1: 
                status_style = "bold black on yellow"
                status_text = "ANALYZING PATTERN..."
                border = "yellow"
            else:
                status_style = "bold white on green"
                status_text = "SYSTEM SECURE"
                border = "green"

        table = Table(box=box.ROUNDED, border_style=border, expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_column("Graph", justify="left", width=25)
         
        cpu_c = "red" if cpu > 80 else "green"
        table.add_row("CPU Load", f"[{cpu_c}]{cpu:.1f}%[/{cpu_c}]", make_bar(cpu, 100, cpu_c))
        
        mid_c = "red" if mid_val > (mid_max * 0.8) else "green"
        table.add_row(mid_label, f"[{mid_c}]{mid_val:.1f}[/{mid_c}]", make_bar(mid_val, mid_max, mid_c))
        
        bot_c = "red" if bot_val > (bot_max * 0.8) else "green"
        table.add_row(bot_label, f"[{bot_c}]{bot_val:.1f}[/{bot_c}]", make_bar(bot_val, bot_max, bot_c))

        return Layout(
            Panel(table, title=f"[{status_style}] {status_text} [/{status_style}]", border_style=border),
            name="top"
        )

    with Live(refresh_per_second=4) as live:
        while True:
            is_attack = os.path.exists(TRIGGER_FILE)
            metrics = get_metrics(is_attack, use_real, invert)
            
            raw_score = detector.score([metrics])[0]
            
            debouncer.trigger(raw_score)
            
            is_alert = debouncer.count >= debouncer.threshold
            
            live.update(generate_ui(metrics, raw_score, is_alert))
            time.sleep(0.2)

# --- MODE 2: STRUCTURED STREAM ---
def run_stream(detector, debouncer, use_json=False, use_real=False, invert=False):
    if not use_json:
        cols = "cpu,net_io,disk_io" if use_real else "cpu,jitter,memory"
        print(f"timestamp,status,raw_score,{cols}") 
    
    try:
        while True:
            is_attack = os.path.exists(TRIGGER_FILE)
            metrics = get_metrics(is_attack, use_real, invert)
            
            raw_score = detector.score([metrics])[0]
            
            debouncer.trigger(raw_score)
            
            is_alert = debouncer.count >= debouncer.threshold
            status = "ANOMALY" if is_alert else "NORMAL"
            
            if use_json:
                event = ResonanceEvent.build(
                    score=raw_score,
                    inputs=metrics,
                    metadata={
                        "host": "localhost", 
                        "trigger_active": is_attack, 
                        "mode": "REAL" if use_real else "SIM",
                        "debounce_count": debouncer.count,
                        "debounce_active": is_alert
                    }
                )
                event["status"] = status
                print(ResonanceEvent.to_json(event))
            else:
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                v1, v2, v3 = metrics
                print(f"{timestamp},{status},{raw_score},{v1:.2f},{v2:.2f},{v3:.2f}")
            
            sys.stdout.flush()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

# --- MODE 3: PRODUCTION WATCHDOG ---
def run_production(detector, debouncer, halt_on_error, use_real=False, invert=False):
    in_alarm_state = False
    try:
        while True:
            is_attack = os.path.exists(TRIGGER_FILE)
            metrics = get_metrics(is_attack, use_real, invert)
            raw_score = detector.score([metrics])[0]

            is_rising_edge = debouncer.trigger(raw_score)
            is_alert = debouncer.count >= debouncer.threshold

            if is_rising_edge and not in_alarm_state:
                event = ResonanceEvent.build(
                    score=raw_score, 
                    inputs=metrics, 
                    metadata={"level": "CRITICAL", "msg": "Anomaly Threshold Breached"}
                )
                event["status"] = "ANOMALY"
                print(ResonanceEvent.to_json(event))
                sys.stdout.flush()
                in_alarm_state = True
                
                if halt_on_error:
                    sys.exit(1)

            elif not is_alert and in_alarm_state:
                event = ResonanceEvent.build(
                    score=raw_score, 
                    inputs=metrics, 
                    metadata={"level": "INFO", "msg": "System Recovered"}
                )
                event["status"] = "NORMAL"
                print(ResonanceEvent.to_json(event))
                sys.stdout.flush()
                in_alarm_state = False
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resonance Biometric Engine CLI (v0.2.0)")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ui", action="store_true", help="Launch Visual Dashboard")
    group.add_argument("--stream", action="store_true", help="Output verbose CSV logs")
    group.add_argument("--json", action="store_true", help="Output verbose JSON logs (New v0.2.0 Schema)")
    group.add_argument("--prod", action="store_true", help="Production Mode: Quiet until anomaly")
    
    parser.add_argument("--halt", action="store_true", help="Halt on error (Prod mode)")
    parser.add_argument("--real", action="store_true", help="Use REAL hardware metrics (requires psutil)")
    # FIXED: Added --retrain so the command doesn't crash
    parser.add_argument("--retrain", action="store_true", help="Force retraining of the baseline model (Default behavior)")
    parser.add_argument("--sensitivity", type=float, default=0.02, help="Anomaly threshold (0.001 - 0.5). Default 0.02")
    parser.add_argument("--threshold", type=int, default=5, help="Debounce: Anomalies required to trigger alert")
    parser.add_argument("--window", type=int, default=60, help="Debounce: Window size in seconds")
    parser.add_argument("--invert", action="store_true", help="SIM ONLY: Normal = High Load, Attack = Crash (Zero)")

    args = parser.parse_args()
    
    if args.real and not PSUTIL_AVAILABLE:
        print("Error: --real requested but 'psutil' not found. Run 'pip install psutil'")
        sys.exit(1)

    quiet_mode = args.json or args.stream or args.prod
    
    # 1. Train
    engine = train_engine(quiet=quiet_mode, use_real=args.real, sensitivity=args.sensitivity, invert=args.invert)

    # 2. Init Debouncer
    gate = Debouncer(threshold=args.threshold, window_seconds=args.window)

    # 3. Run
    if args.stream:
        run_stream(engine, gate, use_json=False, use_real=args.real, invert=args.invert)
    elif args.json:
        run_stream(engine, gate, use_json=True, use_real=args.real, invert=args.invert)
    elif args.prod:
        run_production(engine, gate, args.halt, use_real=args.real, invert=args.invert)
    else:
        run_dashboard(engine, gate, use_real=args.real, invert=args.invert)
