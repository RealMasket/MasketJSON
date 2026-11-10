"""Common untimed exact/profile checks for local transfer tests and CI."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reservation'))
from check_matrix import executable,run,validate_memory,CATEGORIES
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'auto-v3'))
from journal import validate as validate_journal
from fetch import verify
POLICIES=('balanced','v3-speed','low-memory','v3-memory')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(p):return hashlib.sha256(p.read_text(encoding='utf-8-sig').encode()).hexdigest()
def tools(directory,policy):
    prefix='AutoV3' if policy.startswith('v3-') else 'Auto';goal=policy[3:] if prefix=='AutoV3' else policy
    return {s:executable(directory,f'{prefix}{s}-{goal}') for s in ('Time','Inspect','Profile','Trace','Verify')}
def observe(fixed,auto,inputs,destination,profiles=True):
    destination.mkdir(parents=True,exist_ok=True);expected={f.name:f.stat().st_size for f in inputs}
    reference=run(executable(fixed,'AutoInspect-balanced'),*inputs);(destination/'shapes.csv').write_bytes(reference.encode());memory={}
    for p in POLICIES:
        t=tools(auto if p.startswith('v3-') else fixed,p)
        assert run(t['Inspect'],*inputs)==reference,p
        if p.startswith('v3-'):run(t['Verify'],*inputs)
        if profiles:
            text=run(t['Profile'],*inputs);memory[p]=validate_memory(text,expected);(destination/f'{p}-memory.csv').write_bytes(text.encode())
            for key,row in memory[p].items():
                assert row['token_count']==memory['balanced'][key]['token_count']
                if key[1]=='whole_parse':assert all(row[c]==memory['balanced'][key][c] for c in (*CATEGORIES,'retained_bytes','dom_nodes','array_capacity'))
        if p.startswith('v3-'):
            goal=p[3:];text=run(t['Trace'],*inputs);rows=validate_journal(text,goal,expected);(destination/f'{goal}-decisions.csv').write_bytes(text.encode())
            for n in expected:
                last=next(r for r in reversed(rows) if r['dataset']==n and r['stage']=='lex_only')
                assert int(last['budget_bytes'])==(4194304 if goal=='speed' else 1048576)
                g=[r for r in rows if r['dataset']==n and int(r['pressure_floor_quarters'])]
                assert g and all(int(r['pressure_floor_quarters'])==(7 if goal=='speed' else 6) and r['pressure_lookahead']=='1' for r in g)
                if profiles:
                    m=memory[p][n,'lex_only'];assert last['tokens']==m['token_count'] and last['actual_capacity']==m['token_capacity']
                    assert int(last['moved_tokens'])*int(m['token_size'])==int(m['copied_token_bytes'])
        print(destination.name,p,'exact/profile/journal checks passed',flush=True)
    return reference
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path);p.add_argument('--fixed-bin',type=Path);p.add_argument('--auto-bin',type=Path)
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--profiles',action='store_true');a=p.parse_args()
    if a.build:
        a.fixed_bin=a.build/'benchmarks/auto';a.auto_bin=a.build/'benchmarks/auto-v3'
        if (a.fixed_bin/'Release').is_dir():a.fixed_bin/='Release'
        if (a.auto_bin/'Release').is_dir():a.auto_bin/='Release'
    assert a.fixed_bin and a.auto_bin
    manifest,inputs=verify(a.inputs);observe(a.fixed_bin,a.auto_bin,inputs,a.output,a.profiles)
    print('All five original public snapshots passed full token/value/diagnostic comparison')
