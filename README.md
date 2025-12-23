# Resonance Core (`ts-resonance`)

**Resonance** is a lightweight, high-performance library for spectral anomaly detection in multivariate time-series data. 

Designed for signal processing and telemetry analysis, Resonance uses a dual-engine architecture to model the "normal" vibrational state of a system and detect harmonic deviations.

## Features

* **Dual-Engine Architecture:**
    * `statistical`: Fast, efficient outlier detection using isolation forests (O(n)).
    * `neural`: Deep temporal analysis using LSTM Autoencoders for sequence reconstruction.
* **Agnostic Input:** Works with any numerical time-series data (IoT sensors, vibration logs, financial tickers, telemetry).
* **Included CLI Tools:** Comes with a built-in monitoring dashboard for real-time monitoring.

## Installation

Install directly from source:

```bash
pip install git+[https://github.com/resonantcoder/ts-resonance-core.git](https://github.com/resonantcoder/ts-resonance-core.git)
```

*Note: For the visual dashboard features, ensure you have the `rich` library installed (`pip install rich`).*

## CLI Usage 

Resonance includes a production-ready command-line tool (`resonance_cli.py`) for immediate monitoring.

### 1. Visual Dashboard (Default)

Launches a TUI (Text User Interface) for real-time visualization of CPU, Jitter, and Memory biometrics.

```bash
python3 resonance_cli.py --ui
```

*Note: For the visual dashboard features, ensure you have the `rich` library installed (`pip install rich`).*

### 2. Data Stream Mode

Outputs raw, machine-readable CSV logs to STDOUT. Ideal for piping into Splunk, ELK, or other aggregators.

```bash
python3 resonance_cli.py --stream
# Output: 2025-08-16T14:50:01,NORMAL,15.20,5.10,20.00

```

### 3. Production Watchdog

Runs silently in the background. Only outputs logs when an anomaly is detected or resolved.

```bash
python3 resonance_cli.py --prod

```

**Options:**

* `--halt`: Forces the process to exit (System Halt) immediately upon detecting a critical threat.

---

## Python API Quick Start

For integrating Resonance into your own application logic:

```python
import numpy as np
from resonance import SpectralDetector

# 1. Generate some "normal" signal data
t = np.linspace(0, 100, 1000)
normal_signal = np.sin(t) + np.random.normal(0, 0.1, 1000)
normal_signal = normal_signal.reshape(-1, 1)

# 2. Initialize the detector
# Modes: 'statistical' (fast) or 'neural' (deep sequence analysis)
detector = SpectralDetector(mode='statistical', contamination=0.001)

# 3. Learn the "Resonance" (Train)
detector.fit(normal_signal)

# 4. Detect Anomalies
# Create a disrupted signal
disrupted_signal = np.copy(normal_signal)
disrupted_signal[500:550] += 3.0 # Inject a spike

scores = detector.score(disrupted_signal)
# Returns: -1 for Anomaly, 1 for Normal
print(f"Status: {scores}")

```

## Simulation Testing

To simulate an attack while the CLI is running, create a trigger file in the root directory:

```bash
touch trigger.txt   # Starts Attack Simulation
rm trigger.txt      # Restores Normal State

```

## License

MIT License. See `LICENSE` for details.

