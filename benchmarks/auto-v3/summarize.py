"""Audit calibration/freeze/final stages and evaluate unchanged joint targets."""
import csv,hashlib,json,math,statistics,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reservation'))
from check_matrix import validate_memory
from journal import validate
root,report=map(Path,sys.argv[1:]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selection=json.loads((root/'selection.json').read_text());freeze=json.loads((root/'freeze.json').read_text())
plan_path=Path(__file__).with_name('selection-plan.json');plan=json.loads(plan_path.read_text())
assert selection['plan_sha256']==sha(plan_path) and plan['original_plan_sha256']==sha(plan_path.with_name('plan.json'))
for label,h in plan['phase1_metadata'].items():assert sha(root/'calibration'/label/'metadata.json')==h
assert freeze['selection_sha256']==sha(root/'selection.json') and freeze['known_metadata_sha256']==sha(root/'known/metadata.json')
for label,h in selection['calibration_metadata'].items():assert sha(root/'calibration'/label/'metadata.json')==h
data={}
for stage,count in (('known',91),('holdout',16)):
    d=root/stage;m=json.loads((d/'metadata.json').read_text());assert m['stage']==stage and m['rounds']==6
    assert m['selection_sha256']==freeze['selection_sha256'] and m['binaries']==freeze['binaries']
    if stage=='holdout':assert m['freeze_sha256']==sha(root/'freeze.json')
    inputs={i['name']:i['bytes'] for i in m['inputs']};assert len(inputs)==len(m['inputs'])==count
    memory={p:validate_memory((d/f'{p}-memory.csv').read_text(),inputs) for p in m['policies']};times={}
    for i in range(6):
        assert m['round_order'][i]==m['policies'][i:]+m['policies'][:i]
        for p in m['policies']:
            rows=list(csv.DictReader((d/f'{p}-{i+1}.csv').open(newline='')));seen=set()
            for row in rows:
                key=row['dataset'],row['operation'];assert key not in seen;seen.add(key)
                assert row['configuration']=='Release' and int(row['bytes'])==inputs[key[0]]
                assert int(row['samples'])==m['samples'] and int(row['iterations'])==m['iterations']
                assert 0<float(row['min_us'])<=float(row['median_us'])<=float(row['max_us'])
                times.setdefault((p,*key),[]).append(float(row['median_us']))
            assert seen=={(n,o) for n in inputs for o in ('parse','lex_only')}
    journals={}
    for goal in ('speed','memory'):
        rows=validate((d/f'{goal}-decisions.csv').read_text(),goal,inputs);journals[goal]=rows
        for n in inputs:
            last=next(r for r in reversed(rows) if r['dataset']==n and r['stage']=='lex_only');mem=memory['v3-'+goal][n,'lex_only']
            assert int(last['moved_tokens'])*int(mem['token_size'])==int(mem['copied_token_bytes'])
            assert last['tokens']==mem['token_count'] and last['actual_capacity']==mem['token_capacity']
            assert int(last['budget_bytes'])==selection['chosen'][goal]['budget_bytes']
            assert all(int(r['pressure_floor_quarters'])==selection['chosen'][goal]['quarters'] for r in rows if r['dataset']==n and int(r['pressure_floor_quarters']))
    data[stage]=dict(meta=m,inputs=inputs,memory=memory,times=times,journals=journals)
def t(s,p,n):return statistics.median(data[s]['times'][p,n,'parse'])
def peak(s,p,n):return int(data[s]['memory'][p][n,'whole_parse']['peak_live_bytes'])
def ot(s,n):return min(t(s,'balanced',n),t(s,'low-memory',n))
def op(s,n):return min(peak(s,'balanced',n),peak(s,'low-memory',n))
def gm(v):return math.exp(statistics.mean(math.log(x) for x in v))

lines=['# Auto v3: growth under copy pressure','','## Hypothesis and fixed experiment','',
    'The dense-input diagnosis found expensive allocation schedules without JSON scanning or density prediction.',
    'Phase 1 changes only the geometric floor when the existing copy-pressure predicate is active. Density thresholds, pressure thresholds,',
    '4 MiB speed / 1 MiB memory speculative-byte budgets and remaining-byte final-capacity proof are unchanged.',
    'Candidates use floor(capacity * 1.5), floor(capacity * 1.75) or capacity * 2 under pressure; checked arithmetic saturates at max_size.',
    'Without pressure, the ordinary speed 1.5 / memory 1.25 minimum remains. Larger floors can exceed the soft byte ceiling, and every exception is logged.',
    'A proved final-capacity reservation may bypass the geometric floor because all remaining tokens fit, requiring no subsequent expansion.',
    '', 'The [original plan](../auto-v3/plan.json), controllers and tooling were committed before measurements at `f4b9f04`.',
    'Phase 1 showed zero speed pressure activations on dense-zeros-262144: increasing a pressure floor cannot change that schedule.',
    'A [second pre-recorded plan](../auto-v3/selection-plan.json), committed at `f6604dc` before further measurement, adds projected pressure.',
    'Projected pressure includes the inevitable relocation at the pending expansion. Integer comparisons cancel that n-token term:',
    'speed uses moved > floor(n/2), memory moved > 2*n; no overflowing sum is formed. The historical predicate remains a control.',
    'Both predicates are crossed with all three floors. Selection uses all six known-data candidates under the original joint gates.',
    'All 91 previous synthetic inputs, including previous evaluation splits, are calibration data now. No old holdout is reused as an independent test.',
    'The 1.5 control reproduces all 91 v2 heap/profile rows exactly for both goals and both production modes.',
    'One exploratory round of 3 samples x 2 operations selects each goal using all joint CPU/heap gates first, geometric mean time second,',
    'and lowest worst peak/oracle for candidates within 3% of the fastest. If no candidate passes, minimum normalized gate violation is explicitly unqualified.',
    '', '| Candidate / goal | Pressure floor | Lookahead | GM time/Balanced | Worst time/oracle | Worst time/Balanced | Worst peak/oracle | Worst peak/Balanced | Joint eligible |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
for key,score in selection['scores'].items():
    lines.append(f"| {key} | {score['quarters']/4:g} | {score['lookahead']} | {score['geomean_time_balanced']:.3f} | {score['worst_time_oracle']:.3f} | {score['worst_time_balanced']:.3f} | {score['worst_peak_oracle']:.3f} | {score['worst_peak_balanced']:.3f} | {score['joint_eligible']} |")
lines += ['',f"Selected speed pressure floor: {selection['chosen']['speed']['quarters']/4:g}; memory: {selection['chosen']['memory']['quarters']/4:g}. Lookahead speed/memory: {selection['chosen']['speed']['lookahead']}/{selection['chosen']['memory']['lookahead']}.",
    f"Policy sources, all comparison executables and the selected parameters were frozen at `{freeze['frozen_utc']}` after repeated known-set measurements.",
    'Only then were 16 full new inputs generated with seed 20261110 and counts 197/4093: buried trailing padding, escaped/UTF-8 values,',
    'late records, mixed-width floats, ragged objects, whitespace islands, leading padding and irregular stepped string/number regions.',
    'No thresholds, budgets or coefficients were changed using that new evaluation.',
    '', '## Measurement and unchanged gates','',
    f"Machine: {data['known']['meta']['cpu']}; {data['known']['meta']['os']}; {data['known']['meta']['configuration']}.",
    'Logical CPU 0; six cyclic rounds with every mode in every position once. Each round uses 5 samples x 3 operations and 5 warm-ups.',
    'Tables show medians of round medians. Loading and exact checks are outside timing; result construction/destruction is included.',
    'Timing uses ordinary builds without journals or allocation interception. Profile/trace builds run separately.',
    'Captured heap peak counts simultaneous requested bytes from intercepted C++ new calls, including overlapping token buffers.',
    'Caller input, stack/root Json, allocator rounding/metadata, direct malloc/CRT allocations and profiler bookkeeping are excluded; this is not RSS.',
    'Copied bytes are logical live-token relocations, not retained memory. Recorded retained DOM accounting is identical across all six modes.',
    '', 'Pre-registered gates apply on Balanced parse >=1 ms; every smaller input is still reported:',
    '', '- Speed: time/better fixed mode <=1.5, peak/better fixed mode <=2, peak/Balanced <=1.5.',
    '- Memory: time/Balanced <=2, peak/better fixed mode <=1.5.',
    'The better fixed mode (offline oracle) is chosen per document and metric. These are local empirical criteria, not runtime guarantees.',
    '', '| Split / mode | GM time/Balanced, all | Worst time/oracle | Worst time/Balanced | Worst peak/oracle | Worst peak/Balanced | Joint result |',
    '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
gates={};worst=[]
for stage in data:
    names=list(data[stage]['inputs']);non=[n for n in names if t(stage,'balanced',n)>=1000];assert non
    for mode in ('v2-speed','v3-speed','v2-memory','v3-memory'):
        wt=max(t(stage,mode,n)/ot(stage,n) for n in non);wb=max(t(stage,mode,n)/t(stage,'balanced',n) for n in non)
        wp=max(peak(stage,mode,n)/op(stage,n) for n in non);pb=max(peak(stage,mode,n)/peak(stage,'balanced',n) for n in non)
        passed=wt<=1.5 and wp<=2 and pb<=1.5 if mode.endswith('speed') else wb<=2 and wp<=1.5
        gates[stage,mode]=passed
        lines.append(f"| {stage}/{mode} | {gm([t(stage,mode,n)/t(stage,'balanced',n) for n in names]):.3f} | {wt:.3f} | {wb:.3f} | {wp:.3f} | {pb:.3f} | {'PASS' if passed else 'FAIL'} |")
        if mode.startswith('v3-'):
            for metric,f in [('time/oracle',lambda n:t(stage,mode,n)/ot(stage,n)),('time/Balanced',lambda n:t(stage,mode,n)/t(stage,'balanced',n)),('peak/oracle',lambda n:peak(stage,mode,n)/op(stage,n)),('peak/Balanced',lambda n:peak(stage,mode,n)/peak(stage,'balanced',n))]:
                n=max(non,key=f);worst.append(f"- {stage}/{mode}, worst {metric}: {n}, {f(n):.3f}.")
lines += ['', 'Worst-case input names:', '',*worst,'',
    'These results preserve the original thresholds, including failed rows. Passing both splits is evidence for these inputs and this machine,',
    'not proof of general automatic selection. V3 remains a private experiment; public Balanced/LowMemory and Json layout are unchanged.',
    '', '## Dense and sparse-tail regressions','',
    '| Known input / mode | Parse ms | Lexer ms | Copied MiB | Whole-parse peak MiB | Final token buffer MiB |',
    '| --- | ---: | ---: | ---: | ---: | ---: |']
for n in ('dense-zeros-262144.json','alternating-262144.json','held-tail-records-4099.json','dense-zeros-32768.json'):
    for mode in ('balanced','low-memory','v2-speed','v3-speed','v2-memory','v3-memory'):
        r=data['known']['memory'][mode][n,'lex_only'];lex=statistics.median(data['known']['times'][mode,n,'lex_only'])
        lines.append(f"| {n} / {mode} | {t('known',mode,n)/1000:.3f} | {lex/1000:.3f} | {int(r['copied_token_bytes'])/1048576:.3f} | {peak('known',mode,n)/1048576:.3f} | {int(r['token_capacity'])*int(r['token_size'])/1048576:.3f} |")
for title,fn in [('Full parse time, ms',lambda s,p,n:f'{t(s,p,n)/1000:.4f}'),('Full captured heap peak, MiB',lambda s,p,n:f'{peak(s,p,n)/1048576:.3f}')]:
    lines += ['', '## '+title, '', '| Split / input | Balanced | LowMemory | V2 speed | V3 speed | V2 memory | V3 memory |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in data:
        for n in data[s]['inputs']:lines.append('| '+s+' / '+n+' | '+' | '.join(fn(s,p,n) for p in ('balanced','low-memory','v2-speed','v3-speed','v2-memory','v3-memory'))+' |')
lines += ['', '## Growth decisions and correctness','',
    '| Split / goal | Expansions | Pressure active | Pressure raised floor | Byte floor overrides | Proven final capacity |',
    '| --- | ---: | ---: | ---: | ---: | ---: |']
for s in data:
    for goal,rows in data[s]['journals'].items():
        g=[r for r in rows if r['stage']=='lex_only' and r['reason'] not in ('initial','finished','aborted','allocation_failed')]
        lines.append(f"| {s}/{goal} | {len(g)} | {sum(r['pressure_active']=='1' for r in g)} | {sum(r['pressure_raised_floor']=='1' for r in g)} | {sum(r['floor_override']=='1' for r in g)} | {sum(r['tail_applied']=='1' for r in g)} |")
lines += ['', 'Exact comparators check every token field, canonical integer/double/negative-zero representation, results and full error diagnostics against both production modes.',
    'Independent journal checks recompute the pressure floor, verify unchanged ordinary floors, justify each byte exception and reject growth after a proved final-capacity reserve.',
    'Token count/capacity/movement matches allocation profiles; retained categories partition memory and all tracked live bytes/blocks return to zero.',
    'Arithmetic tests cover rational rounding, tiny capacities, saturation near size_t/max_size and near-EOF final capacity. Corpus replay and coverage fuzzers compare independent production parsing.',
    '', 'CPU frequency, code layout, allocator state and background load can affect times. Full sample spread, six rounds, hashes and frozen artifact identities are retained.',
    'The 107 known/new synthetic documents are not representative user workloads; future promotion also needs real workload and other-toolchain measurements.',
    '', 'Raw [calibration, selection, freeze, measurements and journals](auto-v3-msvc1951/) accompany [reproduction instructions](../README.md#auto-v3-growth-under-copy-pressure).',
    'Regenerate with `python benchmarks/auto-v3/summarize.py benchmarks/results/auto-v3-msvc1951 REPORT.md`.','']
report.parent.mkdir(parents=True,exist_ok=True);report.write_bytes(('\n'.join(lines)).encode())
print(json.dumps({f'{s}/{m}':v for (s,m),v in gates.items()},indent=2))
