# earthflagships 1.1.0 (staged only, 2026-11-01) [SUPERSEDED 2026-11-01: Mods has earthflagships-1.1.0.zip, 8,972 B, mtime 2026-11-01 19:27]

Rows added (15, 80 total): allosauridae cryolophosaurus (Antarctica), australovenator (Australia), maip (South America); iguanodontia muttaburrasaurus, leaellynasaura (Australia), trinisaura (Antarctica); ankylosauria minmi (Australia); plateosauridae glacialisaurus (Antarctica); dromaeosauridae imperobator (Antarctica); macronaria savannasaurus (Australia), isisaurus (India), paralititan (North Africa); diplodocoidea amargasaurus (South America); abelisauridae masiakasaurus (Madagascar, existing block); oviraptorosauria gigantoraptor (Central Asia).

Boxes added: Australia [-44,-10] x [112,154]; Antarctica [-90,-60] x [-180,180].
Families added (8): allosauridae, iguanodontia, ankylosauria, plateosauridae, dromaeosauridae, macronaria, diplodocoidea, oviraptorosauria; config bool per family, default true.

FIX (behavior change for the original 6 families too): the 1.0.0 gate compared Code.Path to the bare family code, but runtime.db shows resolved codes like abelisauridae-carnotaurus-adult-male (no entity has Path == family), so 1.0.0 never matched. 1.1.0 uses FlagshipTable.FamilyOfCodePath (path == family or starts with family + "-"). Original families will now actually veto. Revert that one line in EarthFlagshipsModSystem.cs if undesired.

Tests: 722 passed, 0 failed (was 144). Added: per-genus allow/veto/no-op/switch-off, 8 forms each (adult/baby m/f, nest x3, egg), box corners, fail-open for all other variants of new families, code-path derivation. Run with the six original pack zips as modsDir (Mods folder now holds the gapfill Abeli, so the stock "pack present" check fails there).
Zip: staging\earthflagships-1.1.0.zip (modinfo.json, EarthFlagships.dll). Not installed.
