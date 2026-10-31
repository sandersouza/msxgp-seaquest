"""Check startup decompression and capture one isolated HUD frame in openMSX."""
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/presentation'


def main():
    symbols = {name:int(value,16) for name,value in re.findall(
        r'^(\w+): EQU 0x([0-9A-Fa-f]+)',(OUT/'hud64.sym').read_text(),re.M)}
    data = (OUT/'hud.bin').read_bytes()
    (OUT/'hud-probe-start.tcl').write_text(''.join(
        f'set {name} {symbols[name]}\n' for name in ('rpc_start','rpc_done','core_F5B8'))+
        'set hud_stages {'+' '.join(f'{name} {symbols[name]}' for name in
          ('hud_prepare','hud_build_colors','prepare_shapes','prepare_sprites','prepare_original_sprites',
           'render_prepare','render_commit','hud_commit','hud_field_colors'))+'}\n'+
        f'set hud_bytes {len(data)}\nsource scripts/hud_probe.tcl\n')
    with (OUT/'hud-probe.log').open('wb') as log:
        subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1',
                        '-cart',str(OUT/'hud64.rom'),'-romtype','ASCII16',
                        '-script',str(OUT/'hud-probe-start.tcl')],cwd=ROOT,
                       env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                       stdout=log,stderr=subprocess.STDOUT,timeout=20,check=True)
    if (OUT/'unpacked.bin').read_bytes()!=data: raise ValueError('native HUD decompression differs')
    print(json.dumps(json.loads((OUT/'hud-probe.json').read_text())))


if __name__=='__main__': main()
