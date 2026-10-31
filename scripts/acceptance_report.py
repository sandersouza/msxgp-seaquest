"""Export concise public evidence without original-derived states or snapshots."""
import hashlib
import argparse
import importlib.metadata
import json
from pathlib import Path
from acceptance_package import validate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/acceptance'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'outputs/video/seaquest-issue14-final.rom')
    args = parser.parse_args()
    summary = json.loads((OUT/'summary.json').read_text())
    validate(summary,args.rom)
    replay = json.loads((OUT/'replay-summary.json').read_text())
    if replay['verdict']!='pass' or len(replay['routes'])!=18:
        raise ValueError('incomplete independent replay matrix')
    replay_by_path = {r['path']:r for r in replay['routes']}
    routes = []
    for r in summary['routes']:
        target = (ROOT/r['path']).parent
        replay_row = replay_by_path[r['path']]
        if replay_row['verdict']!='pass' or replay_row['replay_sha256']!=r['replay_sha256']:
            raise ValueError('replay identity differs from verified original route')
        routes.append(dict(machine=r['machine'],scenario=r['full_game'],frames=r['frames'],
                           source_updates=r['source_ticks_verified'],pixel_frames=r['pixel_frames'],
                           ordered_audio_stores=r['audio']['ordered_stores'],max_busy=r['max_busy'],
                           stack_min=r['stack_min'],clock_windows=r['cadence_windows_verified'],
                           trace_path=str(target.relative_to(ROOT)),
                           trace_sha256=hashlib.sha256((target/'native.bin').read_bytes()).hexdigest(),
                           timing_sha256=hashlib.sha256((target/'timing.jsonl').read_bytes()).hexdigest(),
                           replay_sha256=r['replay_sha256'],replayed_state_sha256=replay_row['state_sha256'],
                           verdict=r['verdict']))
    evidence = dict(verdict='pass',rom_sha256=summary['rom_sha256'],symbols_sha256=summary['symbols_sha256'],
                    rom_bytes=131072,mapper='ASCII16',original_sha256=summary['routes'][0]['original_sha256'],
                    frames=sum(r['frames'] for r in routes),source_updates=sum(r['source_updates'] for r in routes),
                    pixel_frames=sum(r['pixel_frames'] for r in routes),
                    ordered_audio_stores=sum(r['ordered_audio_stores'] for r in routes),
                    clock_windows=sum(r['clock_windows'] for r in routes),
                    replayed_routes=len(routes),skipped_vdp_frames=0,visible_commits=0,
                    ram_reloads_after_boot=0,routes=routes,
                    tools={k:summary['routes'][0][k] for k in ('python','openmsx')},
                    machines={r['machine']:r['observed_machine'] for r in summary['routes']},
                    validator_sources_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted((ROOT/'scripts').glob('*')) if p.suffix in ('.py','.tcl')},
                    inherited_controlled_evidence='references/video/verification.md; identical cartridge SHA256',
                    manual_emulator='pending owner viewing/listening',physical_hardware=False,
                    natural_full_six_diver_rescue=False,
                    limitation='natural rescue routes cover partial rescue and oxygen death; full-six bonuses retain controlled fixture coverage')
    evidence['tools'].update({name:importlib.metadata.version(name) for name in ('ale-py','py65','numpy')})
    destination = ROOT/'references/acceptance'
    destination.mkdir(exist_ok=True)
    (destination/'suite.json').write_text(json.dumps(evidence,indent=2)+'\n')
    boundary = OUT/'boundary-regression/C-BIOS_MSX1_EU/attract-ready-quick/result.json'
    (destination/'boundary-regression.json').write_text(boundary.read_text())
    print(json.dumps({k:evidence[k] for k in ('verdict','frames','source_updates','pixel_frames','ordered_audio_stores','clock_windows')}))


if __name__=='__main__': main()
