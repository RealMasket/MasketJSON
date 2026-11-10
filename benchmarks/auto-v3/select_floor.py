"""Apply the pre-registered joint-gate rule without consulting new inputs."""
import csv,hashlib,json,math,statistics,sys
from datetime import datetime,timezone
from pathlib import Path
root,destination=map(Path,sys.argv[1:]);assert not destination.exists()
plan_path=Path(__file__).with_name('selection-plan.json');plan=json.loads(plan_path.read_text());scores={}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert plan['original_plan_sha256']==sha(plan_path.with_name('plan.json'))
for label,h in plan['phase1_metadata'].items():assert sha(root/label/'metadata.json')==h
for label,config in plan['candidates'].items():
    q=config['quarters']
    d=root/label;m=json.loads((d/'metadata.json').read_text());assert len(m['inputs'])==91
    times={p:{r['dataset']:float(r['median_us']) for r in csv.DictReader((d/f'{p}-1.csv').open()) if r['operation']=='parse'} for p in ('balanced','low-memory','speed','memory')}
    peaks={p:{r['dataset']:int(r['peak_live_bytes']) for r in csv.DictReader((d/f'{p}-memory.csv').open()) if r['stage']=='whole_parse'} for p in times}
    names=list(times['balanced']);non=[n for n in names if times['balanced'][n]>=1000];assert non
    for goal in ('speed','memory'):
        wt=max(times[goal][n]/min(times['balanced'][n],times['low-memory'][n]) for n in non)
        wb=max(times[goal][n]/times['balanced'][n] for n in non)
        wp=max(peaks[goal][n]/min(peaks['balanced'][n],peaks['low-memory'][n]) for n in non)
        pb=max(peaks[goal][n]/peaks['balanced'][n] for n in non)
        regret=max(wt/1.5,wp/2,pb/1.5) if goal=='speed' else max(wb/2,wp/1.5)
        gm=math.exp(statistics.mean(math.log(times[goal][n]/times['balanced'][n]) for n in names))
        scores[label,goal]=dict(quarters=q,lookahead=config['lookahead'],budget_bytes=plan['budgets'][goal+'_bytes'],joint_eligible=regret<=1,worst_time_oracle=wt,worst_time_balanced=wb,worst_peak_oracle=wp,worst_peak_balanced=pb,normalized_gate_regret=regret,geomean_time_balanced=gm)
chosen={}
for goal in ('speed','memory'):
    eligible=[l for l in plan['candidates'] if scores[l,goal]['joint_eligible']]
    if eligible:
        fastest=min(scores[l,goal]['geomean_time_balanced'] for l in eligible)
        tied=[l for l in eligible if scores[l,goal]['geomean_time_balanced']<=1.03*fastest]
        label=min(tied,key=lambda l:scores[l,goal]['worst_peak_oracle'])
    else:label=min(plan['candidates'],key=lambda l:(scores[l,goal]['normalized_gate_regret'],scores[l,goal]['geomean_time_balanced']))
    chosen[goal]=dict(candidate=label,**scores[label,goal])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=dict(frozen_utc=datetime.now(timezone.utc).isoformat(),chosen=chosen,scores={f'{l}/{g}':v for (l,g),v in scores.items()},plan_sha256=sha(plan_path),calibration_metadata={l:sha(root/l/'metadata.json') for l in plan['candidates']},note='Exploratory single-round selection. Final repeated joint targets may still fail; no new-input observations used.')
destination.write_bytes((json.dumps(out,indent=2)+'\n').encode());print(json.dumps(out,indent=2))
