"""
GPU Hardware Activation & Licensing Engine for C.O.P.P.E.R.

Enforces zero-cloud offline hardware validation via deterministic fingerprinting:
1. Option A (Local Hardware): Generates a hardware fingerprint from local GPU + machine UUID,
   enabling direct execution on compatible user hardware.
2. Option B (Owner Master Code): Allows friends/colleagues to enter the project owner's
   (Akash's) pre-shared activation code, unlocking runtime access.
"""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
from typing import Any

ACTIVATION_DIR = Path.home() / ".copper"
ACTIVATION_FILE = ACTIVATION_DIR / "activation.json"

# Default fallback hash if COPPER_OWNER_CODE_HASH is not set in environment.
# This embeds the owner's authorized activation hash (derived from Akash's RTX 5060 fingerprint).
DEFAULT_OWNER_CODE_HASH = os.getenv(
    "COPPER_OWNER_CODE_HASH",
    "71a81efef1517110a12be96f5ab37ab0be2d41c782c83bd58aa9d7719a0ebb8b",
)


@dataclass
class HardwareFingerprint:
    gpu_name: str = "Unknown"
    gpu_vram_mb: int = 0
    cpu_name: str = "Unknown"
    os_type: str = platform.system()
    machine_id: str = ""

    @property
    def fingerprint_hash(self) -> str:
        """Deterministic SHA-256 digest of core hardware coordinates."""
        raw = f"{self.gpu_name}|{self.gpu_vram_mb}|{self.cpu_name}|{self.machine_id}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @property
    def activation_code(self) -> str:
        """Formatted human-readable code: COPPER-XXXX-XXXX-XXXX"""
        h = self.fingerprint_hash.upper()
        return f"COPPER-{h[:4]}-{h[4:8]}-{h[8:12]}"


@dataclass
class ActivationState:
    activated: bool = False
    mode: str = "none"  # "local_gpu" | "owner_code" | "none"
    fingerprint: str = ""
    activation_code: str = ""
    owner_code_hash: str = ""
    gpu_info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_gpu() -> dict[str, Any]:
    """
    Detects dedicated NVIDIA GPU via nvidia-smi with graceful fallback
    to Windows WMI or generic platform checks.
    """
    # 1. Try nvidia-smi
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=4,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            parts = [p.strip() for p in proc.stdout.strip().split("\n")[0].split(",")]
            name = parts[0]
            vram = int(float(parts[1])) if len(parts) > 1 else 0
            return {
                "name": name,
                "vram_mb": vram,
                "available": True,
                "is_dedicated": True,
                "driver": "nvidia",
            }
    except Exception:
        pass

    # 2. Windows WMI fallback
    if platform.system() == "Windows":
        try:
            cmd = "Get-CimInstance Win32_VideoController | Select-Object -First 1 -ExpandProperty Name"
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=4,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return {
                    "name": proc.stdout.strip(),
                    "vram_mb": 0,
                    "available": True,
                    "is_dedicated": False,
                    "driver": "windows_wmi",
                }
        except Exception:
            pass

    return {
        "name": "Generic CPU Runtime",
        "vram_mb": 0,
        "available": False,
        "is_dedicated": False,
        "driver": "cpu",
    }


def get_machine_uuid() -> str:
    """Retrieves unique machine UUID without requiring network access."""
    if platform.system() == "Windows":
        try:
            cmd = "(Get-CimInstance Win32_ComputerSystemProduct).UUID"
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=4,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception:
            pass
    elif platform.system() == "Linux":
        for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return f.read().strip()
                except Exception:
                    pass

    return platform.node() or "COPPER-SYSTEM-DEFAULT"


def generate_fingerprint() -> HardwareFingerprint:
    """Generates the hardware fingerprint from current host telemetry."""
    gpu = detect_gpu()
    cpu = platform.processor() or platform.machine() or "Unknown CPU"
    uuid = get_machine_uuid()
    return HardwareFingerprint(
        gpu_name=gpu["name"],
        gpu_vram_mb=gpu["vram_mb"],
        cpu_name=cpu,
        os_type=platform.system(),
        machine_id=uuid,
    )


def save_activation(state: ActivationState) -> None:
    """Saves activation state to local user directory ~/.copper/activation.json."""
    try:
        ACTIVATION_DIR.mkdir(parents=True, exist_ok=True)
        with open(ACTIVATION_FILE, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save activation state: {e}")


def load_activation() -> ActivationState:
    """Loads activation state from disk."""
    if ACTIVATION_FILE.exists():
        try:
            with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ActivationState(**data)
        except Exception:
            pass
    return ActivationState()


def is_activated() -> bool:
    """Checks whether COPPER is currently authorized to run."""
    return load_activation().activated


def activate_local_gpu() -> ActivationState:
    """Activates the app using the local system GPU/hardware fingerprint."""
    fp = generate_fingerprint()
    state = ActivationState(
        activated=True,
        mode="local_gpu",
        fingerprint=fp.fingerprint_hash,
        activation_code=fp.activation_code,
        gpu_info={"name": fp.gpu_name, "vram_mb": fp.gpu_vram_mb},
    )
    save_activation(state)
    return state


def validate_owner_code(input_code: str, expected_hash: str | None = None) -> bool:
    """
    Validates a user-supplied code against the owner's code hash.
    Case-insensitive with whitespace trimmed.
    """
    clean = input_code.strip().upper()
    target_hash = expected_hash or os.getenv("COPPER_OWNER_CODE_HASH") or DEFAULT_OWNER_CODE_HASH
    if not target_hash:
        return False
    computed_hash = hashlib.sha256(clean.encode("utf-8")).hexdigest()
    return computed_hash.lower() == target_hash.lower()


def activate_with_owner_code(code: str, expected_hash: str | None = None) -> ActivationState:
    """
    Authorizes COPPER using the owner's shared master code.
    """
    target_hash = expected_hash or os.getenv("COPPER_OWNER_CODE_HASH") or DEFAULT_OWNER_CODE_HASH
    if not validate_owner_code(code, target_hash):
        return ActivationState(activated=False, mode="none")

    fp = generate_fingerprint()
    state = ActivationState(
        activated=True,
        mode="owner_code",
        fingerprint=fp.fingerprint_hash,
        activation_code=code.strip().upper(),
        owner_code_hash=target_hash,
        gpu_info={"name": fp.gpu_name, "vram_mb": fp.gpu_vram_mb},
    )
    save_activation(state)
    return state


def revoke_activation() -> bool:
    """Revokes the current activation license."""
    if ACTIVATION_FILE.exists():
        try:
            ACTIVATION_FILE.unlink()
            return True
        except Exception:
            return False
    return True
