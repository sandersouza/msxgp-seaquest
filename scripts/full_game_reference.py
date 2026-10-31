"""Acceptance predicates for uninterrupted, device-only complete-game traces."""

RECORD_BYTES = 2303


def coverage(data, timing, mode, difficulty, controller='exhaust'):
    if not data or len(data) % RECORD_BYTES:
        raise ValueError('incomplete full-game records')
    starts = [row['tick'] for row in timing if row['kind']=='game-start']
    if len(starts)!=1 or not 0<=starts[0]<len(data)//RECORD_BYTES:
        raise ValueError('missing unique configured game start')
    states = [data[i+2052:i+RECORD_BYTES] for i in range(0,len(data),RECORD_BYTES)][starts[0]:]
    switches = [data[i+2049]&192 for i in range(starts[0]*RECORD_BYTES,len(data),RECORD_BYTES)]
    if any(s[0x80]!=mode for s in states) or set(switches)!={difficulty}:
        raise ValueError('configured mode/difficulty changed during full game')
    pairs = list(zip(states,states[1:]))
    over = [i+1 for i,(a,b) in enumerate(pairs) if not a[0xa3] and b[0xa3] and not b[0xe9]]
    restarts = [i+1 for i,(a,b) in enumerate(pairs) if a[0xa3] and not b[0xa3] and b[0xbb]==3
                and b[0xc2]==(4 if mode else 0)]
    players = sorted({s[0xb7] for s in states if not s[0xa3]})
    result = dict(mode=mode,difficulty=difficulty,controller=controller,
                  configured_start_tick=starts[0],configured_updates=len(states),
                  gameovers=len(over),restarts=len(restarts),active_players=players,
                  deaths=sum(not a[0xe9] and bool(b[0xe9]) for a,b in pairs),
                  death_player_switches=sum(a[0xb7]!=b[0xb7] and a[0xe9]==1 and not b[0xe9]
                                           and not a[0xa3] and not b[0xa3] for a,b in pairs),
                  pickups=sum(b[0xbe]>a[0xbe] and not a[0xe9] and not b[0xe9] for a,b in pairs),
                  partial_rescues=sum(b[0xbe]+1==a[0xbe] and a[0xe1]==13 and not a[0xe9]
                                      and b[0xbd]==(a[0xbd]+1)&255 for a,b in pairs),
                  full_rescues=sum(b[0xe8]==6 and a[0xe8]!=6 for a,b in pairs),
                  oxygen_depletions=sum(a[0xe6]==1 and b[0xe6]==0 and b[0xe9]==23
                                        and a[0xe1]==20 for a,b in pairs),
                  alarm_updates=sum(bool(s[0xf9]) for s in states),
                  ram_reloads_after_boot=0,physical_hardware=False)
    if controller=='exhaust':
        if not over or not restarts or not any(r>over[0] for r in restarts) or not result['deaths']:
            raise ValueError(f'incomplete natural full game: {result}')
        if players!=list(range(mode+1)) or (mode and not result['death_player_switches']):
            raise ValueError(f'incomplete active-player exhaustion: {result}')
        result['first_gameover_tick'] = starts[0]+over[0]
        result['first_restart_tick'] = starts[0]+next(r for r in restarts if r>over[0])
    elif not all(result[k] for k in ('pickups','partial_rescues','oxygen_depletions','alarm_updates')):
        raise ValueError(f'incomplete natural rescue route: {result}')
    return result
