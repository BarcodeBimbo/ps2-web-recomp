# Splice pillar: CC-2 photo theming (added)

Authority: media/reference-command-center-2.png

## Status vs prior splice work

Prior corner-by-corner splice focused on **elements** (globe, brand, feed, agents, talk, overview, timeline).
Shell was marked "Mostly" without a dedicated **theming grade**.

This pillar is now in scope: match the photo's *overall theming approach*, not only widgets.

## Photo theming fingerprint (sampled)

| Trait | What the photo does | Inject target |
|-------|---------------------|---------------|
| Void | Near-black navy at edges (~#020817–#050d16), not flat #000 or solid cyan | Layered void + vignette |
| Content wells | Slightly lifted navy panels (~#001020–#091D35) over void | Glass panels over nebula |
| Accent | Electric cyan / ice (~#00D4FF / #4AD1F1), bloomed | Token cyan + soft drop-shadows |
| Glows | Soft radial blooms + animated wash — never flat cyan fills | .jcc-nebula, particle field, panel inset glows |
| Dark spots | Multiple uneven dark pockets (vignette + panel wells + globe core) — not one solid slab | Multi-stop gradients + nebula holes |
| Lighting | HUD bloom on chrome/text; mesh self-lit; dim inactive rows | Brightness/opacity hierarchy |
| Borders | Thin cool cyan hairlines (
gba(0,212,255,~0.18–0.28)) | Existing panel borders; verify no yellow |
| Grade | Cool blue-cyan grade; avoid warm yellow top-bar / purple-wash drift | No yellow header; purple only on agent accents |

## Mismatch risks (current inject)

1. Flat / single-slab backgrounds where photo has **layered void + panel wells + dark spots**
2. Over-bright solid cyan fills instead of **soft animated glows**
3. Uniform panel fill (missing local dark pockets / vignette)
4. Full-app chrome still partially stock (plan/build) — breaks unison grade
5. Accidental warm amber/yellow in header tools (must stay cool)

## Related

Full button/panel/window/icon inventory + God-missed flags: [`SPLICE-ELEMENT-INVENTORY-CC2.md`](./SPLICE-ELEMENT-INVENTORY-CC2.md)

## Work items

- [ ] Re-sample tokens.css against photo means (void / panel / accent / talk)
- [ ] Verify .jcc-nebula + particles read as photo glow treatment
- [ ] Audit dark-spot layering across rail, grid, footer
- [ ] Full-app chrome grade (editor/sidebar/status) vs HUD unison
- [x] God confirmed: photo colors incl. amber where present; live Cursor data in slots
- [ ] Apply tokens + stamp feed/agents/timeline from Cursor (in progress)
- [ ] No package until God signs theming + element audit
