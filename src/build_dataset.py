import csv
from pathlib import Path

landmarks = [
    # --- LUXOR & SURROUNDINGS (UPPER EGYPT) ---
    {
        "id": 1,
        "landmark_name": "Karnak Temple",
        "city": "Luxor",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, ancient history, hieroglyphics, columns, unesco, temples, open-air museum",
        "ideal_for": "history buffs, photography, solo, family",
        "typical_duration_hours": 3.5,
        "description": "The largest religious complex ever built by the ancient world, featuring the breathtaking Great Hypostyle Hall of 134 towering sandstone columns. Walking through its avenue of ram-headed sphinxes transports visitors back across 2,000 years of pharaonic engineering and divine worship."
    },
    {
        "id": 2,
        "landmark_name": "Valley of the Kings",
        "city": "Luxor",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, tombs, royal burial, ancient history, king tut, unesco, desert valley",
        "ideal_for": "history buffs, solo, couples, exploration",
        "typical_duration_hours": 3.5,
        "description": "A secluded desert canyon where pharaohs of the New Kingdom were entombed beneath the earth in elaborately decorated rock-cut tombs. The vibrant wall frescoes and hieroglyphic ceilings inside tombs like Tutankhamun and Seti I preserve vivid colors that have survived over three millennia."
    },
    {
        "id": 3,
        "landmark_name": "Luxor Temple",
        "city": "Luxor",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, night illumination, ramses ii, avenue of sphinxes, nile river, ancient history",
        "ideal_for": "couples, photography, history buffs, evening walks",
        "typical_duration_hours": 2.0,
        "description": "A majestic temple complex located directly on the East Bank of the Nile in downtown Luxor, illuminated spectacularly at night. It is famed for massive seated colossi of Ramses II, a soaring 25-meter pink granite obelisk, and the historic Avenue of Sphinxes connecting it to Karnak."
    },
    {
        "id": 4,
        "landmark_name": "Mortuary Temple of Hatshepsut",
        "city": "Luxor",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, deir el-bahari, female pharaoh, terraced architecture, cliffside, unesco",
        "ideal_for": "history buffs, photography, solo, exploration",
        "typical_duration_hours": 2.5,
        "description": "A masterpiece of ancient classical architecture rising dramatically in three terraced colonnades against the sheer limestone cliffs of Deir el-Bahari. Dedicated to Egypt's legendary female pharaoh, its painted reliefs depict divine birth and pioneering trade expeditions to the Land of Punt."
    },
    {
        "id": 5,
        "landmark_name": "Valley of the Queens & Tomb of Nefertari",
        "city": "Luxor",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, nefertari, painted tombs, ancient art, queens, unesco, exclusive",
        "ideal_for": "art enthusiasts, history buffs, luxury travelers, bucket list",
        "typical_duration_hours": 2.5,
        "description": "The sacred resting ground of New Kingdom royal wives and princes, housing the incomparable Tomb of Queen Nefertari (QV66). Regarded as the Sistine Chapel of Ancient Egypt, its exquisite wall paintings depict the beloved queen playing senet and receiving divine guidance with breathtaking color brilliance."
    },
    {
        "id": 6,
        "landmark_name": "Medinet Habu (Temple of Ramses III)",
        "city": "Luxor",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, ramses iii, sea peoples, deep carvings, fortified temple, unesco",
        "ideal_for": "history buffs, off the beaten track, photography",
        "typical_duration_hours": 2.5,
        "description": "A colossal fortified mortuary temple renowned for the best-preserved ceiling colors and deeply incised hieroglyphic reliefs in Upper Egypt. Visitors marvel at dramatic battle friezes recounting pharaonic naval victories over the enigmatic Sea Peoples and its monumental Syrian-style gateway."
    },
    {
        "id": 7,
        "landmark_name": "Colossi of Memnon",
        "city": "Luxor",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, giant statues, amenhotep iii, roadside monument, ancient wonder",
        "ideal_for": "quick stop, photography, history buffs",
        "typical_duration_hours": 1.0,
        "description": "Two gigantic 18-meter quartzite sandstone statues of Pharaoh Amenhotep III standing sentry at the entrance to his ruined mortuary temple. Ancient Greek and Roman travelers traveled from across the Mediterranean to witness the acoustic phenomena of the singing dawn colossus."
    },
    {
        "id": 8,
        "landmark_name": "Luxor West Bank Hot Air Balloon Flights",
        "city": "Luxor",
        "region": "Upper Egypt",
        "category": "Adventure / Scenic Experience",
        "tags": "hot air balloon, sunrise, panoramic view, nile valley, desert cliffs, bucket list",
        "ideal_for": "couples, adventure seekers, photographers, bucket list",
        "typical_duration_hours": 2.5,
        "description": "An awe-inspiring dawn balloon ascent drifting silently over the Valley of the Kings, Hatshepsut's terraced colonnades, and verdant sugar cane fields bordered by the Nile. Watching the golden Egyptian sunrise illuminate the Theban mountain range from a thousand feet high is truly unforgettable."
    },
    {
        "id": 9,
        "landmark_name": "Dendera Temple of Hathor",
        "city": "Qena",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, ptolemaic, hathor, blue ceiling, zodiac, cleopatra, crypts",
        "ideal_for": "history buffs, esoteric travelers, photography, day trip",
        "typical_duration_hours": 3.0,
        "description": "One of the most impeccably preserved temple complexes in Egypt, dedicated to Hathor, goddess of love and joy. Highlights include the vibrant turquoise ceiling frescoes of astronomical deities, the celebrated relief of Cleopatra VII and Caesarion, and mysterious subterranean crypts."
    },
    {
        "id": 10,
        "landmark_name": "Temple of Seti I at Abydos",
        "city": "Sohag",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, abydos, seti i, osiris, king list, finest reliefs, ancient mystery",
        "ideal_for": "serious historians, archaeology lovers, spiritual travelers",
        "typical_duration_hours": 3.5,
        "description": "Considered the spiritual epicenter of the cult of Osiris, Abydos contains the world's finest low-relief limestone carvings executed during the 19th Dynasty. It houses seven sacred chapels, the famous Abydos King List chronicling dynasties, and the enigmatic megalithic Osireion behind the sanctuary."
    },

    # --- GREATER CAIRO & GIZA ---
    {
        "id": 11,
        "landmark_name": "Pyramids of Giza & Great Sphinx",
        "city": "Giza",
        "region": "Greater Cairo",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, seven wonders, ancient history, desert, unesco, monument, camels, photography",
        "ideal_for": "family, solo, exploration, bucket list",
        "typical_duration_hours": 4.0,
        "description": "The last remaining wonder of the ancient world, including the Great Pyramid of Khufu, Khafre, Menkaure, and the enigmatic limestone Sphinx. These monumental 4,500-year-old structures stand majestically on the Giza plateau as eternal testaments to Old Kingdom civilization and astronomical precision."
    },
    {
        "id": 12,
        "landmark_name": "Khan el-Khalili",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Market / Cultural",
        "tags": "markets, street shopping, souk, spices, jewelry, street food, historic cairo, nightlife, photography",
        "ideal_for": "cultural exploration, solo, couples, shopping",
        "typical_duration_hours": 2.5,
        "description": "A vibrant medieval labyrinth established in the 14th century, filled with fragrant spices, handcrafted brass lanterns, silver jewelry, and bustling cafes like El Fishawy. It offers an intoxicating sensory immersion into Cairo's authentic trading heritage and lively street culture."
    },
    {
        "id": 13,
        "landmark_name": "The Egyptian Museum (Tahrir)",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Museum / History",
        "tags": "museum, antiquities, pharaonic, mummies, artifacts, central cairo, history",
        "ideal_for": "history buffs, solo, family, academic",
        "typical_duration_hours": 3.0,
        "description": "The historic pink-hued neoclassical palace on Tahrir Square that houses the world's most extensive collection of pharaonic antiquities. Walking through its venerable halls reveals thousands of golden sarcophagi, papyri, statues, and royal treasures spanning dynasties."
    },
    {
        "id": 14,
        "landmark_name": "Grand Egyptian Museum (GEM)",
        "city": "Giza",
        "region": "Greater Cairo",
        "category": "Museum / Modern Culture",
        "tags": "modern museum, mega project, tutankhamun, architectural marvel, world class",
        "ideal_for": "family, solo, architecture enthusiasts, luxury",
        "typical_duration_hours": 4.0,
        "description": "A monumental state-of-the-art museum complex positioned at the foot of the Giza Pyramids, designed to be the premier museum of ancient civilization on Earth. It showcases the complete 5,000-piece Tutankhamun collection together for the very first time alongside a towering hanging obelisk."
    },
    {
        "id": 15,
        "landmark_name": "National Museum of Egyptian Civilization (NMEC)",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Museum / History",
        "tags": "nmec, royal mummies, fustat, modern museum, civilization, pharaohs",
        "ideal_for": "family, history buffs, luxury travelers, educational",
        "typical_duration_hours": 3.0,
        "description": "Located in ancient Fustat, this contemporary cultural beacon chronicles Egyptian civilization from prehistoric times to the modern era. Its crowning attraction is the underground Royal Mummies Hall, where 22 ancient pharaohs and queens (including Ramses II and Hatshepsut) rest in climate-controlled crypts."
    },
    {
        "id": 16,
        "landmark_name": "Saqqara Necropolis & Step Pyramid of Djoser",
        "city": "Giza",
        "region": "Greater Cairo",
        "category": "Historical / Ancient Monument",
        "tags": "saqqara, step pyramid, imhotep, oldest stone building, serapeum, tombs, unesco",
        "ideal_for": "archaeology buffs, solo, adventurous travelers",
        "typical_duration_hours": 4.0,
        "description": "The birth ground of monumental stone architecture, dominated by the 4,700-year-old Step Pyramid engineered by the polymath Imhotep. The vast desert necropolis also features the mysterious underground Serapeum containing colossal granite bull sarcophagi and intricately carved Old Kingdom noble mastabas."
    },
    {
        "id": 17,
        "landmark_name": "Dahshur Pyramids (Bent & Red Pyramids)",
        "city": "Giza",
        "region": "Greater Cairo",
        "category": "Historical / Ancient Monument",
        "tags": "dahshur, bent pyramid, red pyramid, sneferu, uncrowded, desert, interior climb",
        "ideal_for": "adventurers, history buffs, off the beaten track",
        "typical_duration_hours": 3.0,
        "description": "A serene, crowd-free desert necropolis showcasing King Sneferu's architectural experiments that led to the first true smooth-sided pyramid on Earth. Intrepid travelers can climb deep into the interior corbelled burial chambers of both the rhomboidal Bent Pyramid and the towering rust-colored Red Pyramid."
    },
    {
        "id": 18,
        "landmark_name": "Coptic Cairo & The Hanging Church (El Muallaqa)",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Religious Heritage / History",
        "tags": "coptic christian, hanging church, holy family, babylon fortress, icons, peace",
        "ideal_for": "cultural travelers, spiritual, history buffs, families",
        "typical_duration_hours": 2.5,
        "description": "A tranquil walled enclave built over the Roman Fortress of Babylon, central to early Christian history in Egypt. It features the famous Hanging Church suspended over ancient bastions with cedar-wood vaulted ceilings, the Church of St. Sergius where the Holy Family took refuge, and the Ben Ezra Synagogue."
    },
    {
        "id": 19,
        "landmark_name": "Al-Muizz Street & Medieval Islamic Cairo",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Cultural / Architecture",
        "tags": "islamic architecture, unesco, medieval palaces, minarets, mosques, walking street",
        "ideal_for": "architecture enthusiasts, street photographers, history buffs",
        "typical_duration_hours": 3.5,
        "description": "One of the oldest streets in Cairo, containing the highest concentration of medieval architectural treasures in the Islamic world. Strolling along its pedestrian stone pavement reveals soaring Mamluk minarets, the grand complex of Sultan Qalawun, ancient city gates of Bab al-Futuh, and historic Ottoman merchant houses."
    },
    {
        "id": 20,
        "landmark_name": "Cairo Citadel & Mosque of Muhammad Ali",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Fortress / Religious Heritage",
        "tags": "medieval fortress, saladin, alabaster mosque, islamic cairo, panoramic city view, history",
        "ideal_for": "family, photography, cultural exploration",
        "typical_duration_hours": 3.0,
        "description": "A medieval Islamic fortification perched atop the Mokattam hills, commissioned by Saladin in the 12th century to defend against Crusaders. Dominating its skyline is the stunning Ottoman-style Alabaster Mosque with silver twin minarets offering sweeping vistas over the entire city of Cairo."
    },
    {
        "id": 21,
        "landmark_name": "Al-Azhar Park & Historic Cairo",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Parks / Scenic View",
        "tags": "parks, panoramic view, historic cairo, gardens, walking, sunset, dining, relaxing",
        "ideal_for": "family, couples, relaxation, photography",
        "typical_duration_hours": 2.5,
        "description": "A glorious 74-acre hilltop oasis cultivated over historic ruins, offering lush Islamic gardens, cascading fountains, and the most magnificent sunset panoramas over Cairo's skyline of minarets and the Saladin Citadel. An idyllic green sanctuary amidst the bustling capital."
    },
    {
        "id": 22,
        "landmark_name": "Baron Empain Palace (Heliopolis)",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Architecture / Heritage",
        "tags": "hindu revival, belgian baron, heliopolis, exotic architecture, restored palace",
        "ideal_for": "architecture lovers, quirky history, photography",
        "typical_duration_hours": 2.0,
        "description": "An enigmatic Hindu-Khmer revival mansion built in 1911 by Belgian industrialist and Heliopolis founder Édouard Empain. Decorated with elaborate statues of elephants, serpents, and mythological dancers inspired by Angkor Wat, the newly restored palace offers unique insight into early 20th-century Cairo glamour."
    },
    {
        "id": 23,
        "landmark_name": "Nile Felucca Sailing (Zamalek & Downtown)",
        "city": "Cairo",
        "region": "Greater Cairo",
        "category": "Relaxation / Scenic",
        "tags": "felucca, nile river, sailboat, sunset, romantic, breeze, city lights",
        "ideal_for": "couples, friends, relaxation, evening vibe",
        "typical_duration_hours": 1.5,
        "description": "A timeless Cairo tradition of boarding a traditional white-canvassed wooden felucca to glide peacefully across the Nile as the desert breeze cools the evening air. Drifting between the glittering skyline of Zamalek and Garden City provides the ultimate antidote to the capital's bustle."
    },

    # --- ALEXANDRIA & NORTH COAST (MEDITERRANEAN) ---
    {
        "id": 24,
        "landmark_name": "Qaitbay Citadel",
        "city": "Alexandria",
        "region": "Mediterranean Coast",
        "category": "Fortress / Coastal",
        "tags": "fortress, coastal, mediterranean, medieval, naval, history, sea view",
        "ideal_for": "couples, photography, family, history buffs",
        "typical_duration_hours": 2.0,
        "description": "A 15th-century defensive stronghold built directly upon the foundation ruins of the ancient Lighthouse of Alexandria (Pharos). The imposing stone bastion commands sweeping panoramic views over the Mediterranean Sea and Alexandria's picturesque Eastern Harbor."
    },
    {
        "id": 25,
        "landmark_name": "Bibliotheca Alexandrina",
        "city": "Alexandria",
        "region": "Mediterranean Coast",
        "category": "Cultural / History",
        "tags": "library, cultural, architecture, modern history, art galleries, museums, science, reading",
        "ideal_for": "intellectuals, solo, students, family",
        "typical_duration_hours": 3.0,
        "description": "A magnificent modern revival of the ancient library, boasting a striking sun-shaped granite facade carved with characters from 120 global scripts. Inside, it houses expansive reading halls, antiquities museums, a planetarium, and dynamic art galleries overlooking the Mediterranean."
    },
    {
        "id": 26,
        "landmark_name": "Catacombs of Kom El Shoqafa",
        "city": "Alexandria",
        "region": "Mediterranean Coast",
        "category": "Historical / Ancient Monument",
        "tags": "catacombs, greco-roman, burial, ancient, underground, archaeology, unique fusion",
        "ideal_for": "history buffs, exploration, solo",
        "typical_duration_hours": 2.0,
        "description": "A fascinating multi-level underground necropolis representing an extraordinary architectural and artistic fusion of ancient Egyptian, Greek, and Roman funerary traditions. Carved directly into bedrock, it features a circular staircase, banquet hall, and tombs bearing hybrid mythological reliefs."
    },
    {
        "id": 27,
        "landmark_name": "Montaza Palace & Royal Gardens",
        "city": "Alexandria",
        "region": "Mediterranean Coast",
        "category": "Royal Heritage / Coastal Park",
        "tags": "palace, royal gardens, mediterranean, florentine architecture, sea bridge, stroll",
        "ideal_for": "couples, families, photography, relaxation",
        "typical_duration_hours": 3.0,
        "description": "A lavish seaside royal retreat built on high bluffs overlooking the Mediterranean, enveloped by 150 acres of lush pine groves, date palms, and sandy coves. Famed for its Florentine and Ottoman-inspired palace towers and iconic marble bridge, it served as the summer sanctuary of Egyptian royalty."
    },
    {
        "id": 28,
        "landmark_name": "Roman Amphitheatre (Kom El Dikka)",
        "city": "Alexandria",
        "region": "Mediterranean Coast",
        "category": "Historical / Archaeological",
        "tags": "roman ruins, marble theatre, mosaic, lecture halls, downtown alexandria",
        "ideal_for": "history enthusiasts, students, solo",
        "typical_duration_hours": 1.5,
        "description": "The only Roman amphitheater discovered in Egypt, constructed in the 4th century with 13 tiers of imported white marble seating. The surrounding excavation complex contains well-preserved Byzantine university lecture halls, bathhouses, and the exquisite Villa of the Birds mosaic floor."
    },
    {
        "id": 29,
        "landmark_name": "Royal Jewelry Museum",
        "city": "Alexandria",
        "region": "Mediterranean Coast",
        "category": "Museum / Luxury Heritage",
        "tags": "royal jewelry, gold, diamonds, opulent palace, muhammad ali dynasty",
        "ideal_for": "luxury lovers, art aficionados, couples",
        "typical_duration_hours": 2.0,
        "description": "Housed within the opulent early 20th-century neo-classical villa of Princess Fatma Haider, this hidden gem displays thousands of dazzling diamond-encrusted crowns, emerald watches, gold chess sets, and jeweled medallions belonging to the royal family of Egypt."
    },
    {
        "id": 30,
        "landmark_name": "El Alamein War Museum & Memorials",
        "city": "El Alamein",
        "region": "North Coast",
        "category": "Military History / Heritage",
        "tags": "wwii, battle of el alamein, tanks, commonwealth cemetery, german memorial, history",
        "ideal_for": "military history buffs, contemplative travel, day trip",
        "typical_duration_hours": 3.5,
        "description": "The fateful battlefield where Allied and Axis armies clashed in 1942, altering the course of World War II. The comprehensive military museum exhibits restored Churchill tanks and fighter planes, complemented by solemn, beautifully kept Commonwealth, German, and Italian desert memorial cemeteries."
    },
    {
        "id": 31,
        "landmark_name": "Ageeba Beach & Cleopatra Bath",
        "city": "Marsa Matrouh",
        "region": "North Coast",
        "category": "Beaches / Nature",
        "tags": "ageeba beach, turquoise water, cliffs, cleopatra, maldives of egypt, coastal",
        "ideal_for": "beach lovers, scenic photography, relaxation, summer escape",
        "typical_duration_hours": 4.0,
        "description": "Celebrated as one of the most stunning Mediterranean beaches, Ageeba ('Miracle') features translucent electric-blue waters cradled by dramatic yellow limestone cliffs. Nearby lies Cleopatra's Bath, a natural wave-splashed rock pool where the legendary queen was said to swim."
    },

    # --- ASWAN, NUBIA & LAKE NASSER ---
    {
        "id": 32,
        "landmark_name": "Abu Simbel Temples",
        "city": "Aswan",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, colossal statues, ramses ii, lake nasser, unesco, engineering miracle",
        "ideal_for": "bucket list, couples, photography, history buffs",
        "typical_duration_hours": 3.0,
        "description": "Two monolithic rock-cut temples commissioned by Ramses II, adorned with four colossal 20-meter seated statues guarding the entrance on Lake Nasser. Masterfully relocated block-by-block by UNESCO in the 1960s to rescue them from rising Nile floodwaters, the temple is aligned with the sun twice yearly."
    },
    {
        "id": 33,
        "landmark_name": "Philae Temple",
        "city": "Aswan",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, isis, island, nile boat, unesco, mythology, romantic",
        "ideal_for": "couples, romantic, photography, history buffs",
        "typical_duration_hours": 2.5,
        "description": "An enchanting island temple sanctuary dedicated to the goddess Isis, reached exclusively by scenic motorboat across the serene waters of the Nile. Its graceful colonnades and sacred relief carvings harmonize beautifully with the tranquil river landscape and surrounding granite boulders."
    },
    {
        "id": 34,
        "landmark_name": "Nubian Village on Elephantine Island",
        "city": "Aswan",
        "region": "Upper Egypt",
        "category": "Cultural / Community",
        "tags": "nubian culture, colorful houses, nile boat, handicrafts, authentic, hospitality, music",
        "ideal_for": "cultural exploration, family, couples, photography",
        "typical_duration_hours": 3.0,
        "description": "A vibrant riverside settlement distinguished by brightly painted domed mudbrick houses, fragrant mint tea, and warm Nubian hospitality along the Nile. Exploring on foot or by felucca allows travelers to discover unique Nubian crafts, language, and centuries-old culinary traditions."
    },
    {
        "id": 35,
        "landmark_name": "Unfinished Obelisk & Northern Quarries",
        "city": "Aswan",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Engineering",
        "tags": "unfinished obelisk, granite quarry, pharaonic engineering, female pharaoh, stonework",
        "ideal_for": "engineering buffs, history enthusiasts, geology",
        "typical_duration_hours": 1.5,
        "description": "An extraordinary window into ancient quarrying techniques: a colossal 42-meter pink granite obelisk still lying half-carved in solid bedrock. Abandoned when a fatal crack appeared, it would have been the heaviest single piece of stone ever worked by human hands."
    },
    {
        "id": 36,
        "landmark_name": "Temple of Kom Ombo",
        "city": "Kom Ombo",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, ptolemaic, sobek, crocodile god, double temple, mummified crocodiles",
        "ideal_for": "nile cruisers, history buffs, families",
        "typical_duration_hours": 2.0,
        "description": "A dramatically situated dual temple perched right over a bend in the Nile, uniquely dedicated to two rival deities: Sobek the crocodile god and Haroeris the winged falcon. Adjacent is the fascinating Crocodile Museum exhibiting sacred mummified Nile reptiles discovered nearby."
    },
    {
        "id": 37,
        "landmark_name": "Temple of Edfu (Temple of Horus)",
        "city": "Edfu",
        "region": "Upper Egypt",
        "category": "Historical / Ancient Monument",
        "tags": "pharaonic, ptolemaic, horus, falcon, best preserved, towering pylon, unesco",
        "ideal_for": "history lovers, architecture buffs, nile cruisers",
        "typical_duration_hours": 2.5,
        "description": "The most intact and structurally complete cult temple surviving from ancient Egypt, buried for centuries under desert sand. Dedicated to Horus, its towering 36-meter entrance pylon and black granite falcon statues illustrate the legendary mythological duel between Horus and Seth."
    },
    {
        "id": 38,
        "landmark_name": "Aswan High Dam & Lake Nasser Viewpoint",
        "city": "Aswan",
        "region": "Upper Egypt",
        "category": "Modern Engineering / Scenic",
        "tags": "high dam, nasser, lake, engineering feat, modern history, hydropower",
        "ideal_for": "curious minds, engineering fans, scenic view",
        "typical_duration_hours": 1.5,
        "description": "An immense 20th-century engineering triumph completed in 1970 that tamed the annual Nile floods and forged Lake Nasser, one of the world's largest man-made reservoirs. The crest of the dam affords sweeping panoramic views of the colossal cobalt-blue lake stretching towards Sudan."
    },

    # --- SINAI PENINSULA & RED SEA (SHARM, DAHAB, NUWEIBA, TABA) ---
    {
        "id": 39,
        "landmark_name": "Ras Muhammad National Park",
        "city": "Sharm El-Sheikh",
        "region": "Sinai Peninsula",
        "category": "Nature / Diving",
        "tags": "diving, snorkeling, marine life, coral reefs, beaches, nature reserve, biodiversity",
        "ideal_for": "adventure, nature lovers, couples, family",
        "typical_duration_hours": 5.0,
        "description": "Located at the southern tip of Sinai where the Gulf of Suez meets Aqaba, this world-renowned marine reserve boasts dramatic drop-offs like Shark and Yolanda Reefs teeming with colorful corals, manta rays, and barracudas. Pristine desert mangroves meet translucent turquoise waters."
    },
    {
        "id": 40,
        "landmark_name": "Blue Hole & Canyon",
        "city": "Dahab",
        "region": "Sinai Peninsula",
        "category": "Nature / Diving",
        "tags": "diving, freediving, coral, adventure, bohemian, beach, nature, snorkeling",
        "ideal_for": "backpackers, thrill seekers, solo, diving enthusiasts",
        "typical_duration_hours": 4.0,
        "description": "A legendary submarine sinkhole descending down over 100 meters, famous across the world among technical divers and freedivers. Surrounded by Dahab's relaxed bohemian Bedouin cafes, visitors can snorkel along fringing coral gardens where sea turtles and parrotfish thrive."
    },
    {
        "id": 41,
        "landmark_name": "Mount Sinai & St. Catherine Monastery",
        "city": "St. Catherine",
        "region": "Sinai Peninsula",
        "category": "Adventure / Religious Heritage",
        "tags": "hiking, sunrise trek, holy mountain, unesco, pilgrimage, monastery, oldest library",
        "ideal_for": "adventure hikers, spiritual, bucket list, solo",
        "typical_duration_hours": 7.0,
        "description": "A sacred nocturnal trek up the 2,285-meter peak of Mount Sinai rewarded by an unforgettable desert sunrise over jagged granite peaks. At its base lies St. Catherine's, the world's oldest continuously operating Christian monastery housing priceless Byzantine icons and the legendary Burning Bush."
    },
    {
        "id": 42,
        "landmark_name": "Colored Canyon & Wadi Wishwashi",
        "city": "Nuweiba",
        "region": "Sinai Peninsula",
        "category": "Nature / Adventure Hike",
        "tags": "colored canyon, sandstone, hiking, geological wonder, rock scrambles, bedouin",
        "ideal_for": "adventure lovers, hikers, geology fans, photography",
        "typical_duration_hours": 5.0,
        "description": "A breathtaking narrow desert gorge carved by centuries of flash floods, revealing swirls of purple, magenta, gold, and red sandstone rock walls. Scrambling through its winding labyrinth under the guidance of local Bedouins leads to secluded natural granite pools tucked into the mountains."
    },
    {
        "id": 43,
        "landmark_name": "Ras Abu Galum & Blue Lagoon",
        "city": "Dahab",
        "region": "Sinai Peninsula",
        "category": "Nature / Eco-Retreat",
        "tags": "blue lagoon, kitesurfing, camel trek, eco camp, off grid, serene turquoise",
        "ideal_for": "backpackers, kitesurfers, digital nomads, tranquility seekers",
        "typical_duration_hours": 6.0,
        "description": "An off-grid protected desert paradise accessible only by foot, camel, or boat from Dahab. A shallow crystalline turquoise lagoon framed by raw desert mountains makes it one of the premier kitesurfing destinations on Earth, where travelers sleep in simple reed huts under starry skies."
    },
    {
        "id": 44,
        "landmark_name": "Pharaoh's Island & Citadel of Saladin",
        "city": "Taba",
        "region": "Sinai Peninsula",
        "category": "Historical / Island Fortress",
        "tags": "island fortress, saladin, crusades, gulf of aqaba, coral, sea views",
        "ideal_for": "history buffs, scuba divers, scenic photography",
        "typical_duration_hours": 3.0,
        "description": "A picturesque granite island situated in the northernmost reach of the Gulf of Aqaba, crowned by a formidable 12th-century medieval citadel built by Saladin. From its stone ramparts, visitors enjoy views across the borders of four nations: Egypt, Jordan, Israel, and Saudi Arabia."
    },

    # --- RED SEA MAINLAND RIVIERA (HURGHADA, MARSA ALAM, EL GOUNA) ---
    {
        "id": 45,
        "landmark_name": "Giftun Island & Marine Reserve",
        "city": "Hurghada",
        "region": "Red Sea Coast",
        "category": "Beaches / Marine",
        "tags": "island, sandy beach, boat trip, crystal clear water, snorkeling, swimming, water sports",
        "ideal_for": "family, relaxation, couples, beach lovers",
        "typical_duration_hours": 6.0,
        "description": "A tropical paradise island excursion featuring powdery white sandy beaches and turquoise waters reminiscent of the Maldives. Day-trippers can snorkel amongst shallow offshore reefs, spot pods of wild dolphins, and enjoy beachfront dining under shaded palapas."
    },
    {
        "id": 46,
        "landmark_name": "El Gouna Marina & Lagoons",
        "city": "El Gouna",
        "region": "Red Sea Coast",
        "category": "Luxury / Resort Life",
        "tags": "resort, yacht marina, nightlife, watersports, kitesurfing, fine dining, upscale, modern",
        "ideal_for": "couples, luxury, friends, relaxation",
        "typical_duration_hours": 4.0,
        "description": "A chic, eco-friendly Venetian-style resort town built around turquoise saltwater lagoons and an upscale marina filled with luxury yachts. Famous for world-class kitesurfing centers, award-winning international gastronomy, boutique shopping, and vibrant evening entertainment."
    },
    {
        "id": 47,
        "landmark_name": "Marsa Abu Dabbab (Sea Turtles & Dugongs)",
        "city": "Marsa Alam",
        "region": "Red Sea Coast",
        "category": "Nature / Marine Life",
        "tags": "dugong, giant sea turtles, coral bay, sandy bottom, marine biodiversity, snorkeling",
        "ideal_for": "wildlife lovers, families, divers, photographers",
        "typical_duration_hours": 5.0,
        "description": "A world-famous natural coastal bay with lush sea-grass meadows that attract gentle giant green sea turtles and the rare, elusive dugong ('sea cow'). Snorkelers can step directly off the sandy beach into calm waters to swim alongside peaceful marine animals in their wild habitat."
    },
    {
        "id": 48,
        "landmark_name": "Sataya Dolphin Reef (Fury Shoals)",
        "city": "Marsa Alam",
        "region": "Red Sea Coast",
        "category": "Nature / Marine Adventure",
        "tags": "wild dolphins, spinner dolphins, horseshoe reef, boat excursion, open ocean",
        "ideal_for": "wildlife enthusiasts, adventure seekers, bucket list",
        "typical_duration_hours": 8.0,
        "description": "A massive horseshoe-shaped offshore reef in southern Egypt that acts as a natural sanctuary for pods of hundreds of wild spinner dolphins. Snorkeling in the calm, transparent inner lagoon offers the rare, respectful privilege of swimming in harmony with curious dolphin pods."
    },
    {
        "id": 49,
        "landmark_name": "Elphinstone Reef",
        "city": "Marsa Alam",
        "region": "Red Sea Coast",
        "category": "Nature / Extreme Diving",
        "tags": "drift diving, oceanic whitetip, hammerhead sharks, sheer drop-offs, advanced dive",
        "ideal_for": "experienced scuba divers, underwater photographers, adrenaline",
        "typical_duration_hours": 4.0,
        "description": "A legendary offshore finger reef plummeting into abyss depths over 100 meters, famous globally for exhilarating drift diving with pelagic predators. Advanced divers encounter curious oceanic whitetip sharks, schools of hammerheads, and manta rays patrolling vibrant soft-coral walls."
    },
    {
        "id": 50,
        "landmark_name": "Soma Bay Kitesurfing & Thalasso Spa",
        "city": "Safaga",
        "region": "Red Sea Coast",
        "category": "Wellness / Water Sports",
        "tags": "kitesurfing, thalassotherapy, spa, luxury resort, flat water lagoon, wellness",
        "ideal_for": "wellness travelers, kitesurfers, luxury couples",
        "typical_duration_hours": 4.0,
        "description": "A self-contained scenic peninsula blessed with year-round reliable winds, sprawling flat-water kitesurfing lagoons, and one of the largest thalassotherapy wellness centers in the Middle East. It combines athletic adrenaline on the water with rejuvenating natural saltwater treatments."
    },

    # --- WESTERN DESERT & OASES (SIWA, WHITE DESERT, BAHARIYA, DAKHLA, FAYOUM) ---
    {
        "id": 51,
        "landmark_name": "Siwa Oasis & Cleopatra Spring",
        "city": "Siwa",
        "region": "Western Desert",
        "category": "Nature / Eco-Tourism",
        "tags": "desert oasis, salt lakes, eco-tourism, berber culture, hot springs, safari, stargazing",
        "ideal_for": "off the beaten track, adventure, wellness, relaxation",
        "typical_duration_hours": 8.0,
        "description": "An ethereal desert paradise near the Libyan border renowned for turquoise hypersaline salt lakes where swimmers float effortlessly, natural sulfur hot springs, and ancient mud-brick fortress ruins of Shali. It offers unmatched tranquility, date palm groves, and pristine Sahara dunes."
    },
    {
        "id": 52,
        "landmark_name": "Temple of the Oracle (Amun) at Siwa",
        "city": "Siwa",
        "region": "Western Desert",
        "category": "Historical / Ancient Mystery",
        "tags": "alexander the great, oracle, amun, berber heritage, ancient ruins, hilltop",
        "ideal_for": "history buffs, mystery seekers, photography",
        "typical_duration_hours": 2.0,
        "description": "Perched on a limestone promontory over palm groves, this 26th-Dynasty sanctuary is where Alexander the Great journeyed across the desert in 331 BC to consult the divine Oracle and was declared the son of god Amun, legitimizing his Pharaohship over Egypt."
    },
    {
        "id": 53,
        "landmark_name": "White Desert National Park",
        "city": "Farafra",
        "region": "Western Desert",
        "category": "Nature / Adventure",
        "tags": "white desert, chalk formations, safari, camping, stargazing, surreal landscape, geology",
        "ideal_for": "adventure, photography, camping, bucket list",
        "typical_duration_hours": 12.0,
        "description": "A surreal Martian-like landscape of giant brilliant white chalk rock formations sculpted by eons of desert windstorms into shapes resembling mushrooms, hawks, and icebergs. Overnight Bedouin camping under a pitch-black sky ablaze with millions of stars is an unforgettable wilderness experience."
    },
    {
        "id": 54,
        "landmark_name": "Black Desert & Crystal Mountain",
        "city": "Bahariya",
        "region": "Western Desert",
        "category": "Nature / Geology",
        "tags": "black desert, volcanic cones, crystal mountain, quartz, 4x4 safari, desert crossing",
        "ideal_for": "geologists, photographers, adventurers",
        "typical_duration_hours": 4.0,
        "description": "A dramatic landscape of dozens of dark volcanic basalt-capped hills rising from golden desert plains. En route lies Crystal Mountain, an extraordinary natural ridge formed entirely of sparkling calcite and quartz crystal caves thrust upward through tectonic forces."
    },
    {
        "id": 55,
        "landmark_name": "Al-Qasr Islamic Mudbrick Village",
        "city": "Dakhla",
        "region": "Western Desert",
        "category": "Historical / Medieval Settlement",
        "tags": "dakhla oasis, mudbrick, medieval islamic, labyrinth, cool shaded alleys, authentic",
        "ideal_for": "architectural historians, off the beaten track, cultural immersion",
        "typical_duration_hours": 3.0,
        "description": "A remarkably intact medieval mudbrick town founded in the 12th century beneath soaring pink cliffs in Dakhla Oasis. Its covered labyrinths and wooden-lintel archways carved with Quranic verses were engineered to provide cool shaded refuge from ferocious Sahara heat."
    },
    {
        "id": 56,
        "landmark_name": "Wadi Al-Hitan (Valley of the Whales)",
        "city": "Fayoum",
        "region": "Western Desert",
        "category": "Nature / Paleontological UNESCO",
        "tags": "whale fossils, basilosaurus, unesco, desert valley, evolution, eco-museum",
        "ideal_for": "science lovers, families, off the beaten track, campers",
        "typical_duration_hours": 5.0,
        "description": "A remote UNESCO World Heritage site preserving hundreds of fossilized skeletons of early amphibious prehistoric whales (Basilosaurus). These pristine fossils, exposed in sculpted sandstone valleys, provide the world's most critical scientific evidence for the evolution of land mammals into ocean giants."
    },
    {
        "id": 57,
        "landmark_name": "Tunis Pottery Village & Magic Lake",
        "city": "Fayoum",
        "region": "Western Desert",
        "category": "Cultural / Eco-Tourism",
        "tags": "pottery village, art retreat, magic lake, sand dunes, lake qarun, rural getaway",
        "ideal_for": "artists, couples, families, weekend escape from cairo",
        "typical_duration_hours": 4.0,
        "description": "A quaint, eco-friendly village overlooking Lake Qarun transformed into an artisanal ceramic hub with bougainvillea-draped mudbrick workshops. Nearby lies the secluded Magic Lake, surrounded by giant sand dunes perfect for sandboarding and watching waters that change color throughout the day."
    },

    # --- SUEZ CANAL & DELTA REGION ---
    {
        "id": 58,
        "landmark_name": "Port Said Historic Waterfront & Suez Canal Ferry",
        "city": "Port Said",
        "region": "Suez Canal",
        "category": "Maritime / Colonial Heritage",
        "tags": "suez canal, wooden colonial verandas, historic lighthouse, ferry, naval history",
        "ideal_for": "maritime enthusiasts, architecture lovers, day trip",
        "typical_duration_hours": 3.5,
        "description": "A historic port city marking the Mediterranean entrance to the Suez Canal, famous for 19th-century colonial timber verandas and the world's first reinforced concrete lighthouse. Taking the free public ferry between Africa (Port Said) and Asia (Port Fouad) offers front-row views of global container ships."
    },
    {
        "id": 59,
        "landmark_name": "Rosetta (Rashid) Historic Mansions & Nile Mouth",
        "city": "Rosetta",
        "region": "Delta Coast",
        "category": "Historical / Ottoman Architecture",
        "tags": "rosetta stone, ottoman houses, brickwork, nile river mouth, delta, quiet heritage",
        "ideal_for": "history buffs, architecture enthusiasts, quiet explorers",
        "typical_duration_hours": 3.0,
        "description": "The tranquil Delta town where the historic Rosetta Stone was discovered in 1799, unlocking ancient Egyptian hieroglyphs. It boasts the finest collection of Ottoman brick residences in Egypt outside Cairo, set where the western branch of the Nile empties into the Mediterranean."
    },
    {
        "id": 60,
        "landmark_name": "Ancient Tanis (San El-Hagar)",
        "city": "Sharkia",
        "region": "Delta",
        "category": "Archaeological / Ancient Capital",
        "tags": "tanis, 21st dynasty, royal tombs, silver pharaoh, raiders of lost ark, delta ruins",
        "ideal_for": "archaeology explorers, ancient history buffs, off-grid adventure",
        "typical_duration_hours": 3.5,
        "description": "The northern royal capital of Egypt during the 21st and 22nd Dynasties, celebrated in pop culture through Indiana Jones and the Raiders of the Lost Ark. Its sprawling archaeological mound contains the untouched intact royal tombs of the 'Silver Pharaoh' Psusennes I and immense toppled obelisks."
    }
]

def build():
    csv_path = Path(__file__).resolve().parent.parent / "data" / "egyptian_landmarks.csv"
    fieldnames = [
        "id", "landmark_name", "city", "region", "category",
        "tags", "ideal_for", "typical_duration_hours", "description"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in landmarks:
            writer.writerow(item)
    print(f"Successfully generated {len(landmarks)} landmarks in {csv_path}")

if __name__ == "__main__":
    build()
