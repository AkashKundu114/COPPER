#!/usr/bin/env python3
"""
Owner GPU Code Generator for C.O.P.P.E.R.

Run this script on the developer/owner system to extract your hardware fingerprint,
format your master activation code, and generate the SHA-256 verification hash.

Usage:
    python scripts/generate_owner_code.py
"""

import hashlib
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.gpu_activation import generate_fingerprint


def main():
    print("=" * 60)
    print("  C.O.P.P.E.R. OWNER GPU CODE GENERATOR")
    print("=" * 60)

    fp = generate_fingerprint()
    code = fp.activation_code
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

    print(f"\n[Hardware Detected]")
    print(f"  GPU Name:         {fp.gpu_name}")
    print(f"  VRAM:             {fp.gpu_vram_mb} MB")
    print(f"  CPU:              {fp.cpu_name}")
    print(f"  OS:               {fp.os_type}")
    print(f"  Machine UUID:     {fp.machine_id}")

    print(f"\n[Master Activation Credentials]")
    print(f"  Activation Code:  {code}")
    print(f"  Validation Hash:  {code_hash}")

    print("\n[Instructions for Sharing]")
    print("1. Share the Activation Code with authorized recipients:")
    print(f"   -> {code}")
    print("\n2. To make this code universally recognized, set in environment or config:")
    print(f"   COPPER_OWNER_CODE_HASH={code_hash}")
    print("=" * 60)


if __name__ == "__main__":
    main()
