import gzip
import json


def decompress_items(data):
    if not isinstance(data, bytes):
        return data
    return json.loads(gzip.decompress(data).decode("utf-8"))

def compress_item(data: dict):
    return gzip.compress(json.dumps(data).encode("utf-8"))