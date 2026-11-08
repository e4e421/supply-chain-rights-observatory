#!/usr/bin/env python3
"""Make failed collection visible in GitHub Actions after its status has deployed."""
import json
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'docs/data/latest.json').read_text(encoding='utf-8'))
if data.get('status') == 'failed':
    print('::error::All data sources failed or initial collection yielded no usable data. Check sources and retry.')
    sys.exit(1)
print('Health state:',data.get('status'))
