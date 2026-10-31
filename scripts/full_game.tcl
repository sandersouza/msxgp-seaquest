# Private cold-boot device-only controller. No canonical or platform RAM writes.
# All controls pass through the cartridge's keyboard/PSG sampler. Record the
# resulting device events for a replay independent of feedback-controller code.
set game_started 0
set game_restarted 0
reverse start
set rescue_goal 1
set rescue_previous_divers 0
set oxygen_controller_started 1
set rescue_phase partial
set rescue_source [read [set rescue_file [open scripts/oxygen_natural.tcl r]]]
close $rescue_file
# Reuse the established rescue policy; its first-call replay truncation is
# disabled above so the complete cold boot remains available in game.omr.
eval [string range $rescue_source [string first {proc oxygen_controller} $rescue_source] end]
proc full_game_input {} {
    foreach row {6 7 8} {keymatrixup $row 255}
    set n $::tick
    if {$n<120} {return}
    if {$n==120 && $::game_mode==1} {keymatrixdown 6 64; return}
    if {$n==122 && ($::game_difficulty&64)} {keymatrixdown 6 128; return}
    if {$n==124 && ($::game_difficulty&128)} {keymatrixdown 7 1; return}
    if {$n==126} {keymatrixdown 6 32; return}
    if {$n<127} {return}
    if {!$::game_started} {
        if {[debug read memory 0xC080]!=$::game_mode} {fail_video full-game-selection}
        if {([debug read memory 0xC420]&192)!=$::game_difficulty} {fail_video full-game-difficulty}
        set ::game_started 1
        puts $::events "\{\"kind\":\"game-start\",\"tick\":$n,\"time\":[machine_info time]\}"
    }
    if {$::game_controller eq "rescue"} {oxygen_controller; return}
    if {[debug read memory 0xC0A3]} {
        if {!$::game_restarted} {
            keymatrixdown 6 32
            set ::game_restarted 1
        }
        return
    }
    set py [debug read memory 0xC0E1]
    set oxygen [debug read memory 0xC0E6]
    set ty [expr {$oxygen==64 ? 20 : 13}]
    if {$ty<$py} {keymatrixdown 8 32}
    if {$ty>$py} {keymatrixdown 8 64}
}
debug set_bp $::core_F5B8 {$::recording} {full_game_input}
# Save before the existing finisher closes trace channels and exits.
rename finish_video finish_game_video
proc finish_video {} {
    reverse savereplay $::out/game.omr
    finish_game_video
}
