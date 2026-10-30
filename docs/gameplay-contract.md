# Original gameplay contract — issue #3

Status: static specification derived from the **byte-identical Atari 2600 listing**;
runtime trace acceptance is pending #6. Authority: SHA-256
`fbc29f4678f69ac27fe46da298c8c22f98cba2a3e5491e6b308fd9bf68d2ee43` (NTSC/4K).
Addresses below refer to that ROM, not addresses implied by Atari 800 label names.
Regenerate the listing with `make disassemble`. Address correspondence is recorded
in `references/rebuild-report.json`.

## Representation and frame ordering

All state arithmetic is unsigned 8-bit with 6502 carry/borrow behavior unless
explicitly BCD. Preserve wraparound, fractional accumulators and update order.
Canonical X/Y values below are game coordinates; they are not automatically MSX
pixels. Palette, scaling and presentation must not change collision or movement.

The main loop prepares display data at `$F00E`, draws the raster and gathers
collision results in `$F219–$F3B3`, updates audio and enemy values, advances the
PRNG when the **old** frame counter satisfies `frame & 7 == 0`, waits for RIOT
timing and VSYNC at `$F689`, then increments `$81`. It samples console/joystick
input at `$F6A7–$F716` and processes the game with the **new** frame counter.
The `$F689` address is a frame-boundary block, not simply an isolated increment.

Core processing order is: bonus-state handling; patrol/death contact; refill;
diver/enemy-shot pickup contact; player-shot hit; enemy/diver contact; player/enemy
contact; animations; death sequence or lane movement/spawning; surfacing;
player movement; player shot; oxygen drain; next display loop. Branches can exit
early. Do not reorganize these into independent simultaneous updates.

Time is specified in original update ticks. The inventory identifies NTSC, but
actual frame duration/scanline count and input-sampling alignment must be measured
in #6 before converting any tick count into seconds or mapping to MSX 50/60 Hz.

## State variables

| Address | Contract |
|---|---|
| `$80` | mode bit 0: solo / alternating players |
| `$81/$82` | frame phase / persistent PRNG seed |
| `$A2/$A3` | inactivity/color state / non-playing selection or game-over state |
| `$B7` | active player 0/1 |
| `$B8–$BA` | six-digit BCD score, most significant byte first |
| `$BB/$BC/$BD/$BE` | reserve lives / successful full groups / difficulty wave / divers aboard |
| `$BF–$C5` | saved second player's seven bytes corresponding to `$B8–$BE` |
| `$C6/$E1` | player X/Y |
| `$C7–$CA` | diver or hostile-shot X in each of four lanes |
| `$CF–$D1` | fractional movement accumulators |
| `$D6/$D7` | player facing / facing latched for active player shot |
| `$D9–$DC` | per-lane animation/type/direction/diver flags |
| `$E6/$E7` | oxygen / player-shot X (zero means inactive) |
| `$E8/$E9` | special-state flags / death counter |
| `$F6/$F8` | patrol X / surface collision latch snapshot |

`$E8=1` is initial/refill processing. Normal running clears bit 0. Full rescue
sets `$E8=6` (a **state value**, not bit 6); bit 1 selects the bonus branch.
After bonus, `$E8=1`. Death recovery ORs bit 0 into the existing value.
Do not reinterpret these as mutually exclusive new enums without preserving flags.

## Startup, reset, modes and controls

Cold entry `$F000` clears state through `$FA`, initializes seed `$82=1`, and
enters the loop. Game reset at `$F6E0` calls `$FB54`, which clears `$A2–$FA`
while preserving the frame counter and PRNG. Reset is not a new random seed.
Reset sets player `(X,Y)=($4C,$0D)`, three reserve submarines and initial refill.
In alternating mode the other player's reserve field initially holds four so
the switch/decrement path yields the appropriate first turn.

Select at `$F6EC` toggles `$80 & 1`, resets the game state, displays game number
1/2 through the score field, sets `$A3=$FF`, and loads held-select counter 30.
It decrements that counter on the next 30 updates and toggles on the following
update: 31 updates between repeated selections while held.
Mode switching and reset must be mapped to MSX controls, with mappings documented.
Both original difficulty settings must remain independently selectable per player.

`$84` contains active-low up/down/left/right in bits 0/1/2/3. Updates execute
**up, down, left, right**, so opposing held directions must retain this ordering
and its boundary effects. There is no diagonal normalization. Fire is a sampled
held level, not a debounced press edge. The correct joystick port follows `$B7`.
Evidence: `$F6C0–$F716`, `$FA94–$FAD2`.

Player movement is one canonical unit per admitted tick. Up decrements Y when
Y >= `$0E`; down increments while Y < `$6C`. Left sets facing `$08` even when
blocked and decrements X when X >= `$16`; right clears facing and increments
while X < `$86`. Thus normal X bounds are `$15..$86`, Y `$0D..$6C`.
Do not silently round the lower X bound to `$16`.

## Firing and oxygen

At `$FAD2–$FB35`, a new shot is admitted only when no player shot is active,
fire is held and Y >= `$12`. It latches the facing and initializes X from player
X + 8. The shot is moved in that same update. Its base displacement is +5 or -5;
the selected player's A difficulty adds -2 or +2 respectively, giving magnitude
3 instead of B's 5. This changes the time until another shot can exist; there is
no separate arbitrary autofire cooldown. A shot is cleared when its unsigned
position is >= `$A0`. Preserve ADC carry propagation through these instructions.

At `$FB37–$FB4D`, oxygen decreases once when Y >= `$14` and `frame & 31 == 0`.
Oxygen starts/fills to `$40` (64). Therefore shots and oxygen use different Y
thresholds. Decrement reaching zero starts death counter `$17`. Alarm state is
derived during HUD processing near `$F43F–$F47E`; the shot audio is suppressed
below oxygen `$11`. Do not infer a rounded real-time duration from the manual's
eight-second alarm description.

At `$FFB4`, refill increments oxygen on even frame phases, sets sound registers,
and returns carry set only when oxygen >= `$40`. Initial/refill-state processing
gates player controls until this completion; it regenerates lanes and clears the
active shot before dropping refill bit 0. This helper is also used for partial
surfacing. A full oxygen submarine can wait at the surface with no divers.

## Surfacing, rescue and bonus

Surfacing checks run **before** movement at `$FA62–$FA94`. At Y=`$0D`, when
oxygen is not already `$40`:

- No divers: start death counter `$17`.
- Six divers: set `$E8=6` and enter the bonus path next tick.
- One to five: invoke refill, block movement until completion, remove one diver,
  increment difficulty wave `$BD`, silence both channels, then allow movement.

Bonus at `$F71D–$F7A6` first consumes remaining oxygen on even phases, awarding
the current enemy BCD value for each consumed unit. When oxygen is zero, process
one diver on `frame & 15 == 0`. Each diver yields 50 points repeated
`min(successful_groups,19)+1` times: 50..1000. After all six have been processed,
increment successful groups `$BC`, then increment `$BD` **once** only if its
unsigned value is less than the new `$BC`; do not replace this with a maximum
operation (the values differ after wave-byte wrap). Clear lane
positions, and set refill state 1. No normal player update runs during bonus.

## Enemies, divers, patrol and randomness

Four lane arrays are visited from lane 3 down to lane 0. The repeat masks and
animation tables are part of the original contract, not a free choice of spawn
counts. At `$F983–$F994`, derive three speed inputs from 8-bit wave arithmetic:
`(wave+6)>>1`, `wave+6`, `wave+16`; `$FB84` splits their nibbles into integer
movement and low-nibble fractional accumulators. Carry adds the occasional extra
unit. These feed normal diver, enemy and hostile-shot movement respectively.

Enemy motion/spawning at `$F99E–$FA62` preserves bit-3 direction, masked wrap
tests `$A0/$D8`, type alternation, seed-derived direction, original repeat-mask
table `$FEFC[wave & 7]`, spawn bases `$A8/$D7`, lane flags and diver/shot delays.
Do not replace these with uniformly random spawn intervals or a monotonically
increasing speed formula. The complete instruction-level behavior of this block
is the reference for the Z80 port, including carry and shared temporaries.

At `$FEDB`, perform three iterations: compute
`feedback = bit7(((seed << 3) & 255) XOR seed)` and set
`seed = ((seed << 1) | feedback) & 255`. The regular call occurs once per eight
old-frame phases. Other code reads that seed without automatically advancing it.
Preserve startup, reset and phase behavior when replaying inputs.

The patrol begins after at least two successful full groups (`$F7A6`), moving
left when the frame mask permits: every four ticks for groups 2/3/4 and every two
for 5 and above. The index is capped at six and the lookup base is `$F7ED`, two
bytes before the displayed `$F7EF` data label; its zero mask is unreachable through
this path. Contact consumes the latched surface collision
and initiates death even during refill. Bonus handling branches before patrol
processing; do not independently move it during bonus.

## Collision contract and priority

Do **not** replace hardware collisions with generic bounding boxes or the MSX
sprite collision flag. Reproduce occupancy of the original player, missile,
repeated enemies and diver/shot ball, including animation, reflection, clipping,
HMOVE/position offsets, lane raster windows and the exact latch-clear boundaries.
The original kernel `$F219–$F3B3` and its data tables define those masks.

TIA read/write registers share addresses. In the listing, misleading write names
on **reads** at `$F390–$F3B3` mean:

| Read address / bit | Actual collision | Stored result |
|---|---|---|
| `$02`, bit 6 | CXP0FB: player P0 vs ball | `$B6` lane |
| `$00`, bit 7 | CXM0P: player missile M0 vs enemy P1 | `$B4` lane |
| `$03`, bit 6 | CXP1FB: enemy P1 vs ball | `$B0[lane]` |
| `$07`, bit 7 | CXPPMM: player P0 vs enemy P1 | `$B5` lane |

Latches clear before the lane's drawing window; collisions overwrite shared lane
results while iterating 3→0. Surface patrol collision is saved in `$F8` separately.
The port's canonical collision backend must preserve this selection and phase.

Resolution `$F7F6–$F8BC` is ordered: ball/player contact (hostile-shot type kills;
otherwise pick up if fewer than six); valid active missile/enemy hit (X in
`$08..$98`); enemy/ball contact (diver hurry-up behavior); player/enemy contact.
Player/enemy contact both starts death **and awards enemy points**, then modifies
the affected repeat mask. Preserve this behavior instead of “fixing” it.

## Score, lives, death and alternating players

`$FB9D` adds BCD with carry through `$BA,$B9,$B8`, saturates overflow to 999999
and increments the non-playing state. Every 10000-point crossing can add one
reserve, capped at six. Enemy value is `10 * min(successful_groups+2,9)` points
(with original byte arithmetic), calculated from `$F633` before event handling.
Track wave and successful groups separately: partial surfacing changes wave
without increasing the successful-group-based point value.

Death counter `$E9=$17` runs at `$F910–$F980`, decrementing only on frame phases
divisible by four. It suppresses player shots, runs explosion audio, clears oxygen
in the later phase, resets lane positions and player position, removes one diver
if present, clears relevant lane flags, and re-enters refill. Preserve the phase
of the 23 decrements, not an approximate fixed millisecond animation.

`$FCCD` calls `$FFDA`, which swaps all **seven** active/saved bytes
`$B8–$BE` ↔ `$BF–$C5` and toggles `$B7`. If the newly active reserve count is zero,
it swaps back once, then decrements the selected reserve count. This also handles
solo mode through the empty saved-player state. `$FFDA` is a player-state swap, not a generic
score routine. Game-over occurs only after the original reserve/other-player
checks. Game-over/selection `$A3` prevents normal controls, maintains attract
processing and never serves as an implicit reset of the PRNG/frame phase.

Nonzero `$A3` decrements each tick while skipping zero. During that state, when
the low score digit is zero, `frame & 127 == 0` and mode bit 0 is set, `$F654`
swaps player score/state for the attract display. The inactivity counter `$A2`
advances on frame-counter rollover; any joystick direction activity detected in
SWCHA resets it. Preserve these phase effects independently of normal controls.

## Trace acceptance scenarios for #6

Each fixture must record reset/seed/RAM policy, input phase, reference settings,
tick boundaries and expected first state divergence. Static extraction is not a
passing runtime fixture. Cover at least:

| IDs | Required cases |
|---|---|
| INIT-01..03 | cold start vs reset; seed/frame persistence; held-select repeat |
| INPUT-01..04 | all bounds; diagonals; opposing directions at bounds; facing reversal |
| FIRE-01..04 | B vs A for each player; held fire; firing threshold; same-tick move/exit |
| O2-01..04 | Y 19/20 boundary; phase 31/0 drain; alarm region; zero with surface/contact |
| RESCUE-01..05 | surface with 0/1/5/6 divers; full oxygen with no divers |
| BONUS-01..04 | oxygen score; diver phase; point caps; refill/controls transition |
| ENEMY-01..04 | all lane/type/direction/wave masks; fractional carry; wrap/spawn; hurry-up |
| COLL-01..06 | latch windows, repeated shapes/clipping, simultaneous lanes, pickup vs shot, missile vs player hit priority, patrol during refill |
| SCORE-01..04 | BCD carry, 10000 boundary, six-reserve cap, 999999 overflow |
| DEATH-01..03 | all four initial phases, diver penalty, final life/game-over |
| MODE-01..03 | alternate players, exhausted player skip, seven-field state persistence |

Remaining validation: exact raster-derived collision masks and coordinate mapping
must be captured/checked in #6/#7/#8; measured timing in #6/#14; full natural-game
acceptance in #15. The source algorithm and required cases above are binding even
where no runtime trace has been captured yet. Any disagreement is resolved against
the original 2600 ROM, never by silently adopting the Atari 800 adaptation.
