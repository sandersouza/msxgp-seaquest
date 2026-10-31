# MSX HUD font refinement — follow-up to #13

The owner requested complete OXYGEN letters and score digits drawn on the MSX
pixel grid, similar to the original style with balanced strokes. This is an
explicit adaptation of these two text fields, rather than a claim that their
glyph pixels remain identical to the Atari. Original source state, blanking,
player colours, life/diver/logo assets, gauge geometry and alarm logic remain.

Score uses8x8ink in12x8cells with uniform four-pixel spacing and even stems;
0/1/8 are horizontally symmetric. Source blank codeA remains blank. OXYGEN has
complete6x7ink inside the existing six8x8label tiles, including its bottom row.
The original reference model is untouched; the MSX display oracle applies the
authored font specification only to these two rectangles.

Allocation stays171top/127bottom tiles,31colour classes,7168bytes of HUD RAM and
131072-byte ASCII16 ROM on standard MSX1/64KiB RAM/16KiB VRAM. P0font records are
85..189(count105); P1records190..250(count61) include padding244 and all six
scratch tiles245..250. Three unused uniform-role classes preserve the fixed
303-byte logical palette format; compact records now use125bytes. No native
assembly or simulation code changes. Packed HUD data is4349bytes.

Independent read-only review decoded all100score-pair vectors and six oxygen
tiles from generated HUD data and confirmed the literal masks, record ordering,
prewarm bounds, scratch isolation and unchanged source/alarm references.

`make presentation-check` passes on standard-speed NTSC C-BIOS_MSX1/openMSX21.0,
64KiB RAM/16KiB VRAM. Python3.14.7 and pinned sjasmplus1.24.0/d379eeac are unchanged.

| Check | Result |
|---|---|
| Native/source/pixel integration |39,328cases;59,110cycles max, same as baseline |
| Paced dense frame |240frames;57,190busy/1,732commit max; no skips |
| Focused score/oxygen/font/palette/ripple/sprites |1,129cases;24-byte triple-glyph update exercised |
| Continuous boundaries/exits |183x112=20,496source updates,2,745RGB/spriteframes; zero skips/visible commits |
| Forced rebase |20,496updates/180rebases;2,745RGB/spriteframes; zero skips |
| Prepared token240 across next epoch |70,272updates/139rebases/9,723READY1exposures;5,490RGB/spriteframes; zero skips |
| Attract maximum |58,691busy/9,654commit, down from59,583/10,324 on the same source seeds |
| Cold source/TIA/PSG replay |6,421updates/15,812ordered audio stores; no RAM reload or skipped frame;49,181busy max |
| Ordered audio contract |7,982ticks/34,692stores,44observed sites |
| Host/synthetic checks |52host tests pass; original-free local CI passes with one optional py65 skip in systemPython |

Timed ROM SHA256:
`958f554c81a8ccae0a8f14fe434308cbed16662e5c02cd95f97672da23d1cd84`.
Controls/playtest ROM SHA256:
`44f2d5ea2276db4719b6b488b76afc13b9e23a5c5b6cb1263f1b0f3e470561d4`.
The111,264continuous updates/10,980RGBframes use unchanged scenario generation
and byte-identical source seeds to the initial delivery baseline. Fixed-bank
padding grows from117 to373bytes; source-bank padding stays0. Active-picture
VRAM spacing remains29cycles. There are no native assembly/state changes.

The first full pass exposed blank codeA in the new oracle; the target cartridge
already preserved the blank. The oracle/regression were corrected and the whole
command rerun successfully, including all30blank-code fixtures. The raw source
HUD/alarm model was never altered. Summaries alongside this file identify each
accepted run; the old delivery metrics remain separate in the parent directory.

Reproduce serially with local original inputs and pinned tools:

```sh
make presentation-check
.venv/bin/python -B -m unittest discover -s tests
bash scripts/ci.sh
```

Work is isolated in the managedhud-fonts worktree to avoid the active ISSUE14
checkout and the owner's visible openMSX session. Original inputs, comparison
images, extracted data and cartridges stay local/ignored. PAL/source cadence
and full-game/physical release acceptance remain #14/#15.
