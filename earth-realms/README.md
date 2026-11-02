# earth-realms (earthflagships + earthflora)

Two code mods for Vintage Story 1.22.x Earth worlds, kept in one folder because the build shares code between them.

- src/earthflagships: modid earthflagships. Keeps 14 flagship LoP dinosaur families in their real fossil home regions by vetoing natural spawns outside them. Inert unless the world config sets earthWorldgen=true.
- src/earthflora: modid earthflora. Keeps Floral Zones plants in their home floristic regions using a position-to-realm map drawn on the real Earth. Inert unless earthWorldgen=true.
- src/shared: C# files compiled into both projects through relative Compile links (RealmGeo.cs, FlagshipTable.cs, FloraModel.cs). Splitting the mods into separate folders would break those links, so they stay together.

Each project has its own .csproj. Set VSDir in the .csproj (or edit the HintPath) to your Vintage Story install. See CHANGES-1.1.0.md and REGIONS.md for details.

Not on ModDB (no local file shows otherwise).
