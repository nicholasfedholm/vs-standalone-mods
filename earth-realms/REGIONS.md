# REGIONS.md: realm boxes on the real Earth + flagship variant table

Foundation data for `earthflora` (Part A) and `earthflagships` (Part B).
Built 2026-10-30 for Nick's Quarter Earth world (100,352 x 50,176).

## Conventions

- Coordinates are geographic: lat in degrees, +N / -S; lon in degrees, +E / -W.
- Block to lat/lon uses the Earth mod's own mapping (earth-compat\audit_earth.md, EarthCoords.cs):
  `lon = bx * 360 / MapSizeX - 180`, `lat = 90 - bz * 180 / MapSizeZ`.
  Inverse: `bx = (lon + 180) * MapSizeX / 360`, `bz = (90 - lat) * MapSizeZ / 180`.
- A box is `[latMin, latMax] x [lonMin, lonMax]`, inclusive on all sides.
- Realms are evaluated in the priority order listed; the FIRST matching realm wins.
  A position matching no box (open ocean, far polar) has NO realm: under Biomes semantics an
  unassigned position grows/spawns nothing realm-locked, which is the intended behavior at sea.
- Boxes are generous (whole subcontinents), per the design brief: travel reward, not dig-site simulation.
- Realm sector logic mirrors the Biomes author's own list (ModConfig\biomes.json, type "blended"):
  northern realms run west to east around the hemisphere (pacific nearctic, atlantic nearctic,
  atlantic palearctic, central palearctic, eastern palearctic, pacific palearctic); the southern
  list is pacific neotropic, atlantic neotropic, atlantic afrotropic, eastern afrotropic,
  australasian, oceanic. "Pacific/atlantic/eastern" names the ocean-facing longitude sector
  of that landmass.

## Part A: the 12 realms as lat/lon boxes

### Northern realms

| # | Realm | Boxes (lat x lon) | Basis |
|---|-------|-------------------|-------|
| 1 | pacific nearctic | [20, 72] x [-168, -100] | Western North America: Alaska, western Canada, western US, Pacific-facing side of the continent west of ~100W. |
| 2 | atlantic nearctic | [20, 72] x [-100, -45]; [58, 72] x [-58, -20] | Eastern North America from the plains to the Atlantic, plus the Greenland box for its southern coasts. |
| 3 | atlantic palearctic | [36, 71] x [-10, 45] | Europe to the Urals and the Caspian's west shore; the Atlantic-facing end of Eurasia. |
| 4 | central palearctic | [40, 72] x [45, 100]; [28, 40] x [60, 100] | The Siberian/Central Asian steppe belt, plus the Central Asian highland box (Pamir/Tibet fringe). |
| 5 | eastern palearctic | [18, 55] x [100, 142]; [55, 72] x [100, 140] | China, Korea, Japan and the Indochina north; second box is east-central Siberia above it. |
| 6 | pacific palearctic | [42, 72] x [140, 180] | Russian Far East, Kamchatka, Sakhalin: the Pacific-facing end of Eurasia. |

### Southern realms

| # | Realm | Boxes (lat x lon) | Basis |
|---|-------|-------------------|-------|
| 7 | pacific neotropic | [-57, 12] x [-82, -66]; [12, 20] x [-105, -100] | South America's Pacific slope and Andes, west of ~66W, plus Mexico's Pacific slope below the nearctic line (lat 20). |
| 8 | atlantic neotropic | [9, 28] x [-86, -60]; [7, 24] x [-100, -60]; [-57, 12] x [-66, -34] | Caribbean box first (so the islands stay neotropic despite their latitude), then Central America and Mexico east of 100W up to lat 24 (covers Mexico City and the whole Yucatan), then South America east of the Andes to Brazil's Atlantic bulge. Mexico needs its own boxes: without them everything west of 92W and south of lat 20 fell in no realm at all, the same hole the Cape check caught in Africa. |
| 9 | atlantic afrotropic | [-35, 37] x [-18, 22] | West and central Africa: the Atlantic-facing half, Sahara west, Congo basin, Angola, and the Cape (the atlantic/eastern split in southern Africa is the lon 22 line, Atlantic side versus Indian side, so this box runs to the Cape at lat -35). |
| 10 | eastern afrotropic | [-35, 15] x [22, 52]; [15, 33] x [22, 38]; [-26, -12] x [43, 51] | East and southern Africa plus the Egypt/Sudan Red Sea box, and Madagascar as its own box. |
| 11 | australasian | [-44, -10] x [112, 154]; [-9, 1] x [130, 148]; [-47, -34] x [166, 179] | Australia (Tasmania included), New Guinea, New Zealand. |
| 12 | oceanic | [-25, 25] x [155, 180]; [-25, 25] x [-180, -135]; [18, 23] x [-162, -154]; [5, 19] x [117, 127]; [-9, 6] x [95, 131]; [-2, 2] x [-92, -89] | The Pacific island world: Melanesia/Polynesia bands, Hawaii, the Philippines, the Indonesian archipelago, Galapagos. Mainland SE Asia stays eastern palearctic; only the islands are oceanic. |

Priority order (first match wins): atlantic neotropic (Caribbean box), oceanic (Philippines box),
australasian (New Guinea box), then the table order 1 to 12. The three named exceptions exist only
where boxes overlap: the Caribbean above 20N, the Philippines at 18-19N, and New Guinea's west end
inside the Indonesian archipelago box.

Worked spot checks (Quarter size, MapSizeX 100352, MapSizeZ 50176):
- Omaha (41.25N, -95.9): atlantic nearctic. London (51.5N, -0.1): atlantic palearctic.
- Beijing (39.9N, 116.4): eastern palearctic. Tokyo (35.7N, 139.7): eastern palearctic.
- Sydney (-33.9, 151.2): australasian. Auckland (-36.8, 174.8): australasian.
- Manaus (-3.1, -60.0): atlantic neotropic. Santiago (-33.4, -70.7): pacific neotropic.
- Mexico City (19.4, -99.1): atlantic neotropic (Central America / Mexico box). Havana (23.1, -82.4): atlantic neotropic (Caribbean box).
- Lagos (6.5N, 3.4): atlantic afrotropic. Nairobi (-1.3, 36.8): eastern afrotropic.
- Cape Town (-33.9, 18.4): atlantic afrotropic (the Cape sits west of the lon 22 split; a first draft of these boxes stopped the atlantic box at lat -18 and left the Cape in no realm at all, which the offline cross-check caught).
- Antananarivo (-18.9, 47.5): eastern afrotropic (Madagascar box). Honolulu (21.3, -157.8): oceanic.
- Mid-Pacific (0, -150): oceanic. South Pole: no realm (intended).

## Part B: flagship region boxes

Flagship homes are named subcontinent boxes (a variant may hold several). Overlaps are fine here:
a spawn is in-region if it falls in ANY of the variant's boxes.

| Box name | Lat x Lon | Used for |
|----------|-----------|----------|
| North America | [15, 72] x [-168, -52]; [58, 72] x [-58, -20] | NA ceratopsids and tyrannosaurids (Greenland box included for completeness). |
| Central Asia | [33, 50] x [55, 115] | Mongolian and Uzbek genera. |
| East Asia | [20, 54] x [100, 142] | Chinese genera. |
| Southeast Asia | [8, 30] x [92, 110] | Laos/Thailand genera. |
| Europe | [36, 60] x [-10, 32] | English, Iberian, French, Hungarian genera. |
| North Africa | [10, 37] x [-18, 36] | Moroccan, Algerian, Egyptian and Nigerien (Saharan) genera. |
| East Africa | [-12, 12] x [25, 52] | Tanzanian genera. |
| Madagascar | [-26, -12] x [43, 51] | Malagasy abelisaurids. |
| India | [8, 36] x [68, 90] | Indian abelisaurids. |
| South America | [-57, 12] x [-82, -34] | Argentinian and Brazilian genera. |

## Part B: flagship variant-to-region table

Variants extracted from the installed packs' entity JSONs (variantgroup "type", 2026-10-30).
Entity code is the family file's `code`; the gating key is (entity code, type variant).

### ceratopsidae (lop-ceratops 1.2.1), 15 variants
| Variant | Region | Fossil basis |
|---------|--------|--------------|
| triceratops | North America | Hell Creek and Lance, Montana/Wyoming. |
| pentaceratops | North America | Kirtland Formation, New Mexico. |
| styracosaurus | North America | Dinosaur Park Formation, Alberta. |
| centrosaurus | North America | Dinosaur Park Formation, Alberta. |
| nasutoceratops | North America | Kaiparowits Formation, Utah. |
| pachyrhinosaurus | North America | Alberta and Alaska (Prince Creek). |
| torosaurus | North America | Montana, Wyoming, Utah, Texas. |
| xenoceratops | North America | Foremost Formation, Alberta. |
| machairoceratops | North America | Wahweap Formation, Utah. |
| nedoceratops | North America | Hell Creek, Wyoming. |
| sinoceratops | East Asia | Wangshi Group, Shandong, China: the one Chinese ceratopsid in the pack. |
| regaliceratops | North America | St. Mary River Formation, Alberta. |
| leptoceratops | North America | Montana, Wyoming, Alberta. |
| protoceratops | Central Asia | Djadokhta Formation, Gobi, Mongolia. |
| ajkaceratops | Europe | Iharkut, Hungary: Europe's ceratopsian. |

### tyrannosauridae (LoP-Tyranno 1.4.2-batch0), 12 variants
| Variant | Region | Fossil basis |
|---------|--------|--------------|
| tyrannosaurus | North America | Hell Creek and the western interior of North America. |
| tarbosaurus | Central Asia | Nemegt Formation, Mongolia: Asia's apex tyrannosaur. |
| nanuqsaurus | North America | Prince Creek Formation, arctic Alaska. |
| albertosaurus | North America | Horseshoe Canyon Formation, Alberta. |
| gorgosaurus | North America | Dinosaur Park, Alberta, into Montana. |
| alioramus | Central Asia | Nemegt Formation, Mongolia. |
| qianzhousaurus | East Asia | Nanxiong Formation, Jiangxi, China. |
| zhuchengtyrannus | East Asia | Wangshi Group, Shandong, China. |
| bistahieversor | North America | Kirtland Formation, New Mexico. |
| thanatotheristes | North America | Foremost Formation, Alberta. |
| teratophoneus | North America | Kaiparowits Formation, Utah. |
| dynamoterror | North America | Menefee Formation, New Mexico. |

### spinosauridae (LoP-Spino 1.1.0), 6 variants
| Variant | Region | Fossil basis |
|---------|--------|--------------|
| spinosaurus | North Africa | Kem Kem (Morocco) and Bahariya (Egypt). |
| oxalaia | South America | Alcântara Formation, NE Brazil. |
| suchomimus | North Africa | Elrhaz Formation, Niger: Saharan Africa. |
| baryonyx | Europe | Wealden, Surrey, England; also Iberia. |
| ichthyovenator | Southeast Asia | Savannakhet Basin, Laos. |
| irritator | South America | Romualdo Formation, NE Brazil. |

### abelisauridae (LoP-Abeli 1.0.11), 18 variants
| Variant | Region | Fossil basis |
|---------|--------|--------------|
| pycnonemosaurus | South America | Cachoeira do Bom Jardim, Mato Grosso, Brazil. |
| ekrixinatosaurus | South America | Candeleros Formation, Neuquén, Argentina. |
| carnotaurus | South America | La Colonia Formation, Chubut, Argentina. |
| chenanisaurus | North Africa | Phosphates of the Gannour, Morocco. |
| rajasaurus | India | Lameta Formation, Gujarat, India. |
| skorpiovenator | South America | Huincul Formation, Neuquén, Argentina. |
| majungasaurus | Madagascar | Maevarano Formation, Madagascar. |
| abelisaurus | South America | Anacleto Formation, Río Negro, Argentina. |
| xenotarsosaurus | South America | Bajo Barreal Formation, Chubut, Argentina. |
| aucasaurus | South America | Anacleto Formation, Neuquén, Argentina. |
| rahiolisaurus | India | Lameta Formation, Gujarat, India. |
| arcovenator | Europe | Provence, southern France. |
| rugops | North Africa | Echkar Formation, Niger. |
| dahalokely | Madagascar | Diego Basin, northern Madagascar. |
| ilokelesia | South America | Huincul Formation, Neuquén, Argentina. |
| viavenator | South America | Bajo de la Carpa Formation, Neuquén, Argentina. |
| tarascosaurus | Europe | Southern France. |
| thanos | South America | São José do Rio Preto Formation, Brazil. |

### carcharodontosauridae (LoP-Carchar 1.0.7), 12 variants
| Variant | Region | Fossil basis |
|---------|--------|--------------|
| giganotosaurus | South America | Candeleros Formation, Neuquén, Argentina. |
| carcharodontosaurus | North Africa | Kem Kem (Morocco) and Algeria. |
| mapusaurus | South America | Huincul Formation, Neuquén, Argentina. |
| tyrannotitan | South America | Cerro Barcino Formation, Chubut, Argentina. |
| tameryraptor | North Africa | Bahariya Formation, Egypt. |
| veterupristisaurus | East Africa | Tendaguru Formation, Tanzania. |
| ulughbegsaurus | Central Asia | Bissekty Formation, Uzbekistan. |
| siamraptor | Southeast Asia | Khok Kruat Formation, Thailand. |
| shaochilong | East Asia | Ulansuhai Formation, Inner Mongolia, China. |
| concavenator | Europe | Las Hoyas, Cuenca, Spain. |
| lusovenator | Europe | Lourinhã Formation, Portugal. |
| lajasvenator | South America | Mulichinco Formation, Neuquén, Argentina. |

### herrerasauridae (LoP-Herrerasauridae 1.0.0-v1), 2 variants
| Variant | Region | Fossil basis |
|---------|--------|--------------|
| herrerasaurus | South America | Ischigualasto Formation, Argentina. |
| staurikosaurus | South America | Santa Maria Formation, Brazil. |

Total: 65 variants across 6 families. Deviations from the prompt's starter table, all forced by
the packs' actual rosters: Sinoceratops/Protoceratops/Ajkaceratops take Ceratopsidae outside North
America; Suchomimus sits in the Sahara (North Africa box reaches Niger) and Ichthyovenator adds
Southeast Asia to Spinosauridae; Abelisauridae adds Madagascar and Europe (France); 
Carcharodontosauridae adds East Africa, Central Asia, Southeast Asia, East Asia and Europe.
The starter's spirit (per-variant, subcontinent boxes) is unchanged.
