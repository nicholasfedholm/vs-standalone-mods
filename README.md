# Vintage Story standalone mods

Source for our standalone Vintage Story 1.22.7 mods. JSON-only mods are just assets plus modinfo.json. Code mods are C# projects; edit the VS install path in each .csproj. Compiled binaries and archives are not committed.

| folder | modid | author (per modinfo) | what it does | ModDB status |
|---|---|---|---|---|
| sharpscale | sharpscale | Nick | Replaces the nearest-neighbour upscale used when render scale is below 1 with a bilinear plus contrast-adaptive sharpening pass, or an FSR 1 (EASU + RCAS) pass. | not on ModDB |
| earthtpbridge | earthtpbridge | Nick | In Andris Earth worlds only: stands Terra Prety's patches down and adds Terra Prety landform detail on top of Earth's real-world heights, faded out near rivers and coasts. | not on ModDB |
| earth-realms/src/earthflagships | earthflagships | Muse | Earth worlds only: keeps 14 flagship LoP dinosaur families (incl. | not on ModDB |
| earth-realms/src/earthflora | earthflora | Muse | Earth worlds only: keeps Floral Zones plants in their home floristic regions. | not on ModDB |
| oregonebony | oregonebony | Muse | Adds an ebony tree generation row for cool, very wet temperate forest (the Pacific Northwest envelope) in Earth worlds. | not on ModDB |
| fotsagapfill | fotsagapfill | Nick (generated) | Adds missing Stone Age fauna as variants of installed Fauna of the Stone Age packs (plus one own-domain entity derived from the vanilla bear). | not on ModDB |
| seeddropratefloracompat | seeddropratefloracompat | Muse (for Nick) | Applies Seed Drop Rate multipliers (crops x3, tree seeds x5) to Floral Zones crops and tree leaves. | not on ModDB |
| ecomachinafloralzonescompat | ecomachinafloralzones | local compat patch | Lets Eco Machina's foliage treatment apply to Floral Zones Cape Region trees and the small Circumboreal white spruce, which generate with -placed- leaves that Eco Machina skips. | not on ModDB |
| terrapretydefault | terrapretydefault | Nick | Adds a 'Terra Prety' playstyle that sorts first in the new-world list. | not on ModDB |
| knapsterchannelguard | knapsterchannelguard | Nick | Keeps Knapster's network message ids in sync when its admin menu fails to start on the server. | not on ModDB |

Compat and add-on mods here are not the upstream mods: fotsagapfill credits Fauna of the Stone Age (Tenth Architect), ecomachinafloralzonescompat credits Eco Machina (Svend Richter) and Floral Zones (Flishster, Tenth Architect), seeddropratefloracompat patches Seed Drop Rate and Floral Zones, knapsterchannelguard guards Knapster (ApacheTech Solutions).
