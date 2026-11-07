# Controls, compatibility and cheats

The top toolbar provides **Start**, **Menu**, **Touch controls**, **Capture mouse**, **Remap controls** and **Volume**. It remains available in fullscreen. On touch devices, mouse capture is hidden and the toolbar scrolls horizontally when necessary. Mouse capture requires a direct click/tap in a browser that supports pointer lock.

**Remap controls** stores bindings for the current game URL. The mouse settings include independent **Invert horizontal** and **Invert vertical** switches. If a game turns right when you move left, switch horizontal inversion; games differ in how they interpret the right stick. Mouse settings and keyboard mappings are input translations to the game's PS2 controller. They do not replace controller artwork drawn inside the game.

When remapping, press the desired keyboard key. To bind a mouse button, click the instruction message using that button. Settings buttons and dropdowns do not become accidental bindings. Escape cancels capture. Controls are neutral while settings are open, and held keys/touches clear on focus loss.

## If a game does not start or load

Use the top **Start** button to send Start independently of keyboard remapping. This is distinct from the initial loading screen's Start button, which launches the emulator.

**Menu → Download diagnostics** saves the current runtime output, browser capabilities, renderer, disc errors and performance information. An unavailable disc stream or a stopped worker should now produce an error/reload state. A genuine game/CPU/VU emulation loop can still require a title-specific fix.

For missing geometry, compare **Menu → Renderer: software** and **Menu → VU: reference**. The reference VU option bypasses compiled VU programs and enables the existing exact interpreter mode, which can be much slower. Both options reload the game after saving its card. This is a differential diagnosis tool, not a guarantee that the reference implementation is correct for every title.

## Cheats

Open **Menu → Cheats**. Paste codes or load a `.pnach`/text file, then select **Save codes**. Enable each patch using its checkbox. Codes are saved for the current game URL but start disabled each session. This requires rebuilding the browser game with the current runtime.

Supported live codes are `patch=1` PNACH EE direct writes: `byte`, `short`, `word`, `double`, and extended direct-write types 0/1/2. Only aligned addresses inside the 32 MiB EE RAM range are accepted, with a maximum of 128 patches. Boot-only `patch=0` codes, codes for other CPUs, conditions, pointer chains and other extended operations are rejected. Code modifications to statically recompiled functions require a rebuild; changing their guest bytes does not change compiled host instructions. Use codes for the exact game region and revision.

Example syntax only, not a working game cheat:

```text
[Example RAM patch]
patch=1,EE,00123450,word,00000001
```

Cheat updates pass through a bounded command queue and are applied by the emulation thread. Disabling a patch stops future writes; it does not reconstruct the RAM value that the game had before the cheat ran. **Disable all** stops all enabled patches. Reloading resets the runtime cheat slots.

## Cutscenes

**Menu → Skip cutscene** sends one button press. Select Start, Cross, Circle or Triangle in the adjacent selector; the choice is saved for this game. A scene must support that input. There is no universal safe patch that makes every PS2 cutscene skippable.
