"""Profile one existing focused presentation fixture without changing its ROM."""
import argparse
import os
import re
import subprocess
from audio_reference import OUT,ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=int,required=True)
    args = parser.parse_args()
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',
                                              (OUT/'audio64.sym').read_text(),re.M)}
    source = OUT/'sweep'
    target = OUT/'attract-profile'
    target.mkdir(exist_ok=True)
    data = (source/'cases.bin').read_bytes()
    case = data[1034*args.index:1034*(args.index+1)]
    if len(case)!=1034: raise ValueError('profile fixture index out of range')
    (target/'cases.bin').write_bytes(case)
    stages = ('hud_prepare','palette_prepare','palette_start_copy','palette_copy_chunk',
              'hud_prepare_water','hud_player_bases','prepare_shapes','prepare_sprites',
              'prepare_original_sprites','render_prepare','hud_prepare_enemy_colors',
              'render_enemies','upload_name_strips','hud_upload_names','render_commit',
              'palette_commit','hud_commit_water','hud_field_colors','rpc_done')
    script = f'set profile [open {target}/stages.txt w]\nafter time 4.99 {{\n'
    for stage in stages:
        if stage not in symbols: continue
        script += f'debug set_bp {symbols[stage]} {{$::prime_remaining==0}} {{puts $::profile "{stage} '+\
                  '[expr {round(([machine_info time]-$::started)*3579545)}] '+\
                  '$::data_writes Q=[debug read memory 0xC6DC] '+\
                  'FS=[debug read memory 0xC2E1] FC=[debug read memory 0xC2E0] '+\
                  'CP=[debug read memory 0xC2DC],[debug read memory 0xC2DD]"}\n'
    script += '}\n'+(source/'start.tcl').read_text().replace(str(source),str(target))
    (target/'start.tcl').write_text(script)
    with (target/'openmsx.log').open('wb') as log:
        subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1',
                        '-cart',str(OUT/'audio64.rom'),'-romtype','ASCII16',
                        '-script',str(target/'start.tcl')],cwd=ROOT,
                       env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
    print((target/'stages.txt').read_text())


if __name__=='__main__': main()
