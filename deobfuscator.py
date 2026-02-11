#!/usr/bin/env python3
"""
Static Python Deobfuscator for BlankOBF
Reverses obfuscation without executing any code
"""

import re
import base64
import codecs
import marshal
import lzma
import ast
import sys
from typing import Optional, Tuple


class BlankOBFDeobfuscator:
    """Static deobfuscator for BlankOBF obfuscated Python code"""
    
    def __init__(self, obfuscated_code: str):
        self.code = obfuscated_code
        self.deobfuscated = None
        
    def extract_string_from_encryption(self, encrypted_expr: str) -> Optional[str]:
        """
        Extract plaintext from encrypted string expressions like:
        getattr(__import__(bytes([98, 97, 115, 101, 54, 52]).decode()), 
                bytes([98, 54, 52, 100, 101, 99, 111, 100, 101]).decode())
        """
        try:
            # Pattern for bytes([...]).decode()
            bytes_pattern = r'bytes\(\[([\d,\s]+)\]\)\.decode\(\)'
            matches = re.findall(bytes_pattern, encrypted_expr)
            
            if matches:
                byte_list = [int(x.strip()) for x in matches[0].split(',')]
                return bytes(byte_list).decode()
            
            # Pattern for base64 encoded strings
            b64_pattern = r'base64\.b64decode\(["\']([A-Za-z0-9+/=]+)["\']\)\.decode\(\)'
            matches = re.findall(b64_pattern, encrypted_expr)
            if matches:
                return base64.b64decode(matches[0]).decode()
                
        except Exception:
            pass
        return None
    
    def decrypt_layer2(self, code: str) -> Optional[str]:
        """
        Decrypt the second encryption layer (LZMA compressed)
        Pattern: compressed byte arrays stored in variables
        """
        try:
            # Method 1: Direct byte literal (e.g., ________ = b'...')
            match = re.search(r'(\w+)\s*=\s*(b["\'][^"\']*["\']|b\'\'\'.*?\'\'\')', code, re.DOTALL)
            if match:
                try:
                    compressed_data = ast.literal_eval(match.group(2))
                    if compressed_data and isinstance(compressed_data, bytes):
                        try:
                            decompressed = lzma.decompress(compressed_data)
                            return decompressed.decode('utf-8')
                        except:
                            pass
                except:
                    pass
            
            # Method 2: Look for bytes([...]) and try to reconstruct
            # This handles the obfuscated case where bytes are stored as integer arrays
            bytes_array_pattern = r'(\w+)\s*=\s*b\'[^\']*\''
            matches = re.findall(bytes_array_pattern, code, re.DOTALL)
            
            for match_str in matches:
                try:
                    # Try to extract the actual bytes
                    full_match = re.search(rf'{re.escape(match_str)}\s*=\s*(b\'[^\']*\')', code, re.DOTALL)
                    if full_match:
                        byte_data = ast.literal_eval(full_match.group(1))
                        try:
                            decompressed = lzma.decompress(byte_data)
                            return decompressed.decode('utf-8')
                        except:
                            continue
                except:
                    continue
                    
        except Exception as e:
            print(f"Layer 2 decryption error: {e}", file=sys.stderr)
        
        return None
    
    def decrypt_layer1(self, code: str) -> Optional[str]:
        """
        Decrypt the first encryption layer (base64 + rot13)
        Pattern: var1="...";var2="...";var3="...";var4="..."
        Then: codecs.decode(var1, rot13) + var2 + var3[::-1] + var4
        """
        try:
            # Extract variable assignments
            var_pattern = r'(\w+)\s*=\s*"([^"]*)"'
            variables = {}
            
            for match in re.finditer(var_pattern, code):
                var_name = match.group(1)
                var_value = match.group(2)
                variables[var_name] = var_value
            
            if len(variables) < 4:
                return None
            
            # Find the concatenation pattern
            # Pattern: codecs.decode(var1, 'rot13') + var2 + var3[::-1] + var4
            concat_pattern = r'codecs\.decode\((\w+),.*?\)\+(\w+)\+(\w+)\[::-1\]\+(\w+)'
            match = re.search(concat_pattern, code)
            
            if not match:
                return None
            
            var1, var2, var3, var4 = match.groups()
            
            # Reconstruct the base64 string
            part1 = codecs.decode(variables.get(var1, ''), 'rot13')
            part2 = variables.get(var2, '')
            part3 = variables.get(var3, '')[::-1]  # Reverse
            part4 = variables.get(var4, '')
            
            base64_string = part1 + part2 + part3 + part4
            
            # Decode base64
            decoded = base64.b64decode(base64_string)
            
            # Unmarshal
            code_obj = marshal.loads(decoded)
            
            # Decompile (basic reconstruction)
            import dis
            import io
            
            output = io.StringIO()
            dis.dis(code_obj, file=output)
            disassembly = output.getvalue()
            
            return f"# Decompiled from marshal object:\n# {disassembly}\n\n# Original marshaled bytecode\n# (Cannot fully decompile to source without execution)"
            
        except Exception as e:
            print(f"Layer 1 decryption error: {e}", file=sys.stderr)
        
        return None
    
    def detect_layer(self, code: str) -> int:
        """Detect which obfuscation layer is present"""
        
        # Layer 2 indicators: bytes([...]) pattern with lzma
        if re.search(r'bytes\(\[\d+,\s*\d+', code) and ('lzma' in code or 'decompress' in code):
            return 2
        
        # Layer 2 alternative: eval, getattr, __import__ pattern
        if all(x in code for x in ['eval', 'getattr', '__import__']) and re.search(r'bytes\(\[', code):
            return 2
        
        # Layer 1 indicators: codecs.decode, rot13, marshal.loads
        if all(x in code for x in ['codecs.decode', 'marshal.loads', 'base64.b64decode']):
            return 1
        
        return 0
    
    def deobfuscate(self) -> str:
        """Main deobfuscation routine"""
        
        current_code = self.code
        iterations = 0
        max_iterations = 5
        
        print("Starting static deobfuscation...\n")
        
        while iterations < max_iterations:
            iterations += 1
            layer = self.detect_layer(current_code)
            
            print(f"Iteration {iterations}: Detected Layer {layer}")
            
            if layer == 0:
                print("No more obfuscation layers detected.")
                break
            
            if layer == 2:
                result = self.decrypt_layer2(current_code)
                if result:
                    print(f"  ✓ Successfully decrypted Layer 2 (LZMA compression)")
                    current_code = result
                else:
                    print(f"  ✗ Failed to decrypt Layer 2")
                    break
                    
            elif layer == 1:
                result = self.decrypt_layer1(current_code)
                if result:
                    print(f"  ✓ Successfully decrypted Layer 1 (Base64 + ROT13)")
                    current_code = result
                else:
                    print(f"  ✗ Failed to decrypt Layer 1")
                    break
        
        self.deobfuscated = current_code
        return current_code
    
    def save_output(self, output_path: str):
        """Save deobfuscated code to file"""
        if self.deobfuscated:
            with open(output_path, 'w') as f:
                f.write(self.deobfuscated)
            print(f"\n✓ Deobfuscated code saved to: {output_path}")
        else:
            print("\n✗ No deobfuscated code to save. Run deobfuscate() first.")


def analyze_loader_structure(loader_code: str):
    """Analyze the loader.py structure to extract encryption details"""
    
    print("\n=== Loader Analysis ===")
    
    # Extract key and IV placeholders
    key_match = re.search(r'key\s*=\s*base64\.b64decode\("([^"]+)"\)', loader_code)
    iv_match = re.search(r'iv\s*=\s*base64\.b64decode\("([^"]+)"\)', loader_code)
    
    if key_match:
        print(f"Key placeholder: {key_match.group(1)}")
    if iv_match:
        print(f"IV placeholder: {iv_match.group(1)}")
    
    # Extract module name
    module_match = re.search(r'module\s*=\s*"([^"]+)"', loader_code)
    if module_match:
        print(f"Module name: {module_match.group(1)}")
    
    # Extract zip file location
    zipfile_match = re.search(r'zipfile\s*=\s*.*?"([^"]+)"', loader_code)
    if zipfile_match:
        print(f"Encrypted file: {zipfile_match.group(1)}")
    
    print("\nNote: The actual encryption key/IV are embedded during build.")
    print("To decrypt blank.aes, you would need the actual key/IV from a built sample.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Static deobfuscator for BlankOBF obfuscated Python code"
    )
    parser.add_argument(
        "input_file",
        help="Path to the obfuscated Python file"
    )
    parser.add_argument(
        "-o", "--output",
        default="deobfuscated.py",
        help="Output file path (default: deobfuscated.py)"
    )
    parser.add_argument(
        "--analyze-loader",
        action="store_true",
        help="Analyze loader.py structure instead of deobfuscating"
    )
    
    args = parser.parse_args()
    
    # Read input file
    try:
        with open(args.input_file, 'r') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Analyze loader if requested
    if args.analyze_loader:
        analyze_loader_structure(code)
        sys.exit(0)
    
    # Deobfuscate
    deobfuscator = BlankOBFDeobfuscator(code)
    deobfuscated_code = deobfuscator.deobfuscate()
    
    # Save output
    deobfuscator.save_output(args.output)
    
    print("\n" + "="*60)
    print("DEOBFUSCATION COMPLETE")
    print("="*60)
    print(f"\nInput:  {args.input_file}")
    print(f"Output: {args.output}")
    print("\nNote: BlankOBF uses marshal compilation which cannot be")
    print("      fully reversed to original source without execution.")
    print("      The output shows the deobfuscation progress and any")
    print("      readable code extracted from the layers.")


if __name__ == "__main__":
    main()
