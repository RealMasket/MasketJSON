"""Eight cyclic rounds over all compiler/policy pairs, with frozen identities."""
import argparse,csv,io,json,platform,sys
from pathlib import Path
from common import POLICIES,tools,sha,normalized,observe,run as run_cpp
from fetch import verify,MANIFEST
from run_matrix import pin,cpu_name
p=argparse.ArgumentParser();p.add_argument('--bin',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
repo=Path(__file__).resolve().parents[2];frozen_path=a.bin/'freeze.json';frozen=json.loads(frozen_path.read_text());plan_path=Path(__file__).with_name('plan.json');plan=json.loads(plan_path.read_text())
assert sha(MANIFEST)==frozen['corpus_sha256'] and sha(plan_path)==frozen['plan_sha256']
for e in frozen['sources']:assert normalized(repo/e['file'])==e['sha256'],e['file']
for compiler,programs in frozen['binaries'].items():
    for name,h in programs.items():assert sha(a.bin/compiler/name)==h
manifest,inputs=verify(a.inputs);a.output.mkdir(parents=True);restore=pin(plan['cpu'])
try:
    reference=None
    for compiler in ('msvc','clang'):
        shape=observe(a.bin/compiler,a.bin/compiler,inputs,a.output/compiler)
        if reference is None:reference=shape
        else:assert shape==reference,'Cross-compiler value/shape fingerprints differ'
    pairs=[(c,p) for p in POLICIES for c in ('msvc','clang')];orders=[]
    for index in range(plan['rounds']):
        order=pairs[index:]+pairs[:index];orders.append(order)
        for compiler,policy in order:
            text=run_cpp(tools(a.bin/compiler,policy)['Time'],plan['iterations'],plan['samples'],*inputs)
            rows=list(csv.DictReader(io.StringIO(text)));assert len(rows)==len(inputs)*2
            assert {(r['dataset'],r['operation']) for r in rows}=={(f.name,o) for f in inputs for o in ('parse','lex_only')}
            for r in rows:
                assert r['configuration']=='Release' and int(r['iterations'])==plan['iterations'] and int(r['samples'])==plan['samples']
                assert 0<float(r['min_us'])<=float(r['median_us'])<=float(r['max_us'])
            (a.output/compiler/f'{policy}-{index+1}.csv').write_bytes(text.encode())
            print(f'round {index+1}/{plan["rounds"]}: {compiler}/{policy}',flush=True)
    files={f.relative_to(a.output).as_posix():sha(f) for f in sorted(a.output.rglob('*')) if f.is_file()}
    meta=dict(freeze_sha256=sha(frozen_path),corpus_sha256=sha(MANIFEST),plan_sha256=sha(plan_path),cpu=cpu_name(),os=platform.platform(),logical_cpu=plan['cpu'],rounds=plan['rounds'],samples=plan['samples'],iterations=plan['iterations'],round_order=orders,files=files,inputs=manifest['entries'])
    (a.output/'metadata.json').write_bytes((json.dumps(meta,indent=2)+'\n').encode())
finally:restore()
