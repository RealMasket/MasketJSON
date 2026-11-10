"""Audit every recorded file and evaluate unchanged per-compiler resource gates."""
import csv,json,math,statistics,sys
from pathlib import Path
from common import POLICIES,sha,validate_memory,validate_journal
root,report=map(Path,sys.argv[1:]);m=json.loads((root/'metadata.json').read_text());f=json.loads((root/'freeze.json').read_text());corpus=json.loads((root/'corpus.json').read_text());plan=json.loads((root/'plan.json').read_text())
assert sha(root/'freeze.json')==m['freeze_sha256']
assert sha(root/'corpus.json')==m['corpus_sha256']==f['corpus_sha256']
assert sha(root/'plan.json')==m['plan_sha256']==f['plan_sha256']
for rel,h in m['files'].items():assert sha(root/rel)==h,rel
for e in f['sources']:assert sha(root/'sources'/(e['sha256']+'.txt'))==e['sha256']
assert (m['rounds'],m['samples'],m['iterations'])==(8,5,3)
names=[e['name'] for e in corpus['entries']];expected={e['name']:e['bytes'] for e in corpus['entries']};assert len(names)==5
pairs=[(c,p) for p in POLICIES for c in ('msvc','clang')]
for i,order in enumerate(m['round_order']):assert order==[list(x) for x in pairs[i:]+pairs[:i]]
data={}
for c in ('msvc','clang'):
    d=root/c;memory={p:validate_memory((d/f'{p}-memory.csv').read_text(),expected) for p in POLICIES};times={}
    for p in POLICIES:
        for i in range(1,9):
            rows=list(csv.DictReader((d/f'{p}-{i}.csv').open(newline='')))
            assert len(rows)==10 and {(r['dataset'],r['operation']) for r in rows}=={(n,o) for n in names for o in ('parse','lex_only')}
            for r in rows:
                assert r['configuration']=='Release' and int(r['bytes'])==expected[r['dataset']]
                assert int(r['samples'])==5 and int(r['iterations'])==3
                assert 0<float(r['min_us'])<=float(r['median_us'])<=float(r['max_us'])
                times.setdefault((p,r['dataset'],r['operation']),[]).append(float(r['median_us']))
    for goal in ('speed','memory'):
        rows=validate_journal((d/f'{goal}-decisions.csv').read_text(),goal,names)
        for n in names:
            last=next(r for r in reversed(rows) if r['dataset']==n and r['stage']=='lex_only');mrow=memory['v3-'+goal][n,'lex_only']
            assert last['tokens']==mrow['token_count'] and last['actual_capacity']==mrow['token_capacity']
            assert int(last['moved_tokens'])*int(mrow['token_size'])==int(mrow['copied_token_bytes'])
    data[c]=dict(memory=memory,times=times)
assert (root/'msvc/shapes.csv').read_bytes()==(root/'clang/shapes.csv').read_bytes()
def t(c,p,n,o='parse'):return statistics.median(data[c]['times'][p,n,o])
def peak(c,p,n):return int(data[c]['memory'][p][n,'whole_parse']['peak_live_bytes'])
def gm(xs):return math.exp(statistics.mean(math.log(x) for x in xs))
lines=['# Frozen Auto v3 on external JSON snapshots and two compilers','','## Scope and frozen protocol','',
    'This evaluates the selected private Auto v3 from `838a26e`; no controller, pressure threshold, budget or coefficient is tuned using these files.',
    'Five immutable public snapshots cover numeric geometry, an indented event catalog, historical CJK social text, country attributes/geometry and a dependency lockfile.',
    'These are external transfer examples, not a random or representative sample of user workloads. The native benchmark snapshots are historical.',
    'Original bytes are used without minification, content editing or synthetic repetition. Raw upstream JSON is downloaded into ignored output and is not redistributed here.',
    '', '| Snapshot | Original bytes | Upstream revision | SHA-256 |', '| --- | ---: | --- | --- |']
for e in corpus['entries']:
    url=f"https://github.com/{e['repo']}/blob/{e['commit']}/{e['path']}"
    lines.append(f"| [{e['name']}]({url}) | {e['bytes']} | `{e['commit'][:12]}` | `{e['sha256']}` |")
lines += ['',f"Compiler builds, sources and corpus were frozen at `{f['frozen_utc']}`; source revision `{f['source_revision']}`.",
    'Source snapshots are content-addressed and checked against the freeze; all timing/profile files have recorded hashes.',
    'Upstream source context: [Native JSON Benchmark data](https://github.com/miloyip/nativejson-benchmark#json-data),',
    '[Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/), [TypeScript](https://github.com/microsoft/TypeScript).',
    'MasketJSON does not claim that its MIT license relicenses upstream datasets.',
    '', '## Comparable builds and measurements','',f"Machine: {m['cpu']}; {m['os']}; logical CPU {m['logical_cpu']}.",
    'Both compilers target Windows x64 with Microsoft STL 14.51.36231 and Release CRT /MD. MSVC link.exe 14.51 links both builds.',
    'Clang uses its normal resource wrappers around the same Microsoft STL headers. This isolates a compiler change while holding OS, STL and runtime allocator constant;',
    'it does not measure Linux, libc++, libstdc++ or another allocator. The allocator used by the Clang compiler process is unrelated to measured applications.',
    '', '| Build | Compiler version | Global flags | Release flags |', '| --- | --- | --- | --- |']
for c,info in f['compilers'].items():lines.append(f"| {c} | {info['build_info']['compiler']} {info['build_info']['compiler_version']} | `{info['cache']['CMAKE_CXX_FLAGS']}` | `{info['cache']['CMAKE_CXX_FLAGS_RELEASE']}` |")
lines += ['', 'C++17, static library, no LTO or fast-math. Eight compiler/preset pairs rotate over eight rounds: each occupies each absolute position once.',
    'Within each compiler every preset occupies each position twice. Each measurement has 5 samples x 3 operations plus 5 warm-ups.',
    'Tables use medians of eight round medians. Loading, shape checks and semantic validation are outside timing; parse includes result destruction.',
    'Ordinary timing builds have no allocation interception or journal hooks. Profiles and traces run separately.',
    'Captured peak counts simultaneous requested C++ new bytes, including old/new token-buffer overlap; it excludes caller input, stack/root Json, allocator rounding/metadata,',
    'direct malloc/CRT internals and profiler bookkeeping. It is not RSS. Copied MiB are logical live-token relocations, not retained heap.',
    '', 'All five files pass every token/value/diagnostic comparison against both fixed parsers in both toolchains.',
    'Canonical value/shape fingerprints also match across compilers. Journal token count, final capacity and moved bytes match independent allocation profiles.',
    '', '## Unchanged empirical gates','',
    'Per compiler, gates apply when its Balanced median parse is >=1 ms; every smaller file remains in all tables.',
    '', '- Speed: time/better fixed mode <=1.5, peak/better fixed mode <=2, peak/Balanced <=1.5.',
    '- Memory: time/Balanced <=2 and peak/better fixed mode <=1.5.',
    '', 'The offline oracle is the better fixed mode per document and metric. These local criteria are not runtime guarantees.',
    '', '| Compiler / goal | GM time/Balanced, all | Worst time/oracle | Worst time/Balanced | Worst peak/oracle | Worst peak/Balanced | Joint result |',
    '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
gates={};worst=[]
for c in data:
    non=[n for n in names if t(c,'balanced',n)>=1000];assert non
    for goal in ('speed','memory'):
        p='v3-'+goal
        ratios={
            'time/oracle':lambda n:t(c,p,n)/min(t(c,'balanced',n),t(c,'low-memory',n)),
            'time/Balanced':lambda n:t(c,p,n)/t(c,'balanced',n),
            'peak/oracle':lambda n:peak(c,p,n)/min(peak(c,'balanced',n),peak(c,'low-memory',n)),
            'peak/Balanced':lambda n:peak(c,p,n)/peak(c,'balanced',n)}
        values={k:max(fn(n) for n in non) for k,fn in ratios.items()}
        passed=values['time/oracle']<=1.5 and values['peak/oracle']<=2 and values['peak/Balanced']<=1.5 if goal=='speed' else values['time/Balanced']<=2 and values['peak/oracle']<=1.5
        gates[c,goal]=passed
        lines.append(f"| {c}/{goal} | {gm([t(c,p,n)/t(c,'balanced',n) for n in names]):.3f} | {values['time/oracle']:.3f} | {values['time/Balanced']:.3f} | {values['peak/oracle']:.3f} | {values['peak/Balanced']:.3f} | {'PASS' if passed else 'FAIL'} |")
        for metric,fn in ratios.items():
            n=max(non,key=fn);worst.append(f"- {c}/{goal}, worst {metric}: {n}, {fn(n):.3f}.")
lines += ['',*worst,'', 'A failed external gate remains a failure. No presets, coefficients, inputs or acceptance rules were adjusted in response.',
    'Passing these five snapshots would still not establish reliable automatic selection for arbitrary applications; Auto remains private.',
    '', '## Full per-input results','', '| Compiler / input / preset | Parse ms | Lexer ms | Whole-parse peak MiB | Copied MiB | Token count | Final token capacity |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
for n in names:
    for c in data:
        for p in POLICIES:
            r=data[c]['memory'][p][n,'lex_only']
            lines.append(f"| {c} / {n} / {p} | {t(c,p,n)/1000:.4f} | {t(c,p,n,'lex_only')/1000:.4f} | {peak(c,p,n)/1048576:.3f} | {int(r['copied_token_bytes'])/1048576:.3f} | {r['token_count']} | {r['token_capacity']} |")
lines += ['', '## Compiler transfer','', 'Clang/MSVC parse-time ratio below 1 means faster Clang for the same preset/input on this run.',
    'Use these paired local results rather than interpreting the compiler as a universally faster choice.',
    '', '| Input | Balanced | V3 speed | LowMemory | V3 memory |','| --- | ---: | ---: | ---: | ---: |']
for n in names:lines.append('| '+n+' | '+' | '.join(f"{t('clang',p,n)/t('msvc',p,n):.3f}" for p in POLICIES)+' |')
lines.append('| Geometric mean | '+' | '.join(f"{gm([t('clang',p,n)/t('msvc',p,n) for n in names]):.3f}" for p in POLICIES)+' |')
lines += ['', '## Reproduction and limits','',
    'Raw [freeze, upstream manifest, eight timing rounds, profiles, journals and source snapshots](real-corpus-windows/) accompany the report.',
    'Use [the real-corpus instructions](../real-corpus/README.md). Regenerate with `python benchmarks/real-corpus/summarize.py benchmarks/results/real-corpus-windows REPORT.md`.',
    'No noisy performance threshold runs in CI. Windows/Linux CI repeats exact results and journal/profile invariants on the original external files.',
    'CPU frequency, thermal state, code layout and background load can still affect measurements. This is one machine and a small convenience sample,',
    'with no pretense that the historical external corpus covers users actual file distributions. Representative opt-in workload data remains the next evidence needed.','']
report.parent.mkdir(parents=True,exist_ok=True);report.write_bytes(('\n'.join(lines)).encode());print(json.dumps({c+'/'+g:v for (c,g),v in gates.items()},indent=2))
