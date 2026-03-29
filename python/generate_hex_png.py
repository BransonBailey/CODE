#!/usr/bin/env python3
"""Generate all combinations of 4 hexadecimal characters with .png extension."""

import itertools

# Hexadecimal characters
hex_chars = '0123456789abcdef'

# Generate all 4-character combinations
combinations = [''.join(p) + '.png' for p in itertools.product(hex_chars, repeat=4)]

# Write to file
with open('hex_combinations.txt', 'w') as f:
    for combo in combinations:
        f.write(combo + '\n')

print(f"Generated {len(combinations)} combinations in hex_combinations.txt")