# Score, progression and alternating players — issue #12

The translated original F5B8→F00E instructions already implement this scope.
This delivery adds explicit acceptance probes and a specialized native score block.
The running cartridge remains the source-ordered native
Z80 implementation, with original raster contacts and F44F→F473 alarm acquired
before every integrated update. HUD composition and sound playback belong to #13.

## Arithmetic and event order

- FB9D clears incoming carry, adds decimal through BA/B9/B8 and saturates at
  999999. Overflow increments A3 with byte wrap. A valid 10000-point crossing
  adds one reserve when fewer than six remain; overflow does not add a reserve.
- F633 computes enemy/oxygen value before processing events:
  `10 * min((groups + 2) & 255, 9)`. Groups254/255 therefore produce0/10.
  The modulo operation precedes the cap; a mathematical unbounded addition
  would change the original late-game behavior.
- Missile hits and body contacts both award the computed enemy value. A
  simultaneous missile/body contact can award twice, even when death starts.
  The resulting reserve/overflow state participates in subsequent source logic.
- During a full rescue, each oxygen unit awards the enemy value on the original
  even new phases. Each diver pays `50 * (min(groups,19)+1)` on phases divisible
  by16. The source executes repeated50-point additions, preserving intermediate
  lives, score saturation and A3 effects. Death/contact handling follows its
  original priority relative to the bonus early exit.
- Full-bonus completion increments groups with byte wrap, then increments wave
  only when its unsigned value is lower than the new group value. Partial rescue
  increments wave alone. Wave arithmetic, fractional carries and spawn tables
  retain original byte semantics, including values beyond the usual early game.
- Patrol unlocks at groups2. Its new-phase mask is3 for groups2..4 and1 for
  groups5..255; the table index is capped at6. Bonus skips this branch. Patrol
  contact can interrupt refill as specified in the collision contract.

## Players, death and restart

FFDA swaps all seven bytes B8..BE with BF..C5 and toggles B7. FCCD first swaps,
swaps back if the selected player has no reserves, then decrements the selected
reserve. Death completion enters game over only after checking both reserve
counts. Score, reserves, successful groups, wave and divers remain per player;
the two difficulty switches remain independent and survive Reset/Select.

The death counter decrements on new phases divisible by4. Reset, selection,
attract swapping and restart retain source frame/seed persistence and event
order. Game-over A3 is not a new high-level reset command. The natural acceptance
controller uses keyboard input to exhaust both players and restart; seeded chains
provide distinct seven-byte player states and late-game/full-bonus coverage.

## Independent evidence and reproduction

```
make progression-contract
make render-progression-bench
make progression-natural
make native-contract
make collision-contract
make oxygen-contract
bash scripts/ci.sh
```

The direct contract checks every valid low-byte BCD operand pair with both
incoming carries, high-digit boundaries and all reserve counts. Its expectations
execute the original binary on py65 and additionally check decimal arithmetic
and exact seven-field swaps independently. Score checks include returned A/X/Y,
carry and NMOS N/Z, including79+01→80/N=1. Native ADD/ADC/DAA retain the source
low/middle/high additions and direct carry through stores. A middle addition
without carry leaves the high byte unchanged and cannot award a life because
the new middle byte is nonzero; its identity high store is omitted. At terminal score, the guarded path
increments A3 once per original scoring call and returns the same registers and
flags; no observer can read the dead intermediate score stores under DI. All
other score operations retain the source additions, ordered writes and reserve checks.
Integrated records use original-mask
contacts, the source HUD alarm and BIOS-sampled device input, then compare all251
shadow bytes with the original CPU. Continuous seeded chains reload game RAM
only at each scenario start.

The omitted-display audit executes original F00E→F5B8 and then F5B8→F00E while
tracking display writes read before a core overwrite. It identifies B0..B6/F8/F9
as the sampled inputs. This is dynamic CPU dependency evidence; the Atari TIA
oracle independently certifies contact geometry. The cold-boot replay checks
both TIA occupancy and the original CPU each tick, without reloading game RAM.

The renderer sweep includes the oxygen regression, all progression fixtures and
full-density clipped scenes during capped diver/oxygen payouts and score overflow.
It checks pixels, source state, preceding visible VRAM, port spacing and pacing.
Exact results, ROM hashes, versions and review are in `references/progression/`.
Raw records, source-derived data, cartridges and replay dumps stay ignored under
outputs/. Public CI uses synthetic inputs only. NTSC emulator evidence does not
establish PAL, full-game or physical MSX acceptance.

Negative control (must fail; then rerun the normal contract):

```
SEAQUEST_PROGRESSION_CORRUPT=1 make progression-contract
```

This changes the running Z80 score byte BA after execution; the independent
expected record cannot receive the corrupted native result.
