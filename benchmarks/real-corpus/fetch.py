"""Retrieve immutable upstream JSON bytes; never replace a mismatching local file."""
import argparse,hashlib,json,time,urllib.request
from pathlib import Path
MANIFEST=Path(__file__).with_name('corpus.json')
def digest(data):return hashlib.sha256(data).hexdigest()
def validate(data,e):
    assert len(data)==e['bytes'] and digest(data)==e['sha256'],e['name']
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==e['git_blob_sha1']
    json.loads(data.decode('utf-8'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def verify(directory):
    m=json.loads(MANIFEST.read_text());inputs=[]
    for e in m['entries']:
        f=directory/e['name'];validate(f.read_bytes(),e);inputs.append(f)
    return m,inputs
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();a.directory.mkdir(parents=True,exist_ok=True)
    for e in json.loads(MANIFEST.read_text())['entries']:
        f=a.directory/e['name']
        if f.exists():validate(f.read_bytes(),e);continue
        for attempt in range(3):
            try:
                with urllib.request.urlopen(e['url'],timeout=90) as response:data=response.read(e['bytes']+1)
                validate(data,e);break
            except Exception:
                if attempt==2:raise
                time.sleep(1+attempt)
        f.write_bytes(data)
    verify(a.directory);print('Five original upstream snapshots passed byte count, Git blob and SHA-256 checks')
