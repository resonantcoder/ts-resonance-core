import numpy as np
from resonance import SpectralDetector
import time

def generate_signal(length=1000, noise_level=0.1):
    """Generates a synthetic 'heartbeat' signal (Sine wave + Noise)."""
    t = np.linspace(0, 100, length)
    # A smooth sine wave representing a healthy device/router
    signal = np.sin(t) 
    # Add some random noise (network jitter simulation)
    noise = np.random.normal(0, noise_level, length)
    return (signal + noise).reshape(-1, 1)

def print_ascii_graph(signal, scores, start_idx=480, end_idx=540):
    """Prints a cool ASCII visualization of the anomaly."""
    print("\n--- VISUALIZATION (Time Steps 480-540) ---")
    for i in range(start_idx, end_idx):
        val = signal[i][0]
        score = scores[i]
        
        # Determine status
        is_anomaly = score == -1
        status = " [!!! ANOMALY !!!]" if is_anomaly else " [OK]"
        
        # Simple bar chart
        bar_len = int((val + 2) * 10) # Shift up and scale
        bar = "#" * bar_len
        
        print(f"T={i:03d} | {val:+.2f} | {bar:<40} {status}")

def run_demo():
    print(">>> RESONANCE CORE: SYSTEM STARTUP")
    print(">>> Mode: Statistical (Isolation Forest)")
    
    # 1. GENERATE HEALTHY TRAINING DATA
    print("\n[1] Learning baseline vibration patterns...")
    train_data = generate_signal(length=1000)
    
    # Initialize the engine
    # window_size doesn't matter much for Statistical mode, but we set it anyway
    detector = SpectralDetector(mode='statistical', contamination=0.05)
    
    # Fit the model (This is what you do in the 'Training' phase)
    detector.fit(train_data)
    print("    Model Fitted Successfully.")

    # 2. GENERATE ATTACK DATA
    print("\n[2] Simulating live data stream...")
    test_data = generate_signal(length=1000)
    
    # INJECT ANOMALY: A sudden spike at index 500-520
    print("    >> INJECTING 'IMPOSTER' SIGNAL AT T=500...")
    test_data[500:520] += 4.0 # Massive spike
    
    # 3. DETECT
    print("[3] Analyzing spectrum...")
    start_time = time.time()
    scores = detector.score(test_data)
    end_time = time.time()
    
    print(f"    Analysis complete in {(end_time - start_time):.4f} seconds.")
    
    # 4. REPORT
    anomalies = np.where(scores == -1)[0]
    print(f"\n[4] REPORT:")
    print(f"    Total Time Steps: {len(test_data)}")
    print(f"    Anomalies Detected: {len(anomalies)}")
    
    if len(anomalies) > 0:
        print(f"    First Detection at: T={anomalies[0]}")
        print_ascii_graph(test_data, scores)
    else:
        print("    No anomalies detected.")

if __name__ == "__main__":
    run_demo()
