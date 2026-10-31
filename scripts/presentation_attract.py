"""Continuous native idle-palette boundaries/exits from a real game-over seed."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from audio_reference import OUT,ROOT
from graphics_palette import tms_color
from original_graphics import read_original,extract
from presentation_check import PresentationOracle
from render_bench import check_original_sprites


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick',action='store_true')
    wrap = parser.add_mutually_exclusive_group()
    wrap.add_argument('--force-generation-wrap',action='store_true',help='force real native token rebase in each chain that allocates')
    wrap.add_argument('--ready-generation-wrap',action='store_true',help='carry token240 pending IDs through activation and next epoch')
    parser.add_argument('--profile-chain',type=int,default=0)
    parser.add_argument('--profile-start',type=int,default=90)
    parser.add_argument('--skip-source',action='store_true',help='timing/pixels only; not source acceptance')
    args = parser.parse_args()
    target = OUT/'attract-continuous'
    target.mkdir(exist_ok=True)
    symbols = {n:int(v,16) for n,v in re.findall(r'^(\w+): EQU 0x([0-9A-Fa-f]+)',
                                               (OUT/'audio64.sym').read_text(),re.M)}
    symbols['sample_input_return'] = symbols['core_F6A9']
    rom = read_original()
    cold = (ROOT/'outputs/input/natural.bin').read_bytes()
    # Select the first genuine game-over post-state from the cold device replay.
    # No manually normalized gameplay flags or renderer buffers seed the chain.
    seed_tick = next((tick for tick in range(1000,len(cold)//2303)
                      if (state:=cold[tick*2303+2052:(tick+1)*2303])[0xa3]
                      and not any(state[address] for address in (0xe9,0xbb,0xc2))),None)
    if seed_tick is None: raise ValueError('cold device replay has no genuine game-over seed')
    seed = bytearray(1024)
    seed[:251] = cold[seed_tick*2303+2052:(seed_tick+1)*2303]
    configs = [(n,240,1,63,0,255) for n in ([199] if args.quick else range(127,256))]
    for n in ([199] if args.quick else (127,199,215,255)):
        for phase in (254,255,0):
            for action in (1,2,3): configs.append((n,240,1,63,action,phase))
    if not args.quick:
        configs += [(n,240,1,55,0,255) for n in (127,128,191,199,215,255)]
        configs += [(199,a3,player,63,0,255) for a3 in (1,96,104,159,160,255) for player in (0,1)]
    seeds = []
    for counter,a3,player,switches,action,phase in configs:
        state = bytearray(seed)
        state[0x81],state[0xa2],state[0xa3],state[0xb7] = 160,counter,a3,player
        state[0x85],state[0x86] = ((2*counter)&255,7 if switches==55 else 247) if counter>=128 else (0,15 if switches==55 else 255)
        for lane in range(4):
            raw = 8 if state[0xd9+lane]&4 else rom[0xf0f+(state[0xbd]&7)]
            state[0xac+lane] = (raw^state[0x85])&state[0x86]
        state[0x280],state[0x282],state[0x284] = 255,switches,0
        state[12],state[13] = 128,128
        seeds.append(state)
    (target/'seeds.bin').write_bytes(b''.join(seeds))
    (target/'case-index.json').write_text(json.dumps(configs)+'\n')
    chain_ticks = 384 if args.ready_generation_wrap else 112
    epoch_seed = 239 if args.ready_generation_wrap else 240
    watchdog_seconds = max(1000,len(configs)*(chain_ticks+4)//50+60)
    script = f'set out {target}\nset chain_ticks {chain_ticks}\nset epoch_seed {epoch_seed}\nset watchdog_seconds {watchdog_seconds}\n'
    script += f'set profile_chain {args.profile_chain}\nset profile_start {args.profile_start}\nset force_wrap {int(args.force_generation_wrap or args.ready_generation_wrap)}\nset palette_rebase_generations {symbols["palette_rebase_generations"]}\n'
    for name,column in (('switches',3),('actions',4),('phases',5)):
        script += 'set '+name+' {'+' '.join(str(row[column]) for row in configs)+'}\n'
    names = ('core_F00E','audio_prime_start','rpc_done','paced_start','paced_commit',
             'paced_frame_start','paced_core_start','paced_core_done','paced_prepared','paced_wait','sample_input_return')
    script += ''.join(f'set {name} {symbols[name]}\n' for name in names)
    script += f'set palette_prefetch {symbols["palette_prefetch"]}\n'
    script += 'set profile_stages {'+' '.join(f'{name} {symbols[name]}' for name in
              ('hud_prepare','palette_prepare','palette_forecast_apply','prepare_shapes','prepare_sprites',
               'prepare_original_sprites','render_prepare','hud_prepare_enemy_colors','render_enemies',
               'upload_name_strips','hud_upload_names','hud_field_colors','palette_default_prepare',
               'palette_translate_ids','hud_prepare_water','hud_player_bases','palette_player_memo',
               'palette_prefetch','palette_enemy_prefetch','palette_player_prefetch','palette_forecast_tick',
               'palette_rebase_generations','palette_copy_chunk'))+'}\n'
    (target/'start.tcl').write_text(script+'source scripts/presentation_attract.tcl\n')
    with (target/'openmsx.log').open('wb') as log:
        subprocess.run(['openmsx','-control','stdio','-machine','C-BIOS_MSX1','-cart',str(OUT/'audio64.rom'),
                        '-romtype','ASCII16','-script',str(target/'start.tcl')],cwd=ROOT,
                       env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
                       stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
    report = json.loads((target/'result-raw.json').read_text())
    oracle = PresentationOracle(rom)
    assets = extract(rom)
    pixels = (target/'pixels.bin').read_bytes()
    states = (target/'pixel-states.bin').read_bytes()
    pages = (target/'pixel-pages.bin').read_bytes()
    for index in range(len(pages)//3):
        page,backdrop,r1 = pages[index*3:index*3+3]
        state = states[index*251:(index+1)*251]
        frame = pixels[index*16384:(index+1)*16384]
        if backdrop&15!=tms_color((rom[0xcf2]^state[0x85])&state[0x86]):
            raise ValueError(f'water backdrop mismatch:{index}')
        oracle.check(state,frame,page*1024,backdrop&15,bool(r1&64))
        check_original_sprites(state,frame,assets,rom,True)
    report['pixel_frames'] = len(pages)//3
    if (args.force_generation_wrap or args.ready_generation_wrap) and not report['generation_rebases']:
        raise ValueError('forced generation rebase was not exercised')
    if args.ready_generation_wrap and not report['ready_epoch_exposures']:
        raise ValueError('ready pending palette was not exercised at token240')
    report['source_ticks_verified'] = 0
    if not args.skip_source:
        from native_contract import reference
        from collision_reference import contacts
        data = (target/'native.bin').read_bytes()
        for index,offset in enumerate(range(0,len(data),2303)):
            raster = data[offset:offset+1024]
            before = bytearray(data[offset+1024:offset+2048])
            acquired = contacts(raster,rom,assets)
            if before[0xb0:0xb7]+before[0xf8:0xf9]!=acquired:
                raise ValueError(f'attract source acquisition:{index}')
            before[0x280],before[0x282],before[12],before[13] = data[offset+2048:offset+2052]
            expected,_ = reference(rom,list(before),0xf5b8,0,130,0,0)
            if expected!=data[offset+2052:offset+2303]: raise ValueError(f'attract native state:{index}')
            report['source_ticks_verified'] += 1
    report.update(rom_sha256=hashlib.sha256((OUT/'audio64.rom').read_bytes()).hexdigest(),
                  source=f'real cold game-over post-state; one RAM seed per{chain_ticks}-update chain',
                  source_acceptance=not args.skip_source,seed_tick=seed_tick,
                  chain_ticks=chain_ticks,generation_seed=epoch_seed if args.force_generation_wrap or args.ready_generation_wrap else None)
    result_text = json.dumps(report,indent=2)+'\n'
    (target/'result.json').write_text(result_text)
    mode = 'ready' if args.ready_generation_wrap else 'wrap' if args.force_generation_wrap else 'continuous'
    (OUT/f'attract-{mode}-result.json').write_text(result_text)
    print(json.dumps(report))
    if report['skipped'] or report['visible_commit'] or report['max_busy']>=59736:
        raise ValueError('continuous attract timing failed')


if __name__=='__main__': main()
