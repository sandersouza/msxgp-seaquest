"""Package only the exact full-game-tested candidate into a local-only ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
from acceptance_replay import relocate_replay, verify as verify_replay

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/acceptance'
RUNTIME_BASE = '19940e8fb08ac8269990725b88a70e8c56156e16'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(summary,rom):
    if summary.get('verdict')!='pass' or len(summary.get('routes',[]))!=18:
        raise ValueError('requires all 18 successful full-game/rescue routes')
    if rom.stat().st_size!=131072 or digest(rom)!=summary['rom_sha256']:
        raise ValueError('cartridge differs from the full-game-tested 128 KiB candidate')
    if digest(rom.with_suffix('.sym'))!=summary['symbols_sha256']:
        raise ValueError('symbols differ from the full-game-tested candidate')
    expected = {(m,mode,d,'exhaust') for m in ('C-BIOS_MSX1','C-BIOS_MSX1_EU')
                for mode in (0,1) for d in (0,64,128,192)}
    expected |= {(m,0,0,'rescue') for m in ('C-BIOS_MSX1','C-BIOS_MSX1_EU')}
    observed = []
    for r in summary['routes']:
        game = r['full_game']
        observed.append((r['machine'],game['mode'],game['difficulty'],game['controller']))
        if r['verdict']!='pass' or r['rom_sha256']!=summary['rom_sha256'] or r['symbols_sha256']!=summary['symbols_sha256']:
            raise ValueError('mixed cartridge/symbol identities in route reports')
        if r['mapper']!='ASCII16' or r['ram_kib']!=64 or r['vram_kib']!=16 or r['cpu_hz']!=3579545:
            raise ValueError('route used different target hardware settings')
        if r['skipped_vdp_frames'] or r['visible_commits'] or r['ram_reloads_after_chain_start']:
            raise ValueError('route has pacing/state failures')
    if len(set(observed))!=18 or set(observed)!=expected:
        raise ValueError('missing or duplicated mode/difficulty/standard route')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'outputs/video/seaquest-issue14-final.rom')
    args = parser.parse_args()
    summary = json.loads((OUT/'summary.json').read_text())
    validate(summary,args.rom)
    replays = json.loads((OUT/'replay-summary.json').read_text())
    if replays.get('verdict')!='pass' or len(replays.get('routes',[]))!=18:
        raise ValueError('all 18 device replays must pass independently before packaging')
    replay_reports = {r['path']:r for r in replays['routes']}
    baseline = json.loads((ROOT/'references/video/summary.json').read_text())
    if baseline['verdict']!='pass' or baseline['rom_sha256']!=summary['rom_sha256']:
        raise ValueError('inherited video evidence is for another cartridge')
    destination = OUT/('seaquest-issue15-'+summary['rom_sha256'][:12]+'.zip')
    if destination.exists():
        raise FileExistsError(f'preserving existing package: {destination}')
    with tempfile.TemporaryDirectory(dir=OUT,prefix='package-') as temporary:
        folder = Path(temporary)
        shutil.copyfile(args.rom,folder/'seaquest.rom')
        shutil.copyfile(args.rom.with_suffix('.sym'),folder/'seaquest.sym')
        for name in ('hardware-acceptance.md','acceptance-observations.md'):
            shutil.copyfile(ROOT/'docs'/name,folder/name)
        for r in summary['routes']:
            source = ROOT/r['path']
            if json.loads(source.read_text())!={k:v for k,v in r.items() if k!='path'}:
                raise ValueError(f'route report changed since summary: {source}')
            replay = source.parent/'game.omr'
            if digest(replay)!=r['replay_sha256']:
                raise ValueError(f'replay changed: {replay}')
            target = folder/'replays'/r['machine']/source.parent.name
            target.mkdir(parents=True)
            replay_result = json.loads((source.parent/'replay-result.json').read_text())
            if (replay_result.get('verdict')!='pass' or replay_result['replay_sha256']!=r['replay_sha256']
                    or replay_reports.get(r['path'])!=dict(path=r['path'],**replay_result)):
                raise ValueError('missing or stale independent replay verification')
            relocate_replay(replay,target/'game.omr',args.rom,relative=True)
            shutil.copyfile(source,target/'result.json')
            shutil.copyfile(source.parent/'replay-result.json',target/'replay-result.json')
            # Verify packaged relative-path snapshots against the extracted ROM,
            # without a controller, original checkout ROM path or raw trace file.
            verify_replay(target,folder/'seaquest.rom')
            for name in ('replayed-states.bin','replay-check.tcl','replay-check.omr','replay-check.log'):
                (target/name).unlink(missing_ok=True)
        (folder/'automated-results.json').write_text(json.dumps(summary,indent=2)+'\n')
        files = {str(p.relative_to(folder)):dict(bytes=p.stat().st_size,sha256=digest(p))
                 for p in sorted(folder.rglob('*')) if p.is_file()}
        manifest = dict(format_version=1,runtime_base_commit=RUNTIME_BASE,
                        delivery_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                        mapper='ASCII16',ram_kib=64,vram_kib=16,cpu_hz=3579545,
                        rom_sha256=summary['rom_sha256'],symbols_sha256=summary['symbols_sha256'],
                        files=files,automated='pass',manual_emulator='pending owner observation',
                        physical_hardware='pending actual machine test',
                        inherited_video_evidence_sha256=digest(ROOT/'references/video/summary.json'),
                        publication='local only; contains original-derived cartridge and replay snapshots')
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as archive:
            for p in sorted(folder.rglob('*')):
                if p.is_file(): archive.write(p,p.relative_to(folder))
        with zipfile.ZipFile(destination) as archive:
            if archive.testzip(): raise ValueError('corrupt package member')
            for name,item in files.items():
                if hashlib.sha256(archive.read(name)).hexdigest()!=item['sha256']:
                    raise ValueError(f'packaged content mismatch: {name}')
    result = dict(path=str(destination.relative_to(ROOT)),sha256=digest(destination),
                  rom_sha256=summary['rom_sha256'],bytes=destination.stat().st_size,verdict='pass')
    (OUT/'package.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__': main()
