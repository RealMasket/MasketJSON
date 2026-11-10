"""Retain v2 proofs and check the independently computed pressure growth floor."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'auto-v2'))
from check_journal import validate as validate_v2

def validate(text,goal,names):
    rows=validate_v2(text,goal,names)
    for r in rows:
        if r['reason'] in ('initial','finished','aborted','allocation_failed'):continue
        n=int(r['tokens']);q=int(r['pressure_floor_quarters']);assert q in (6,7,8)
        base=n+max(n//(2 if goal=='speed' else 4),1)
        floor=n+max(n*(q-4)//4,1) if r['pressure_active']=='1' else base
        expected=max(base,floor)
        assert int(r['lower'])==expected
        assert (r['pressure_raised_floor']=='1')==(expected>base)
    return rows
