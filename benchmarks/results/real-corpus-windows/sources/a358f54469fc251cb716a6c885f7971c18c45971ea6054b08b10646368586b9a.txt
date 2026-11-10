"""Full generation is allowed only after freezing the selected V3 artifacts."""
import argparse,json,random
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--small',action='store_true');a=p.parse_args()
a.directory.mkdir(parents=True,exist_ok=True)
for n in ((17,53) if a.small else (197,4093)):
    r=random.Random(20261110+n);dump=lambda x:json.dumps(x,ensure_ascii=True,separators=(',',':'))
    numbers=[r.randrange(-999999,999999) for _ in range(n*7+11)]
    cells=[{'row':i,'flags':[bool(i%3),None],'children':[{},[]]} for i in range(n)]
    padding=' \r\n\t'*(n*(3 if a.small else 97))
    steps=[('[]{}\\\n\"'* (5 if a.small else 521) if i%59==0 else i) for i in range(n*3)]
    records=[([] if i<n*3//4 else {'i':i,'data':[i,-i,None,'x'*(i%31)]}) for i in range(n*3)]
    escaped=[('Привет😀\\\n\"'* (3 if a.small else 173) if i%37==0 else str(i)) for i in range(n*2)]
    floats='['+','.join(str(r.randrange(-999999,999999))+'e-'+str(r.randrange(1,9)) for _ in range(n*5))+']'
    ragged={str(i):({'v':i,'a':list(range(i%11))} if i%3 else [None,{},bool(i%2)]) for i in range(n)}
    documents={f'v3-held-buried-tail-{n}':dump({'items':cells})+padding,
        f'v3-held-step-regions-{n}':dump(steps),
        f'v3-held-late-records-{n}':dump(records),
        f'v3-held-escaped-values-{n}':json.dumps(escaped,ensure_ascii=False,separators=(',',':')),
        f'v3-held-float-values-{n}':floats,
        f'v3-held-ragged-object-{n}':dump(ragged),
        f'v3-held-space-island-{n}':'{"first":'+dump(numbers[:n])+',"second":'+padding+dump(numbers[n:])+'}',
        f'v3-held-leading-blank-{n}':padding+dump(numbers)}
    for name,text in documents.items():(a.directory/(name+'.json')).write_bytes(text.encode('utf-8'))
print('Generated 16 independent V3 cases' if not a.small else 'Generated 16 V3 smoke cases')
