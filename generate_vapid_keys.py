#!/usr/bin/env python3
"""
Generate VAPID keys for push notifications
This script creates new VAPID keys for use with the Web Push protocol.
"""
import base64
import json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    """Generate VAPID keys for Web Push"""
    # Generate a new EC private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Serialize the private key to bytes
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Get the public key
    public_key = private_key.public_key()
    
    # Serialize the public key to bytes
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # Base64 encode the keys (URL-safe, no padding)
    private_key_str = base64.urlsafe_b64encode(private_bytes).decode('utf8').rstrip('=')
    public_key_str = base64.urlsafe_b64encode(public_bytes).decode('utf8').rstrip('=')
    
    # Print the keys for immediate use
    print("VAPID_PRIVATE_KEY = \"" + private_key_str + "\"")
    print("VAPID_PUBLIC_KEY = \"" + public_key_str + "\"")
    
    # Save to a file for easy reference
    with open('vapid_keys.json', 'w') as f:
        json.dump({
            'private_key': private_key_str,
            'public_key': public_key_str
        }, f, indent=2)
    
    print("Keys saved to vapid_keys.json")
    
    # Validation instructions
    print("\nTo use these keys:")
    print("1. Update the VAPID keys in push_service.py")
    print("2. Restart your application")
    print("3. Test with: python3 test_comprehensive_notifications.py")

if __name__ == "__main__":
    generate_vapid_keys()
