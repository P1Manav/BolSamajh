import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bolsamajh.benchmark.sentences import SENTENCES

for s in SENTENCES:
    r = s.reference_roman
    d = s.reference_devanagari
    
    # Check AM/PM vs baje
    if ("PM" in r or "AM" in r) and "बजे" in d:
        print(f"[{s.id}] AM/PM vs baje: Roman='{r}' vs Deva='{d}'")
    if "ms" in r and "मिलीसेकंड" in d:
        print(f"[{s.id}] Unit mismatch: Roman='{r}' vs Deva='{d}'")
    
    # Check English numbers spelled out vs digits
    # Check for words in Roman that don't match Devanagari
    r_words = r.replace(".", "").replace(",", "").replace("?", "").replace("!", "").split()
    d_words = d.replace("।", "").replace(",", "").replace("?", "").replace("!", "").split()
    if abs(len(r_words) - len(d_words)) >= 2:
        print(f"[{s.id}] Length discrepancy: len(R)={len(r_words)}, len(D)={len(d_words)}")
        print(f"    R: {r}")
        print(f"    D: {d}")
