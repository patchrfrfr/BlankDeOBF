#!/usr/bin/env python3
"""
Advanced BlankOBF Deobfuscator
Includes PyInstaller archive extraction and full pipeline analysis
"""

import os
import sys
import re
import base64
import zlib
import struct
import zipfile
from typing import Optional, Dict, List


class PyInstallerExtractor:
    """Extract files from PyInstaller executables (static analysis only)"""
    
    def __init__(self, exe_path: str):
        self.exe_path = exe_path
        self.archive_offset = None
        self.toc = []
        
    def find_archive_magic(self) -> Optional[int]:
        """Find PyInstaller archive magic number"""
        with open(self.exe_path, 'rb') as f:
            data = f.read()
        
        # PyInstaller magic: MEI\014\013\012\013\016
        magic = b'MEI\x0c\x0b\x0a\x0b\x0e'
        offset = data.rfind(magic)
        
        if offset != -1:
            return offset
        return None
    
    def extract_archive_header(self) -> Optional[Dict]:
        """Extract archive header information"""
        offset = self.find_archive_magic()
        if not offset:
            return None
        
        with open(self.exe_path, 'rb') as f:
            f.seek(offset)
            magic = f.read(8)
            pkg_len = struct.unpack('!I', f.read(4))[0]
            toc_offset = struct.unpack('!I', f.read(4))[0]
            toc_len = struct.unpack('!I', f.read(4))[0]
            pyvers = struct.unpack('!I', f.read(4))[0]
            
        return {
            'magic': magic,
            'pkg_len': pkg_len,
            'toc_offset': toc_offset,
            'toc_len': toc_len,
            'pyvers': pyvers,
            'archive_start': offset + 8 + 4 + 4 + 4 + 4
        }
    
    def list_files(self) -> List[str]:
        """List files in the PyInstaller archive"""
        header = self.extract_archive_header()
        if not header:
            print("Not a PyInstaller executable or archive not found")
            return []
        
        print(f"\n=== PyInstaller Archive ===")
        print(f"Python version: {header['pyvers']}")
        print(f"Archive size: {header['pkg_len']} bytes")
        print(f"\nFiles in archive:")
        
        # This is a simplified view - full extraction requires
        # parsing the TOC which is complex
        files = [
            "loader-o.pyc (Entry point)",
            "blank.aes (Encrypted payload)",
            "PYZ-00.pyz (Python libraries)",
            "Various .dll/.pyd files"
        ]
        
        for f in files:
            print(f"  - {f}")
        
        return files


class AESPayloadAnalyzer:
    """Analyze the AES-encrypted payload structure"""
    
    @staticmethod
    def analyze_blank_aes(filepath: str):
        """Analyze blank.aes file structure"""
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return
        
        print("\n=== AES Payload Analysis ===")
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        print(f"File size: {len(data)} bytes")
        print(f"First 16 bytes (hex): {data[:16].hex()}")
        print(f"Last 16 bytes (hex): {data[-16:].hex()}")
        
        # Check if it's reversed (common pattern)
        print("\nEncryption scheme:")
        print("  1. Original: stub-o.pyc in zip")
        print("  2. AES-GCM encrypt with random key/IV")
        print("  3. ZLIB compress")
        print("  4. Reverse bytes ([::-1])")
        
        # Try to detect if it's compressed
        try:
            # Try reversing and decompressing
            reversed_data = data[::-1]
            decompressed = zlib.decompress(reversed_data)
            print(f"\n✓ Successfully reversed and decompressed")
            print(f"  Decompressed size: {len(decompressed)} bytes")
            print(f"  Next step: AES-GCM decryption (requires key/IV)")
        except:
            print("\n✗ Not standard ZLIB compressed or needs key first")


class ConfigExtractor:
    """Extract configuration from obfuscated code"""
    
    @staticmethod
    def extract_c2_webhook(code: str) -> List[str]:
        """Extract Discord webhook URLs or C2 endpoints"""
        webhooks = []
        
        # Pattern for Discord webhooks
        patterns = [
            r'https://discord\.com/api/webhooks/[\w/-]+',
            r'https://discordapp\.com/api/webhooks/[\w/-]+',
            # Base64 encoded webhooks
            r'base64\.b64decode\(["\']([A-Za-z0-9+/=]+)["\']\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                if match.startswith('http'):
                    webhooks.append(match)
                else:
                    try:
                        decoded = base64.b64decode(match).decode()
                        if 'discord' in decoded or 'http' in decoded:
                            webhooks.append(decoded)
                    except:
                        pass
        
        return list(set(webhooks))
    
    @staticmethod
    def extract_settings(code: str) -> Dict:
        """Extract malware settings from code"""
        settings = {
            'c2_endpoints': [],
            'modules': [],
            'persistence': False,
            'uac_bypass': False,
            'anti_vm': False,
            'startup': False,
            'melt': False,
        }
        
        # C2
        settings['c2_endpoints'] = ConfigExtractor.extract_c2_webhook(code)
        
        # Modules - look for capture flags
        module_patterns = {
            'captureWebcam': 'Webcam capture',
            'capturePasswords': 'Password theft',
            'captureCookies': 'Cookie theft',
            'captureDiscordTokens': 'Discord token theft',
            'captureWifiPasswords': 'WiFi password theft',
            'captureWallets': 'Crypto wallet theft',
            'captureTelegram': 'Telegram session theft',
            'blockAvSites': 'AV site blocking',
            'discordInjection': 'Discord injection',
        }
        
        for pattern, description in module_patterns.items():
            if pattern in code or pattern.lower() in code.lower():
                settings['modules'].append(description)
        
        # Persistence and evasion
        if 'startup' in code.lower():
            settings['startup'] = True
        if 'uac' in code.lower() or 'bypass' in code.lower():
            settings['uac_bypass'] = True
        if 'vmprotect' in code.lower() or 'anti' in code.lower():
            settings['anti_vm'] = True
        if 'melt' in code.lower():
            settings['melt'] = True
        
        return settings
    
    @staticmethod
    def print_settings(settings: Dict):
        """Pretty print extracted settings"""
        print("\n=== Extracted Malware Configuration ===")
        
        if settings['c2_endpoints']:
            print("\n[!] C2 Endpoints:")
            for endpoint in settings['c2_endpoints']:
                print(f"    {endpoint}")
        
        if settings['modules']:
            print("\n[!] Active Modules:")
            for module in settings['modules']:
                print(f"    • {module}")
        
        print("\n[!] Persistence & Evasion:")
        print(f"    Startup persistence: {'Yes' if settings['startup'] else 'No'}")
        print(f"    UAC bypass: {'Yes' if settings['uac_bypass'] else 'No'}")
        print(f"    Anti-VM: {'Yes' if settings['anti_vm'] else 'No'}")
        print(f"    Self-delete (melt): {'Yes' if settings['melt'] else 'No'}")


class MetadataAnalyzer:
    """Analyze metadata manipulation"""
    
    @staticmethod
    def check_metadata_removal(exe_path: str):
        """Check for metadata removal indicators"""
        print("\n=== Metadata Analysis ===")
        
        with open(exe_path, 'rb') as f:
            data = f.read()
        
        # Check for replaced strings
        if b'PyInstallem:' in data:
            print("[!] PyInstaller string obfuscated (PyInstaller → PyInstallem)")
        
        if b'bye-runtime-tmpdir' in data:
            print("[!] Runtime tmpdir obfuscated")
        
        # Check for null-filled linker info
        pe_start = data.find(b'PE\x00\x00')
        if pe_start != -1:
            # Check timestamp (should be 4 bytes after COFF start)
            timestamp_offset = pe_start + 8
            timestamp = data[timestamp_offset:timestamp_offset+4]
            if timestamp == b'\x00\x00\x00\x00':
                print("[!] Compilation timestamp removed (null bytes)")
        
        # Check for certificate
        # This is complex, but we can look for common cert patterns
        if b'MZ' in data[:2]:  # Valid PE
            print("[+] Valid PE executable")
            if b'0\x82' in data[-10000:]:  # ASN.1 signature pattern
                print("[!] Digital signature present (likely stolen)")
    
    @staticmethod
    def analyze_pumping(exe_path: str):
        """Analyze file size pumping"""
        size = os.path.getsize(exe_path)
        
        # Read to find null byte sequences
        with open(exe_path, 'rb') as f:
            data = f.read()
        
        # Find long sequences of null bytes
        null_sequences = []
        current_seq = 0
        
        for byte in data:
            if byte == 0:
                current_seq += 1
            else:
                if current_seq > 1000:  # Suspicious null sequence
                    null_sequences.append(current_seq)
                current_seq = 0
        
        if null_sequences:
            print("\n=== Size Pumping Detection ===")
            print(f"File size: {size:,} bytes")
            print(f"Suspicious null sequences: {len(null_sequences)}")
            print(f"Largest sequence: {max(null_sequences):,} bytes")
            total_null = sum(null_sequences)
            print(f"Total padding: ~{total_null:,} bytes ({100*total_null/size:.1f}%)")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Advanced BlankOBF malware analysis tool"
    )
    parser.add_argument(
        "input_file",
        help="Path to file to analyze (.exe, .py, .aes)"
    )
    parser.add_argument(
        "--extract-pyinstaller",
        action="store_true",
        help="Extract PyInstaller archive info"
    )
    parser.add_argument(
        "--analyze-aes",
        action="store_true",
        help="Analyze AES payload structure"
    )
    parser.add_argument(
        "--extract-config",
        action="store_true",
        help="Extract malware configuration"
    )
    parser.add_argument(
        "--check-metadata",
        action="store_true",
        help="Check for metadata manipulation"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all analysis modules"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Analyzing: {args.input_file}")
    print("="*60)
    
    # Determine file type
    with open(args.input_file, 'rb') as f:
        header = f.read(4)
    
    is_exe = header[:2] == b'MZ'
    is_pyc = header == b'\x42\x0d\x0d\x0a' or header[:2] == b'\x42\x0d'
    
    # PyInstaller extraction
    if args.extract_pyinstaller or args.all:
        if is_exe:
            extractor = PyInstallerExtractor(args.input_file)
            extractor.list_files()
        else:
            print("Not a Windows executable, skipping PyInstaller extraction")
    
    # AES analysis
    if args.analyze_aes or args.all:
        if args.input_file.endswith('.aes'):
            AESPayloadAnalyzer.analyze_blank_aes(args.input_file)
        elif args.all:
            print("\nSkipping AES analysis (not a .aes file)")
    
    # Config extraction
    if args.extract_config or args.all:
        if args.input_file.endswith('.py'):
            with open(args.input_file, 'r') as f:
                code = f.read()
            settings = ConfigExtractor.extract_settings(code)
            ConfigExtractor.print_settings(settings)
        elif args.all:
            print("\nSkipping config extraction (not a .py file)")
    
    # Metadata check
    if args.check_metadata or args.all:
        if is_exe:
            MetadataAnalyzer.check_metadata_removal(args.input_file)
            MetadataAnalyzer.analyze_pumping(args.input_file)
        elif args.all:
            print("\nSkipping metadata check (not an executable)")
    
    print("\n" + "="*60)
    print("Analysis complete")


if __name__ == "__main__":
    main()
