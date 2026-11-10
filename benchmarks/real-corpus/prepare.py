"""Snapshot both compiler builds and freeze code/data identities before timing."""
import argparse,json,shutil,subprocess,re
from pathlib import Path
from datetime import datetime,timezone
from common import sha,normalized,tools,POLICIES
from fetch import verify,MANIFEST
p=argparse.ArgumentParser();p.add_argument('--msvc-build',type=Path,required=True);p.add_argument('--clang-build',type=Path,required=True)
p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[2]
verify(a.inputs);a.output.mkdir(parents=True);compilers={};binaries={}
def bindir(build,part):
    d=build/'benchmarks'/part
    return d/'Release' if (d/'Release').is_dir() else d
for compiler,build in (('msvc',a.msvc_build),('clang',a.clang_build)):
    destination=a.output/compiler;destination.mkdir();auto=bindir(build,'auto-v3');fixed=bindir(build,'auto')
    info=(auto/'build-info-Release.txt').read_text();kv=dict(line.split('=',1) for line in info.splitlines() if '=' in line)
    assert kv['configuration']=='Release' and kv['compiler']==('MSVC' if compiler=='msvc' else 'Clang')
    assert kv['compiler_version']==('19.51.36257.0' if compiler=='msvc' else '23.1.5')
    assert all(kv[k]==v for k,v in dict(speed_budget_bytes='4194304',memory_budget_bytes='1048576',speed_quarters='7',memory_quarters='6',speed_lookahead='1',memory_lookahead='1').items())
    cache={}
    for line in (build/'CMakeCache.txt').read_text().splitlines():
        if line and not line.startswith(('#','//')) and '=' in line and ':' in line.split('=',1)[0]:
            key,value=line.split('=',1);cache[key.split(':',1)[0]]=value
    compiler_settings=next((build/'CMakeFiles').glob('*/CMakeCXXCompiler.cmake')).read_text()
    if 'CMAKE_CXX_COMPILER' not in cache:
        cache['CMAKE_CXX_COMPILER']=re.search(r'set\(CMAKE_CXX_COMPILER "([^"]+)"\)',compiler_settings).group(1)
    runtime=re.search(r'set\(CMAKE_MSVC_RUNTIME_LIBRARY_DEFAULT "([^"]+)"\)',compiler_settings)
    cache['CMAKE_MSVC_RUNTIME_LIBRARY_DEFAULT']=runtime.group(1) if runtime else None
    assert not any(flag in (cache['CMAKE_CXX_FLAGS']+' '+cache['CMAKE_CXX_FLAGS_RELEASE']).lower() for flag in ('/gl','-flto','/fp:fast','-ffast-math'))
    selected={}
    for policy in POLICIES:
        items=tools(auto if policy.startswith('v3-') else fixed,policy)
        for kind in ('Time','Inspect','Profile','Trace','Verify') if policy.startswith('v3-') else ('Time','Inspect','Profile'):
            f=items[kind];shutil.copyfile(f,destination/f.name);selected[f.name]=sha(f)
    compilers[compiler]=dict(build_info=kv,cache={k:cache.get(k) for k in ('CMAKE_CXX_FLAGS','CMAKE_CXX_FLAGS_RELEASE','CMAKE_BUILD_TYPE','CMAKE_GENERATOR','CMAKE_LINKER','CMAKE_MSVC_RUNTIME_LIBRARY','CMAKE_MSVC_RUNTIME_LIBRARY_DEFAULT')},compiler_binary_sha256=sha(Path(cache['CMAKE_CXX_COMPILER'])),target='Windows x64 MSVC ABI',standard_library='Microsoft STL 14.51.36231, Release CRT /MD; link.exe 14.51',application_allocator='Microsoft CRT; compiler executable allocator is irrelevant to measured applications')
    binaries[compiler]=selected
tracked=subprocess.check_output(['git','-c','safe.directory='+repo.as_posix(),'ls-files'],cwd=repo,text=True).splitlines()
prefixes=('core/','parser/','serializer/','io/','errors/','diagnostics/','utils/','fuzz/','benchmarks/real-corpus/','benchmarks/auto/','benchmarks/auto-v3/','benchmarks/reservation/')
paths=[repo/f for f in tracked if (f.startswith(prefixes) or f in ('CMakeLists.txt','benchmarks/CMakeLists.txt','benchmarks/BenchmarkUtils.cpp','benchmarks/BenchmarkUtils.hpp','benchmarks/ParserProfile.cpp','benchmarks/MemoryTracker.cpp','benchmarks/MemoryTracker.hpp','pch.cpp','pch.h')) and Path(f).suffix in ('.cpp','.hpp','.h','.py','.json','.txt')]
stdlib=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/include/yvals_core.h')
out=dict(frozen_utc=datetime.now(timezone.utc).isoformat(),source_revision=subprocess.check_output(['git','-c','safe.directory='+repo.as_posix(),'rev-parse','HEAD'],cwd=repo,text=True).strip(),corpus_sha256=sha(MANIFEST),plan_sha256=sha(Path(__file__).with_name('plan.json')),compilers=compilers,binaries=binaries,standard_library_header_sha256=sha(stdlib),sources=[dict(file=f.relative_to(repo).as_posix(),sha256=normalized(f)) for f in sorted(paths)],source_hash_format='UTF-8 without BOM, LF line endings')
(a.output/'freeze.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print('Frozen both compiler builds and all code/data identities')
