import json
from datetime import datetime
from typing import Dict, Any, Union, List

try:
    from . import __version__
except ImportError:
    __version__ = "0.2.0"

class ResonanceEvent:
    """
    Defines the standard JSON schema for Resonance events.
    Ensures stability for downstream consumers (Splunk, Grafana, API).
    """
    
    @staticmethod
    def build(
        score: float,
        inputs: Union[List[float], Dict[str, float]],
        algorithm: str = "statistical",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Constructs a standardized event dictionary.
        """
        # normalize inputs to list if numpy array
        if hasattr(inputs, 'tolist'):
            inputs = inputs.tolist()

        status = "ANOMALY" if score == -1 else "NORMAL"
        
        return {
            "schema_version": "1.0",
            "resonance_version": __version__,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": status,
            "analysis": {
                "algorithm": algorithm,
                "score": float(score)
            },
            "telemetry": {
                "inputs": inputs
            },
            "metadata": metadata or {}
        }

    @staticmethod
    def to_json(event_dict: Dict[str, Any]) -> str:
        """Returns the event as a JSON string."""
        return json.dumps(event_dict)
