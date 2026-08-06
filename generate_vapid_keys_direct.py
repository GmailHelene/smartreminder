#!/usr/bin/env python3
"""
Generate VAPID keys for push notifications
This script creates new VAPID keys suitable for pywebpush.
"""
import base64
import json
import binascii
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    """Generate VAPID keys for Web Push"""
    # Generate a new EC private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Extract the raw private value as an integer
    private_value = private_key.private_numbers().private_value
    
    # Serialize the private value as bytes (32 bytes)
    private_bytes = private_value.to_bytes(32, byteorder='big')
    
    # Encode the private key as base64 URL-safe
    private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf8').rstrip('=')
    
    # Get the public key
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    
    # Get the x and y coordinates (32 bytes each)
    x = public_numbers.x.to_bytes(32, byteorder='big')
    y = public_numbers.y.to_bytes(32, byteorder='big')
    
    # Format public key as uncompressed point (0x04 followed by x and y)
    public_bytes = b'\x04' + x + y
    
    # Encode the public key as base64 URL-safe
    public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf8').rstrip('=')
    
    # Print the keys for immediate use
    print("VAPID_PRIVATE_KEY = \"" + private_key_b64 + "\"")
    print("VAPID_PUBLIC_KEY = \"" + public_key_b64 + "\"")
    
    # Save to a file for easy reference
    with open('vapid_keys_direct.json', 'w') as f:
        json.dump({
            'private_key': private_key_b64,
            'public_key': public_key_b64
        }, f, indent=2)
    
    print("Keys saved to vapid_keys_direct.json")
    
    # Print as hex for debugging
    print("\nDebug info (hex format):")
    print(f"Private key (hex): {binascii.hexlify(private_bytes).decode()}")
    print(f"Public key (hex): {binascii.hexlify(public_bytes).decode()}")

if __name__ == "__main__":
    generate_vapid_keys()
