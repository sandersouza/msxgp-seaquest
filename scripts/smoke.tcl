# Isolated diagnostic boot, not a gameplay acceptance test.
set renderer none
set speed 999
set throttle off
set power true
after time 5 {
    set signature [list [debug read memory 0xC000] [debug read memory 0xC001]]
    if {$signature ne {83 81}} {error "Diagnostic did not boot: $signature"}
    if {[debug read VRAM 0] != 255} {error "Pattern VRAM was not initialized"}
    if {[debug read VRAM 0x2000] != 33} {error "Color VRAM was not initialized"}
    if {[debug read VRAM 0x1800] != 0} {error "Name table was not initialized"}
    set ticks [debug read memory 0xC002]
    after time 0.1 [list apply {{previous} {
        if {[debug read memory 0xC002] == $previous} {error "BIOS interrupts did not advance"}
        set result [open "outputs/smoke-result.json" w]
        puts $result {{"passed":true,"signature":"5351","pattern":255,"color":33,"name":0,"interrupts":"advancing"}}
        close $result
        puts stderr "SEAQUEST_SMOKE_PASS signature=5351 pattern=255 color=33 name=0 interrupts=advancing"
        exit
    }} $ticks]
}
