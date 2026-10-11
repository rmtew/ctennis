"""Atomic bounded diagnostic progress; never an acceptance receipt."""
import gzip
import json
import os
from pathlib import Path

MAX_UNCOMPRESSED=64*1024*1024
MAX_COMPRESSED=16*1024*1024


def write_progress(path,payload):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    count=0
    try:
        with gzip.open(temporary,'wt',encoding='utf-8') as output:
            for chunk in json.JSONEncoder(separators=(',',':')).iterencode(payload):
                count+=len(chunk.encode('utf-8'))
                if count>MAX_UNCOMPRESSED:raise ValueError('Unvalidated progress exceeds uncompressed storage cap')
                output.write(chunk)
        if temporary.stat().st_size>MAX_COMPRESSED:raise ValueError('Unvalidated progress exceeds compressed storage cap')
        os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)
