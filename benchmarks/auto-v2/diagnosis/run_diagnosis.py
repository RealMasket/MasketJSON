"""Known-input diagnosis using frozen parsers plus isolated vector schedule replay."""
import argparse,csv,hashlib,io,json,platform,statistics,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'reservation'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from check_matrix import executable,run,validate_memory
from run_matrix import pin,cpu_name,sha
from check_journal import validate

POLICIES=('balanced','v1-speed','v2-speed','low-memory','v1-memory','v2-memory')
NAMES=tuple(f'{kind}-{n}.json' for kind in ('dense-zeros','alternating') for n in (4096,32768,262144))+('held-tail-records-4099.json','whitespace-interleaved-16384.json')

def rows(path):return list(csv.DictReader(path.open(newline='',encoding='utf-8')))
def median(root,policy,name,operation):
    return statistics.median(float(r['median_us']) for i in range(1,7) for r in rows(root/f'{policy}-{i}.csv') if r['dataset']==name and r['operation']==operation)
def render(root,destination):
    m=json.loads((root/'metadata.json').read_text());old=Path(__file__).resolve().parents[2]/'results/auto-v2-msvc1951/known'
    for rel,h in m['files'].items():assert sha(root/rel)==h,rel
    lines=['# Auto v2: dense-input diagnosis','','## Scope and method','',
        'This is a follow-up on eight already known synthetic inputs, not an independent evaluation or a retuned Auto policy.',
        'Production code and the frozen v1/v2 controllers are unchanged. Six cyclic rounds compare the original frozen executables.',
        f"Measured on {m['cpu']}, {m['os']}; {m['configuration']}; pinned to logical CPU 0.",
        'Each sample contains 3 operations; 5 samples per round, plus 5 warm-ups. Reported times are medians of six round medians.',
        'Parser/lexer time includes allocation and destruction; allocation profiles and journals are separate untimed runs.',
        '', 'The isolated replay appends the same number of 48-byte Token objects to std::vector and follows the exact v2 allocation schedule.',
        'It performs no JSON scan, source copy, density prediction, token conversion or DOM construction. Every observed growth and copied-token count must match the journal/profile.',
        'The exact-known-count control reserves all tokens once before appending; knowing this count for free is an offline experiment, not an implementable Auto mode.',
        'Replay still includes token synthesis, vector checks, allocation and destruction. Timing differences between separate executables cannot be subtracted to assign exact parser percentages.',
        '', '## Repeated full parse and lexer measurements','',
        '| Known input / mode | Parse ms | Lexer ms | Parse/Balanced | Lexer/Balanced | Parse/prior run |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    memory={p:{r['dataset']:r for r in rows(root/f'{p}-memory.csv') if r['stage']=='lex_only'} for p in POLICIES}
    for n in NAMES:
        for p in POLICIES:
            pt=median(root,p,n,'parse');lt=median(root,p,n,'lex_only')
            lines.append(f"| {n} / {p} | {pt/1000:.3f} | {lt/1000:.3f} | {pt/median(root,'balanced',n,'parse'):.3f} | {lt/median(root,'balanced',n,'lex_only'):.3f} | {pt/median(old,p,n,'parse'):.3f} |")
    lines += ['', '## Buffer accounting','',
        'MiB are requested bytes, not RSS. Copied bytes are cumulative logical live-token relocation, not retained heap.',
        '', '| Input / mode | Tokens | Expansions | Copied MiB | Final token-buffer MiB | Lexer peak MiB |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for n in NAMES:
        for p in ('balanced','low-memory','v2-speed','v2-memory'):
            r=memory[p][n]
            lines.append(f"| {n} / {p} | {r['token_count']} | {r['token_growth_events']} | {int(r['copied_token_bytes'])/1048576:.3f} | {int(r['token_capacity'])*int(r['token_size'])/1048576:.3f} | {int(r['peak_live_bytes'])/1048576:.3f} |")
    replay=rows(root/'replay.csv')
    lines += ['', '## Isolated schedule replay','',
        '| Input | Exact-known-count ms | V2 speed schedule ms | Speed/exact | V2 memory schedule ms | Memory/exact |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for n in NAMES:
        t={p:statistics.median(float(r['median_us']) for r in replay if r['dataset']==n and r['policy']==p) for p in ('exact','speed','memory')}
        lines.append(f"| {n} | {t['exact']/1000:.3f} | {t['speed']/1000:.3f} | {t['speed']/t['exact']:.3f} | {t['memory']/1000:.3f} | {t['memory']/t['exact']:.3f} |")
    lines += ['', '## Interpretation and next experiment','',
        'Read full-parse and lexer ratios together with replay: costly recorded schedules can be slow even when density calculations and JSON parsing are absent.',
        'The byte ceiling trades a large speculative allocation for repeated copies. In dense inputs, final capacity can be exact while old/new overlap and cumulative copying remain expensive.',
        'A remaining-byte final reservation avoids only the last unnecessary expansion; it cannot recover copies already made earlier.',
        'Changing thresholds based on these known inputs would be calibration. The previous holdout is also known now; a future candidate needs a fresh evaluation set.',
        '', 'The next targeted experiment should vary the growth floor after copy pressure, while retaining the byte ceiling and the sparse-suffix regressions.',
        'Evaluate time, simultaneous peak and relocation together. A larger floor can reduce copies and increase both overlap and final slack, so no promotion follows from replay alone.',
        'Keep Balanced/LowMemory as the public choices. Representative user workloads remain necessary; this synthetic diagnosis does not establish production frequency.',
        '', 'Raw CSVs, replay schedules, source/input/binary hashes and frozen-reference hashes are in [the result directory](auto-v2-diagnosis-msvc1951/).',
        'Reproduce with [the diagnosis instructions](../auto-v2/diagnosis/README.md).']
    destination.write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--bin',type=Path);p.add_argument('--v1-bin',type=Path);p.add_argument('--replay',type=Path)
    p.add_argument('--inputs',type=Path,nargs='+');p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--report-only',action='store_true')
    a=p.parse_args()
    if a.report_only:render(a.output,a.report);return
    assert all((a.bin,a.v1_bin,a.replay,a.inputs))
    repo=Path(__file__).resolve().parents[3];old=repo/'benchmarks/results/auto-v2-msvc1951/known'
    frozen=json.loads((old/'metadata.json').read_text());programs={}
    for mode in POLICIES:
        directory=a.v1_bin if mode.startswith('v1-') else a.bin
        prefix='AutoV2' if mode.startswith('v2-') else 'Auto';goal=mode.split('-',1)[1] if mode.startswith(('v1-','v2-')) else mode
        programs[mode]={s:executable(directory,f'{prefix}{s}-{goal}') for s in ('Time','Profile','Inspect')}
        if mode.startswith('v2-'):
            programs[mode].update({s:executable(directory,f'{prefix}{s}-{goal}') for s in ('Trace','Verify')})
        for s,path in programs[mode].items():assert sha(path)==frozen['binaries'][mode][s],(mode,s)
    available=[f for d in a.inputs for f in d.glob('*.json')];by_name={f.name:f for f in available}
    assert len(by_name)==len(available),'Duplicate input names'
    inputs=[by_name[n] for n in NAMES];expected={f.name:f.stat().st_size for f in inputs}
    ref_inputs={i['name']:i for i in frozen['inputs']}
    for f in inputs:assert sha(f)==ref_inputs[f.name]['sha256'],f.name
    a.output.mkdir(parents=True);plans=a.output/'plans';plans.mkdir()
    restore=pin(0)
    try:
        run(a.replay,'--self-test');reference=run(programs['balanced']['Inspect'],*inputs)
        (a.output/'shapes.csv').write_bytes(reference.encode());memories={};journals={}
        for mode,tools in programs.items():
            assert run(tools['Inspect'],*inputs)==reference
            text=run(tools['Profile'],*inputs);memories[mode]=validate_memory(text,expected)
            (a.output/f'{mode}-memory.csv').write_bytes(text.encode())
            previous={(r['dataset'],r['stage']):r for r in rows(old/f'{mode}-memory.csv')}
            for key,r in memories[mode].items():assert r==previous[key],(mode,key)
            if mode.startswith('v2-'):
                run(tools['Verify'],*inputs);goal=mode[3:];text=run(tools['Trace'],*inputs)
                journals[goal]=validate(text,goal,expected);(a.output/f'{goal}-decisions.csv').write_bytes(text.encode())
            print(mode,'exact/profile checks passed',flush=True)
        schedules={}
        for n in NAMES:
            token_count=int(memories['balanced'][n,'lex_only']['token_count'])
            for goal in ('exact','speed','memory'):
                events=[] if goal=='exact' else [r for r in journals[goal] if r['dataset']==n and r['stage']=='lex_only']
                growths=[r for r in events if r['reason'] not in ('initial','finished','aborted')]
                initial=token_count if goal=='exact' else int(events[0]['actual_capacity'])
                plan=plans/f'{n}.{goal}.txt';plan.write_bytes(''.join(f"{r['tokens']} {r['request']} {r['actual_capacity']}\n" for r in growths).encode())
                schedules[n,goal]=(token_count,initial,plan)
        replay_rows=[];orders=[]
        for i in range(6):
            order=POLICIES[i:]+POLICIES[:i];orders.append(order)
            for mode in order:
                text=run(programs[mode]['Time'],3,5,*inputs);result=list(csv.DictReader(io.StringIO(text)))
                assert len(result)==16 and all(r['configuration']=='Release' for r in result)
                assert {(r['dataset'],r['operation']) for r in result}=={(n,o) for n in NAMES for o in ('parse','lex_only')}
                assert all(0<float(r['min_us'])<=float(r['median_us'])<=float(r['max_us']) for r in result)
                (a.output/f'{mode}-{i+1}.csv').write_bytes(text.encode())
            goals=('exact','speed','memory');goals=goals[i%3:]+goals[:i%3]
            for n in NAMES:
                for goal in goals:
                    count,initial,plan=schedules[n,goal];r=list(csv.DictReader(io.StringIO(run(a.replay,count,initial,plan,3,5))))[0]
                    assert r['configuration']=='Release' and int(r['tokens'])==count and int(r['initial_capacity'])==initial
                    assert 0<float(r['min_us'])<=float(r['median_us'])<=float(r['max_us'])
                    if goal=='exact':assert int(r['moved_tokens'])==int(r['expansions'])==0 and int(r['final_capacity'])==count
                    else:
                        m=memories['v2-'+goal][n,'lex_only']
                        assert int(r['moved_tokens'])*int(r['token_size'])==int(m['copied_token_bytes'])
                        assert r['token_size']==m['token_size'] and r['expansions']==m['token_growth_events'] and r['final_capacity']==m['token_capacity']
                    replay_rows.append(dict(dataset=n,policy=goal,round=i+1,**r))
            print('round',i+1,'of 6 complete',flush=True)
        with (a.output/'replay.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(replay_rows[0]));w.writeheader();w.writerows(replay_rows)
        files={f.relative_to(a.output).as_posix():sha(f) for f in sorted(a.output.rglob('*')) if f.is_file()}
        sources=[Path(__file__).resolve(),*Path(__file__).parent.glob('*.cpp'),Path(__file__).with_name('CMakeLists.txt'),repo/'parser/Token.hpp',repo/'benchmarks/BenchmarkUtils.cpp',repo/'benchmarks/BenchmarkUtils.hpp']
        meta=dict(created_utc=datetime.now(timezone.utc).isoformat(),base_revision='fc03daef4b88daa900195cc2245969f6e8a1212e',cpu=cpu_name(),os=platform.platform(),logical_cpu=0,
            configuration='MSVC 19.51 Release, /O2 /Ob2 /DNDEBUG; original frozen parsers and standalone replay',rounds=6,samples=5,iterations=3,round_orders=orders,
            note='Known-set diagnostic only; exact token count is offline information; replay times are not parser cost percentages.',
            frozen_metadata_sha256=sha(old/'metadata.json'),files=files,binaries={m:{s:sha(f) for s,f in d.items()} for m,d in programs.items()},replay_sha256=sha(a.replay),
            inputs=[dict(name=f.name,bytes=f.stat().st_size,sha256=sha(f)) for f in inputs],
            sources=[dict(file=f.relative_to(repo).as_posix(),sha256=hashlib.sha256(f.read_text(encoding='utf-8-sig').encode()).hexdigest()) for f in sorted(sources)])
        (a.output/'metadata.json').write_bytes((json.dumps(meta,indent=2)+'\n').encode())
    finally:restore()
    render(a.output,a.report)

if __name__=='__main__':main()
