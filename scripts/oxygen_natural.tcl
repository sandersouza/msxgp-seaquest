# Device-only feedback: never write canonical game RAM. Each tick still samples
# SNSMAT/PSG and runs the complete paced native collision/input/graphics workload.
set rescue_goal 1
set rescue_previous_divers 0
set oxygen_controller_started 0
set rescue_phase partial
proc oxygen_controller {} {
    if {!$::oxygen_controller_started} {
        reverse truncatereplay
        set ::oxygen_controller_started 1
        puts $::timings "\{\"kind\":\"controller\",\"time\":[machine_info time]\}"
    }
    set px [debug read memory 0xC0C6]
    set py [debug read memory 0xC0E1]
    set divers [debug read memory 0xC0BE]
    set oxygen [debug read memory 0xC0E6]
    set special [debug read memory 0xC0E8]
    set death [debug read memory 0xC0E9]
    if {$py==13 && $divers<$::rescue_previous_divers && !$death && $special==0} {
        set ::rescue_goal 6
        set ::rescue_phase deplete
    }
    set ::rescue_previous_divers $divers
    keymatrixup 6 255
    keymatrixup 8 255
    if {[debug read memory 0xC0A3]} {keymatrixdown 6 32; return}
    if {$death && $::rescue_phase eq "deplete"} {set ::rescue_phase full}
    if {$special || $death} {keymatrixdown 8 65; return}
    set tx $px
    set ty 100
    if {$::rescue_phase eq "deplete"} {
        set ty 20
    } elseif {$divers >= $::rescue_goal || ($divers>0 && $oxygen<20)} {
        # At oxygen64 the original deliberately does not rescue. Stay submerged
        # until an actual drain, then ascend using device input.
        set ty [expr {$oxygen==64 ? 20 : 13}]
    } else {
        set best 10000
        for {set lane 0} {$lane<4} {incr lane} {
            set ball [debug read memory [expr {0xC0C7+$lane}]]
            set flags [debug read memory [expr {0xC0D9+$lane}]]
            if {$ball<15 || $ball>145 || ($flags&4)} {continue}
            set target_y [expr {32+24*(3-$lane)}]
            set cost [expr {abs($target_y-$py)+abs($ball-$px)}]
            if {$cost<$best} {set best $cost; set tx $ball; set ty $target_y}
        }
    }
    set keys 1
    if {$ty<$py} {set keys [expr {$keys|32}]}
    if {$ty>$py} {set keys [expr {$keys|64}]}
    if {$tx<$px-2} {set keys [expr {$keys|16}]}
    if {$tx>$px+2} {set keys [expr {$keys|128}]}
    keymatrixdown 8 $keys
}
