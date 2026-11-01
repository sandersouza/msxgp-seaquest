"""Real-load qualification hooks for the flat-RAM disk/plain-cartridge targets.

These hooks never install game code or data. The loader must materialize every
immutable byte itself. Debug writes only mark the unused guard/stack reserve.
"""
from pathlib import Path
import struct


def disk_com_bytes(image):
    """Read the DOS1 root file through its actual FAT12 cluster chain."""
    if len(image)<512:
        raise ValueError('truncated DOS1 disk image')
    bps=struct.unpack_from('<H',image,11)[0]
    spc=image[13]
    reserved=struct.unpack_from('<H',image,14)[0]
    fats=image[16]
    entries=struct.unpack_from('<H',image,17)[0]
    spf=struct.unpack_from('<H',image,22)[0]
    if bps!=512 or spc not in (1,2,4,8) or not reserved or not 1<=fats<=2 or not spf:
        raise ValueError('expected a standard DOS1 FAT12 floppy')
    root=(reserved+fats*spf)*bps
    data_start=root+(entries*32+bps-1)//bps*bps
    if data_start>=len(image):
        raise ValueError('invalid DOS1 floppy geometry')
    for index in range(entries):
        entry=image[root+index*32:root+(index+1)*32]
        if entry[:11]==b'SEAQUESTCOM' and not entry[11]&0x18:
            cluster=struct.unpack_from('<H',entry,26)[0]
            length=struct.unpack_from('<I',entry,28)[0]
            break
    else:
        raise ValueError('disk root does not contain SEAQUEST.COM')
    cluster_bytes=spc*bps
    maximum=(len(image)-data_start)//cluster_bytes+2
    result=bytearray()
    visited=set()
    while len(result)<length:
        if not 2<=cluster<min(maximum,0xff0) or cluster in visited:
            raise ValueError('invalid or cyclic SEAQUEST.COM cluster chain')
        visited.add(cluster)
        offset=data_start+(cluster-2)*cluster_bytes
        result+=image[offset:offset+cluster_bytes]
        offset=reserved*bps+cluster*3//2
        if offset+1>=(reserved+spf)*bps:
            raise ValueError('SEAQUEST.COM cluster exceeds FAT')
        value=image[offset]|image[offset+1]<<8
        cluster=value>>4 if cluster&1 else value&4095
    return bytes(result[:length])


def launch_arguments(delivery, binary, disk):
    if delivery=='dos':
        if disk is None or not disk.is_file():
            raise ValueError('--delivery dos requires a private bootable --disk')
        if disk_com_bytes(disk.read_bytes())!=binary.read_bytes():
            raise ValueError('SEAQUEST.COM on the disk differs from the --rom executable')
        return ['-diska',str(disk)]
    if delivery=='plain32' and binary.stat().st_size!=32768:
        raise ValueError('plain32 qualification requires the exact 32768-byte cartridge')
    return ['-cart',str(binary),'-romtype','Normal' if delivery=='plain32' else 'ASCII16']


def configure(harness,s,delivery,read_only=False):
    start=s['native_cold_end']
    size=0xf300-start
    harness=f'set native_guard_start {start}\nset native_guard_size {size}\n'+harness
    harness=harness.replace('0xF000 768','$::native_guard_start $::native_guard_size')
    harness=harness.replace('165] 768]','165] $::native_guard_size]')
    harness=harness.replace('debug write_block memory 0xF000 [string repeat [binary format c 165] 896]',
                            'debug write_block memory $::native_guard_start [string repeat [binary format c 165] [expr {$::native_guard_size+128}]]')
    harness=harness.replace('set ::stack_marker 201','set ::stack_marker 165')
    harness=harness.replace('binary format c 201','binary format c 165')
    harness=harness.replace('{$cold?0:5}','{$cold?0:60}')
    harness=harness.replace('set bios [dict get [machine_info device {C-BIOS Main ROM}] actualSHA1]', '''set bios unavailable
    foreach device [machine_info device] {
        set info [machine_info device $device]
        if {[dict get $info type] eq "ROM" && [string match -nocase *bios* $device]} {
            set bios [dict get $info actualSHA1]
            break
        }
    }''')
    hook=f'''
set loaded_native 0
set native_token_chunks 0
debug set_bp 0x0100 {{[debug read memory 0x100]==243 && [debug read memory 0x101]==195 && !$::loaded_native}} {{
    set ::loaded_native 1
    set f [open $::out/loaded.bin wb]
    puts -nonewline $f [debug read_block memory 0 65535]
    close $f
    set f [open $::out/loaded-resident.bin wb]
    puts -nonewline $f [debug read_block VRAM 0x3800 1504]
    close $f
    set ::immutable {{}}
    foreach {{start size}} {{256 {s['native_static_end']-256} 53248 7168 61440 {s['native_cold_end']-61440} 62464 3060}} {{
        lappend ::immutable [list $start $size [debug read_block memory $start $size]]
        debug set_watchpoint write_mem [list $start [expr {{$start+$size-1}}]] {{}} {{
            fail_video "immutable-write PC=[format %04X [reg PC]]"
        }}
    }}
    set ::secondary [debug read memory 0xFFFF]
    debug set_bp {s['palette_translate_ids_chunk']} {{}} {{
        if {{[debug read memory 0xC6EA]!=[debug read memory 0xCEB8]}} {{
            fail_video token-generation-changed-during-copy
        }}
        incr ::native_token_chunks
        debug cont
    }}
    debug write_block memory $::native_guard_start [string repeat [binary format c 165] [expr {{$::native_guard_size+128}}]]
    debug cont
}}
rename finish_video original_finish_video
proc finish_video {{}} {{
    if {{!$::loaded_native}} {{fail_video native-load-missing}}
    foreach range $::immutable {{
        lassign $range start size expected
        if {{[debug read_block memory $start $size] ne $expected}} {{fail_video immutable-RAM}}
    }}
    if {{[debug read memory 0xFFFF]!=$::secondary}} {{fail_video secondary-slot-changed}}
    set f [open $::out/native-integrity.json w]
    puts $f "\\{{\\\"immutable_write_watchpoints\\\":true,\\\"token_chunks_verified\\\":$::native_token_chunks\\}}"
    close $f
    original_finish_video
}}
'''
    if read_only:
        # View-only OMR playback rejects debugger writes. Compare the reserve
        # with its real loader bytes instead of installing a marker pattern.
        harness=harness.replace('        if {[debug read_block memory 0xF300 64] ne [string repeat [binary format c 165] 64]} {fail_video cold-stack-baseline}\n','')
        harness=harness.replace('[lindex $stack $i]!=$::stack_marker','[lindex $stack $i]!=[lindex $::native_stack_initial $i]')
        hook=hook.replace('    debug write_block memory $::native_guard_start [string repeat [binary format c 165] [expr {$::native_guard_size+128}]]',
                          '    binary scan [debug read_block memory 0xF300 128] cu* ::native_stack_initial')
    harness+=hook
    return harness


def verify_loaded(target,runtime,s):
    memory=(target/'loaded.bin').read_bytes()
    expected=runtime.read_bytes()
    if len(expected)!=65536:
        raise ValueError('expected a complete, independently built 64 KiB RAM image')
    for start,end in ((0x100,s['native_static_end']),(0xd000,0xec00),
                      (0xf000,s['native_cold_end']),(0xf400,0xfff4)):
        if memory[start:end]!=expected[start:end]:
            raise ValueError(f'loaded immutable segment mismatch at {start:04X}')
    if (target/'loaded-resident.bin').read_bytes()!=(runtime.parent/'resident.bin').read_bytes():
        raise ValueError('loader did not prepare the resident sprite atlas')
