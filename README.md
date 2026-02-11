# BlankOBF Static Deobfuscator

A static analysis tool for deobfuscating Python code obfuscated with BlankOBF. This tool **does not execute** any code and is safe to use on potentially malicious samples.

## Features

- ✅ **100% Static Analysis** - Never executes obfuscated code
- ✅ **Layer Detection** - Automatically detects obfuscation layers
- ✅ **Multi-Layer Decryption** - Handles multiple obfuscation layers
- ✅ **Loader Analysis** - Analyzes the loader structure
- ✅ **Safe** - No code execution, no risk

## Obfuscation Layers Supported

### Layer 1: Base64 + ROT13 + Marshal
- Variables split into 4 parts (rot13, normal, reversed, normal)
- Base64 encoded
- Marshal compiled bytecode

### Layer 2: LZMA Compression + Encrypted Strings
- LZMA compressed payload
- Encrypted string literals using base64
- Dynamic imports via `getattr` and `eval`

## Installation

```bash
# No external dependencies needed for basic deobfuscation
# Python 3.6+ with standard library

# For advanced features, install:
pip install pyaes  # Only if analyzing encrypted .aes files
```

## Usage

### Basic Deobfuscation

```bash
python deobfuscator.py obfuscated.py -o deobfuscated.py
```

### Analyze Loader Structure

```bash
python deobfuscator.py loader.py --analyze-loader
```

### Example Output

```
Starting static deobfuscation...

Iteration 1: Detected Layer 2
  ✓ Successfully decrypted Layer 2 (LZMA compression)
Iteration 2: Detected Layer 1
  ✓ Successfully decrypted Layer 1 (Base64 + ROT13)
Iteration 3: Detected Layer 0
No more obfuscation layers detected.

✓ Deobfuscated code saved to: deobfuscated.py
```

## Command Line Options

```
positional arguments:
  input_file            Path to the obfuscated Python file

optional arguments:
  -h, --help            Show this help message
  -o OUTPUT, --output OUTPUT
                        Output file path (default: deobfuscated.py)
  --analyze-loader      Analyze loader.py structure instead of deobfuscating
```

## Technical Details

### BlankOBF Obfuscation Scheme

1. **Original Code** → Marshal compilation
2. **Layer 1**: 
   - Base64 encode
   - Split into 4 parts
   - Apply ROT13 to part 1
   - Reverse part 3
   - Shuffle variable assignments

3. **Layer 2**:
   - LZMA compress the Layer 1 code
   - Encrypt string literals
   - Use dynamic imports via `getattr(__import__(...))`

4. **Layer 3** (Optional):
   - Additional LZMA + Base64
   - Usually disabled due to detection concerns

### Full Build Pipeline

The malware builder does the following:

```
stub.py → BlankOBF → stub-o.py → junk code → stub-o.pyc → 
blank.aes (AES-GCM encrypted) → loader-o.py → PyInstaller → Built.exe
```

Post-processing:
- Remove PyInstaller metadata
- Add fake certificate (stolen from system .exe)
- Pump file size
- Rename entry point

### Limitations

⚠️ **Marshal Bytecode**: Layer 1 produces marshal-compiled bytecode which cannot be fully decompiled to original Python source without execution. The deobfuscator provides:
- Disassembly of bytecode
- Extracted string literals where possible
- Structural analysis

⚠️ **AES Encryption**: The final `blank.aes` file is encrypted with AES-GCM. The key/IV are randomly generated during build and embedded in the loader. To decrypt:
1. Extract the key/IV from a built `loader-o.py` file
2. Reverse the operations manually:
   - Reverse bytes (payload is stored reversed)
   - ZLIB decompress
   - AES-GCM decrypt
   - Unzip to get `stub-o.pyc`

## Examples

### Example 1: Deobfuscate a Layer 2 Sample

```python
# Input (obfuscated):
___ = eval(getattr(__import__(bytes([98,117,105,108,116,105,110,115]).decode()), 
           bytes([101,118,97,108]).decode()))
# ... encrypted code ...

# Output (deobfuscated):
# Shows the underlying Layer 1 code
```

### Example 2: Analyze Loader

```bash
$ python deobfuscator.py loader.py --analyze-loader

=== Loader Analysis ===
Key placeholder: %key%
IV placeholder: %iv%
Module name: stub-o
Encrypted file: blank.aes

Note: The actual encryption key/IV are embedded during build.
```

## Safety Notes

This tool is designed for malware analysis and does NOT:
- Execute any code from obfuscated files
- Import obfuscated modules
- Eval/exec any user-controlled strings
- Make network connections
- Write to unexpected locations

All operations are pure static analysis using:
- Regular expressions
- AST parsing (literal_eval only)
- Standard library decompression (lzma, base64, zlib)
- Marshal loading (safe, doesn't execute)

## Understanding the Output

Due to marshal compilation, you may see output like:

```python
# Decompiled from marshal object:
# (Bytecode disassembly showing opcodes and constants)
# Original marshaled bytecode
# (Cannot fully decompile to source without execution)
```

This is expected. To get the original source, you would need a full Python bytecode decompiler like `uncompyle6`, but be aware that:
1. This requires executing the unmarshal operation (higher risk)
2. Decompilation may not be perfect
3. The original may have been further obfuscated before marshaling

## Advanced: Manual AES Decryption

If you have a built sample and need to decrypt `blank.aes`:

```python
import base64, zlib
from pyaes import AESModeOfOperationGCM

# Extract these from loader-o.py in the built sample
key = base64.b64decode("...actual key from built file...")
iv = base64.b64decode("...actual IV from built file...")

# Read encrypted file
with open("blank.aes", "rb") as f:
    encrypted = f.read()

# Reverse operations in order
encrypted = encrypted[::-1]  # Un-reverse
decompressed = zlib.decompress(encrypted)  # Un-compress
decrypted = AESModeOfOperationGCM(key, iv).decrypt(decompressed)

# Save decrypted zip
with open("blank.zip", "wb") as f:
    f.write(decrypted)

# Extract stub-o.pyc from zip
# Then decompile with uncompyle6 or similar
```

## Contributing

This is a defensive tool for malware analysis. Use responsibly and only on samples you have permission to analyze.

## License

MIT License - Use for educational and defensive security purposes only.

## Disclaimer

This tool is provided for malware analysis and cybersecurity research purposes only. 
Do not use for illegal purposes. The authors are not responsible for misuse.
