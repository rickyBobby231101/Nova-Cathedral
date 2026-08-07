#!/usr/bin/env python3
"""
Nova Herbal Knowledge System
==============================
Seeds Nova's memory with plant medicine knowledge drawn from:
  - Ellen Evert Hopman: Secret Medicines from Your Garden
  - Ellen Evert Hopman: A Druid's Herbal for the Sacred Earth Year
  - Ellen Evert Hopman: A Druid's Herbal of Sacred Tree Medicine
  - Traditional Western herbalism & apothecary practice
  - Holistic health principles (mind-body-spirit)
  - Wildcrafting, preparation methods, and plant lore

Also provides HerbalKnowledgePlugin for live query answering inside Nova.

Usage (standalone seeder):
    python3 nova_herbal_knowledge.py
    python3 nova_herbal_knowledge.py --db ~/Cathedral/nova_memory.db
    python3 nova_herbal_knowledge.py --query "yarrow"

Usage (Nova plugin):
    from nova_herbal_knowledge import HerbalKnowledgePlugin
    system.plugins.register(HerbalKnowledgePlugin(system))
"""

import sqlite3
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

# ═══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE CORPUS
# ═══════════════════════════════════════════════════════════════════════════════

# ── Individual plants ─────────────────────────────────────────────────────────

PLANT_KNOWLEDGE: List[Dict[str, Any]] = [

    {
        "common_name": "Yarrow",
        "latin_name": "Achillea millefolium",
        "family": "Asteraceae",
        "parts_used": ["flowers", "leaves", "stems"],
        "actions": ["hemostatic", "vulnerary", "diaphoretic", "antipyretic",
                    "anti-inflammatory", "bitter tonic", "antispasmodic"],
        "constituents": ["achillin", "achillicin", "flavonoids", "tannins",
                         "volatile oils", "salicylic acid", "alkaloids"],
        "traditional_uses": (
            "One of the most ancient wound herbs — Achilles legendarily used it on soldiers. "
            "Hopman describes yarrow as a premier first-aid plant from the garden, staunching "
            "bleeding on contact when fresh leaves are applied directly to cuts and scrapes. "
            "Internally it breaks fevers by opening pores and promoting perspiration. "
            "Strong tea drunk hot at the onset of a cold or flu drives fever out through the "
            "skin. It tones the blood vessels and is used for heavy menstruation, nosebleeds, "
            "and hemorrhoids. Bitter properties aid digestion and stimulate bile flow. "
            "In Druid tradition yarrow is sacred, used in ritual for protection and courage."
        ),
        "preparations": {
            "fresh_poultice": "Bruise fresh leaves and apply directly to wounds to stop bleeding.",
            "standard_tea": "1 tsp dried herb per cup boiling water, steep 10–15 min covered. "
                            "Drink hot to break fevers; cool for digestion.",
            "tincture": "1:5 ratio in 40% alcohol. 2–4 ml three times daily.",
            "oil_infusion": "Pack fresh wilted flowers into oil (olive or sunflower), "
                            "infuse 4–6 weeks in sun; use topically for wounds and skin.",
            "bath_herb": "Strong decoction added to bath water for skin conditions and fever."
        },
        "cautions": (
            "Avoid in pregnancy (uterine stimulant). May cause contact dermatitis "
            "in people sensitive to the Asteraceae family. Avoid in ragweed allergy."
        ),
        "hopman_notes": (
            "Hopman places yarrow among the essential garden medicines — 'no home should "
            "be without it.' She emphasizes its dual nature as both blood-mover and "
            "blood-stopper depending on preparation and need."
        ),
        "season": "Flowers June–September; harvest in full bloom.",
        "growing": "Spreads vigorously; full sun, well-drained soil. Drought tolerant.",
        "druid_lore": "Yarrow stalks were used in I Ching divination. Sacred to the sun.",
        "tags": ["wound", "fever", "bleeding", "cold", "flu", "garden", "first-aid", "sacred"]
    },

    {
        "common_name": "Plantain",
        "latin_name": "Plantago major / Plantago lanceolata",
        "family": "Plantaginaceae",
        "parts_used": ["leaves", "seeds"],
        "actions": ["vulnerary", "drawing", "anti-inflammatory", "expectorant",
                    "demulcent", "antimicrobial", "astringent"],
        "constituents": ["aucubin", "allantoin", "mucilage", "tannins",
                         "flavonoids", "silica", "vitamins C and K"],
        "traditional_uses": (
            "Called 'white man's footprint' by Native Americans — it followed European "
            "settlers everywhere they walked. Hopman calls it the most important first-aid "
            "plant you can find in any yard or roadside. Chewing a leaf and applying it "
            "to a bee sting, spider bite, or splinter draws out venom and foreign matter "
            "within minutes. Internally it soothes irritated mucous membranes throughout "
            "the respiratory and digestive tracts. Excellent for coughs, bronchitis, "
            "irritable bowel, and urinary irritation. Seeds (psyllium) are well-known "
            "bulk laxative and cholesterol support."
        ),
        "preparations": {
            "chew_and_apply": "Chew a fresh leaf to a pulp, apply to insect stings, "
                              "bites, splinters, or minor wounds. Replace every 20 min.",
            "tea": "2 tsp dried leaf per cup, steep 15 min. For coughs, bronchitis, "
                   "bladder irritation, digestive upset.",
            "tincture": "1:5 in 25% alcohol. 2–4 ml three times daily.",
            "syrup": "Strong decoction reduced with honey; for coughs and sore throats.",
            "seed_mucilage": "Soak 1 tsp seeds in water overnight; drink gel and liquid "
                             "for bowel regularity and cholesterol."
        },
        "cautions": "Very safe. Avoid psyllium seeds if swallowing is impaired.",
        "hopman_notes": (
            "Hopman notes that plantain is so universally available it is almost overlooked. "
            "She urges foragers to learn it first — 'it grows in every crack in the sidewalk "
            "and is one of the most healing plants on Earth.'"
        ),
        "season": "Available nearly year-round; harvest young leaves spring through fall.",
        "growing": "Grows in lawns, paths, disturbed soil. No cultivation needed.",
        "druid_lore": "One of nine sacred herbs in the Anglo-Saxon Nine Herbs Charm.",
        "tags": ["wound", "bite", "sting", "cough", "digestive", "first-aid", "weed", "drawing"]
    },

    {
        "common_name": "Elderberry & Elder Flower",
        "latin_name": "Sambucus nigra",
        "family": "Adoxaceae",
        "parts_used": ["berries", "flowers", "inner bark", "leaves (topical)"],
        "actions": ["antiviral", "immune-stimulating", "diaphoretic",
                    "expectorant", "anti-inflammatory", "antioxidant"],
        "constituents": ["anthocyanins", "flavonoids (quercetin, rutin)", "sambunigrin (raw berries)",
                         "vitamins A B C", "volatile oils in flowers"],
        "traditional_uses": (
            "Hopman describes elder as a complete medicine cabinet in one tree. The flowers "
            "are used hot in tea to break fevers and treat colds; they are among the finest "
            "diaphoretics available. The berries, cooked, are powerful antivirals shown to "
            "shorten influenza duration significantly. Inner bark, used cautiously, purges "
            "and moves lymph. In Druid and Celtic tradition elder is a threshold tree — "
            "the home of the Elder Mother, a spirit demanding respect before any harvest. "
            "One must always ask permission before cutting elder. Leaf poultices reduce "
            "bruising and swelling."
        ),
        "preparations": {
            "elderberry_syrup": (
                "Simmer 1 cup dried berries in 3 cups water 45 min until reduced by half. "
                "Mash, strain, add 1 cup raw honey when cooled to 100°F. Add cinnamon, "
                "clove, ginger to taste. 1 tbsp daily preventive; 1 tbsp every 2–3 hours acute."
            ),
            "flower_tea": "1–2 tsp dried flowers per cup boiling water, steep 10 min covered. "
                          "Drink hot for fever and colds; cool for hay fever and skin.",
            "flower_tincture": "1:5 in 40% alcohol. 2–5 ml three times daily.",
            "elderberry_tincture": "1:4 in 25% alcohol. 4–6 ml three times daily when ill.",
            "flower_infused_oil": "For skin softening and sun-damaged skin.",
            "oxymel": "Flowers or berries in equal parts raw apple cider vinegar and honey, "
                      "steeped 4 weeks; strain. For coughs and respiratory congestion."
        },
        "cautions": (
            "Raw/unripe berries, bark, and leaves contain sambunigrin — always cook berries. "
            "Do not use elderberry if on immunosuppressant drugs. Ask the Elder Mother "
            "before harvesting — take only what you need."
        ),
        "hopman_notes": (
            "Hopman is emphatic: elder is sacred. She describes the Druidic protocol of "
            "speaking aloud to the Elder Mother, explaining your need, and leaving an offering "
            "of gratitude. 'The tree gives medicine freely when approached with reverence.'"
        ),
        "season": "Flowers May–June; berries August–October.",
        "growing": "Moist rich soil, sun to part shade. Grows vigorously; can become a large shrub or small tree.",
        "druid_lore": "Elder is one of the Ogham trees (Ruis). Associated with endings, transformation, the Crone aspect, and the spirit world threshold.",
        "tags": ["immune", "antiviral", "flu", "fever", "cold", "sacred", "berry", "flower", "druid"]
    },

    {
        "common_name": "Calendula",
        "latin_name": "Calendula officinalis",
        "family": "Asteraceae",
        "parts_used": ["flowers (fresh and dried)"],
        "actions": ["vulnerary", "anti-inflammatory", "antifungal", "antimicrobial",
                    "lymphatic", "emmenagogue", "astringent", "demulcent"],
        "constituents": ["triterpenoid saponins", "flavonoids", "carotenoids",
                         "volatile oils", "polysaccharides", "resins"],
        "traditional_uses": (
            "Hopman calls calendula 'the great healer of skin.' It is unsurpassed for any "
            "wound, burn, rash, fungal infection, or inflamed skin. It moves the lymphatic "
            "system, making it valuable for swollen glands, breast lumps, and pelvic congestion. "
            "Internally it soothes gastric ulcers, inflammatory bowel conditions, and "
            "supports liver function. The tea is a gentle menstrual regulator. Its bright "
            "orange flowers correspond to the sun in herbal energetics."
        ),
        "preparations": {
            "infused_oil": (
                "Fill a jar with fresh wilted (never wet) flowers; cover completely with "
                "olive oil. Infuse 4–6 weeks in a sunny window or 48–72 hrs in a slow cooker "
                "on lowest setting. Strain. Use as base for salves, creams."
            ),
            "salve": (
                "Melt 1 oz beeswax per cup of calendula-infused oil. Pour into tins. "
                "For wounds, burns, rashes, dry skin, nipple soreness, diaper rash."
            ),
            "tea": "2 tsp dried petals per cup, steep 15 min. For digestive inflammation, "
                   "liver support, menstrual regulation.",
            "tincture": "1:5 in 60% alcohol (high resin extraction). 2–4 ml three times daily.",
            "succus": "Freshly pressed juice applied directly to wounds and fungal infections.",
            "wash": "Strong tea used to wash infected wounds, fungal skin conditions, conjunctivitis."
        },
        "cautions": "Avoid internally in pregnancy (emmenagogue). Asteraceae sensitivity may cause skin reactions.",
        "hopman_notes": (
            "Hopman highlights calendula's solar nature and its affinity for the lymph — "
            "she recommends it for any 'stuck' condition: stuck lymph, stuck digestion, "
            "stuck emotions held in the body. 'It moves what needs moving and heals what needs healing.'"
        ),
        "season": "Flowers continuously June through frost when deadheaded.",
        "growing": "Easy annual; full sun; direct sow after last frost. Self-seeds prolifically.",
        "druid_lore": "Associated with the sun, used in solar festivals and fire ceremony offerings.",
        "tags": ["skin", "wound", "fungal", "lymph", "digestive", "salve", "oil", "solar", "garden"]
    },

    {
        "common_name": "Comfrey",
        "latin_name": "Symphytum officinale",
        "family": "Boraginaceae",
        "parts_used": ["root (topical)", "leaves (topical and limited internal)"],
        "actions": ["vulnerary", "cell-proliferant", "demulcent", "anti-inflammatory",
                    "astringent", "expectorant"],
        "constituents": ["allantoin", "mucilage", "tannins", "rosmarinic acid",
                         "pyrrolizidine alkaloids (root, highest)", "calcium", "silicon"],
        "traditional_uses": (
            "Known historically as 'knitbone' — comfrey's allantoin stimulates cell division "
            "and speeds healing of fractures, sprains, and deep wounds faster than almost "
            "any other plant. Hopman details its use as a poultice for broken bones, "
            "bruises, pulled muscles, and arthritic joints. The mucilage soothes irritated "
            "mucous membranes in the lungs and gut. Root decoction was traditionally drunk "
            "for fractures and peptic ulcers, though modern herbalists restrict internal "
            "use to short courses due to pyrrolizidine alkaloid content."
        ),
        "preparations": {
            "fresh_poultice": "Blend or mash fresh leaves; apply to sprains, bruises, fractures. "
                              "Cover with cloth. Change every few hours.",
            "root_poultice": "Grate or blend fresh root. Apply to fractures and deep bruising.",
            "infused_oil": "Dried leaf or root in olive oil, 4–6 weeks. Base for bone-heal salve.",
            "salve": "Comfrey-infused oil with beeswax. Apply to fractures, sprains, arthritis, scars.",
            "dried_leaf_tea": (
                "Short-term only (2 weeks max): 1 tsp dried leaf per cup for coughs "
                "and stomach ulcers. Not for long-term or daily internal use."
            )
        },
        "cautions": (
            "Pyrrolizidine alkaloids (PAs) are hepatotoxic with prolonged internal use — "
            "internal use is best short-term and with guidance. Do NOT apply to deep puncture "
            "wounds (heals surface before depth, trapping infection). Root contains higher "
            "PAs than leaves. Avoid internally in pregnancy and liver disease."
        ),
        "hopman_notes": (
            "Hopman notes comfrey's extraordinary power and its need for respect. She details "
            "the traditional 'knitbone' poultice technique and emphasizes topical use as "
            "the primary application in modern herbalism."
        ),
        "season": "Leaves harvest spring–fall; root harvest autumn.",
        "growing": "Deep-rooted perennial; nearly impossible to eradicate once established. "
                   "Part shade to full sun; moist rich soil. Excellent compost activator.",
        "druid_lore": "Associated with Saturn and the earth element; a plant of binding and consolidation.",
        "tags": ["bone", "wound", "sprain", "fracture", "poultice", "salve", "joint", "lung"]
    },

    {
        "common_name": "St. John's Wort",
        "latin_name": "Hypericum perforatum",
        "family": "Hypericaceae",
        "parts_used": ["flowering tops (flowers, buds, and leaves in full bloom)"],
        "actions": ["antidepressant", "nervine", "anti-inflammatory", "antiviral",
                    "vulnerary", "analgesic", "antimicrobial"],
        "constituents": ["hypericin", "pseudohypericin", "hyperforin", "flavonoids",
                         "xanthones", "volatile oils", "tannins"],
        "traditional_uses": (
            "Named for the summer solstice (St. John's Day, June 24) — when its red oil "
            "is most potent. Hopman describes harvesting it at midsummer with gratitude, "
            "noting the red pigment that bleeds from bruised flowers as the plant's 'blood.' "
            "Infused in oil it turns blood-red and is the finest nervine oil for pain — "
            "applied to injured nerves, bruises, back pain, and neuralgia. Internally, "
            "the tincture and tea are well-studied antidepressants for mild to moderate "
            "depression. Antiviral against HIV, herpes, and influenza in preliminary research."
        ),
        "preparations": {
            "sun_infused_oil": (
                "Pack fresh flowers (no water on them) into a clear glass jar; cover with "
                "olive oil. Cap and set in direct sun 4–6 weeks. Oil turns deep red. "
                "Strain. Apply to bruises, nerve pain, back pain, sciatica, burns."
            ),
            "tincture": (
                "Fresh plant 1:2 in 60% alcohol — must be made fresh; dried plant loses "
                "potency. 2–4 ml three times daily for depression, nerve pain, viral infection."
            ),
            "tea": "2 tsp dried herb per cup, steep 15 min. For anxiety, mild depression, "
                   "nerve pain. Less potent than tincture.",
            "salve": "Red-infused oil with beeswax. For burns (especially sunburn), "
                     "bruises, nerve injuries.",
            "capsule": "Standardized to 0.3% hypericin; 300 mg three times daily for depression."
        },
        "cautions": (
            "Significant drug interactions — reduces efficacy of antiretrovirals, "
            "cyclosporin, warfarin, oral contraceptives, SSRIs, and digoxin. "
            "Photosensitization in fair-skinned people with high internal doses. "
            "Do not combine with pharmaceutical antidepressants without medical guidance."
        ),
        "hopman_notes": (
            "Hopman emphasizes the sacred timing of harvest — midsummer, when the plant's "
            "life force peaks. She describes the joy of red-stained fingers from harvesting "
            "and the Druidic connection between the plant's solar nature and its healing "
            "of the nervous system and spirit."
        ),
        "season": "Harvest at midsummer (June–July) when in full fresh bloom.",
        "growing": "Full sun, poor dry soil. Spreads by seed and rhizome; perennial.",
        "druid_lore": "Midsummer herb par excellence. Sacred to the sun; burned in solstice bonfires for protection. A powerful ward against malevolent spirits.",
        "tags": ["depression", "nerve", "pain", "antiviral", "oil", "midsummer", "sacred", "solar", "anxiety"]
    },

    {
        "common_name": "Lavender",
        "latin_name": "Lavandula angustifolia",
        "family": "Lamiaceae",
        "parts_used": ["flowers", "essential oil", "leaves"],
        "actions": ["nervine", "relaxant", "antimicrobial", "antifungal",
                    "carminative", "antispasmodic", "analgesic", "antidepressant"],
        "constituents": ["linalool", "linalyl acetate", "camphor", "flavonoids",
                         "tannins", "rosmarinic acid"],
        "traditional_uses": (
            "Universal calming herb. Hopman describes lavender as among the most versatile "
            "garden medicines — nervine for anxiety, insomnia, and headache; antimicrobial "
            "for wounds and skin infections; digestive carminative for gas and spasm. "
            "The essential oil applied neat to minor burns, insect bites, and tension "
            "headaches (temples) is one of the safest direct essential oil applications. "
            "Steam inhalation loosens respiratory congestion."
        ),
        "preparations": {
            "tea": "1–2 tsp dried flowers per cup, steep 10 min. For anxiety, insomnia, headache, digestive upset.",
            "essential_oil_neat": "1–2 drops applied directly to minor burns, bites, headache at temples. "
                                  "One of very few EOs safe undiluted.",
            "tincture": "1:5 in 40% alcohol. 2–4 ml at bedtime for insomnia.",
            "bath": "Handful of flowers or 10 drops essential oil in warm bath for stress and muscle tension.",
            "sachet": "Dried flowers in pillow sachet for sleep.",
            "honey_infusion": "Fresh flowers in raw honey 4 weeks; 1 tsp in tea for sore throat and calm.",
            "smudge": "Dried bundles burned for space clearing and calming atmosphere."
        },
        "cautions": "Very safe. High internal doses of essential oil are toxic — never ingest EO in quantity.",
        "hopman_notes": (
            "Hopman writes of lavender as a protector of the household in Celtic tradition — "
            "hung above doorways to keep illness and harmful spirits out. She includes it in "
            "both garden medicine and sacred ceremony."
        ),
        "season": "Harvest flowers just as first buds open, June–August.",
        "growing": "Full sun, excellent drainage, alkaline to neutral soil. Drought tolerant once established.",
        "druid_lore": "Used in purification rituals and sacred space clearing. Placed on ancestral altars.",
        "tags": ["anxiety", "sleep", "insomnia", "headache", "burn", "antimicrobial", "sacred", "garden", "nervous-system"]
    },

    {
        "common_name": "Lemon Balm",
        "latin_name": "Melissa officinalis",
        "family": "Lamiaceae",
        "parts_used": ["leaves (fresh preferred)"],
        "actions": ["nervine relaxant", "antiviral", "carminative", "antispasmodic",
                    "diaphoretic", "thyroid modulating", "antidepressant"],
        "constituents": ["rosmarinic acid", "volatile oils (citral, linalool)", "flavonoids",
                         "tannins", "caffeic acid derivatives"],
        "traditional_uses": (
            "One of the oldest documented medicinal herbs — used for over 2,000 years for "
            "anxiety and heart palpitations. Hopman describes it as ideal for children's "
            "fevers, nervous stomachs, and colic. Excellent for anxiety-driven digestive "
            "upset — the 'nervous stomach' herb. Strong antiviral, especially against "
            "herpes simplex when applied topically. Modulates thyroid (reduces TSH) which "
            "is useful in hyperthyroidism but means caution in hypothyroidism."
        ),
        "preparations": {
            "fresh_tea": "Handful of fresh leaves steeped 5 min (fresh far superior to dried). "
                         "For anxiety, digestive spasm, palpitations, insomnia, fever in children.",
            "tincture": "Fresh plant 1:2 in 40% alcohol. 2–6 ml three times daily.",
            "topical_lip_balm": "Strong tea or tincture applied to cold sores (herpes labialis) "
                                "at onset; reduces healing time.",
            "glycerite": "Fresh plant in vegetable glycerin 6 weeks — ideal for children.",
            "combined_nervine_tea": "Blend with chamomile and passionflower for anxiety and sleep.",
            "culinary": "Fresh leaves in salads, pestos, lemonade — food-level use is very safe."
        },
        "cautions": (
            "Avoid or use cautiously in hypothyroidism (Hashimoto's) due to TSH-lowering effect. "
            "Dries rapidly after harvest — use fresh or tincture immediately."
        ),
        "hopman_notes": (
            "Hopman emphasizes growing lemon balm close to the kitchen door for ready access "
            "and notes the old beekeeping tradition of rubbing hives with melissa to keep "
            "colonies calm and attract new swarms. The bees know what's good."
        ),
        "season": "Fresh leaves available spring through first frost. Best harvested before flowering.",
        "growing": "Spreads aggressively; container growing recommended. Partial shade to full sun. Self-seeds.",
        "druid_lore": "Sacred to bees and the bee goddess. Associated with the heart, joy, and Beltane.",
        "tags": ["anxiety", "digestive", "herpes", "children", "palpitations", "nervine", "antiviral", "thyroid"]
    },

    {
        "common_name": "Chamomile",
        "latin_name": "Matricaria chamomilla (German) / Chamaemelum nobile (Roman)",
        "family": "Asteraceae",
        "parts_used": ["flowers"],
        "actions": ["nervine", "antispasmodic", "anti-inflammatory", "carminative",
                    "vulnerary", "bitter", "emmenagogue (mild)", "antimicrobial"],
        "constituents": ["apigenin", "chamazulene (blue volatile oil)", "bisabolol",
                         "flavonoids", "mucilage", "tannins"],
        "traditional_uses": (
            "Among the most universally used medicinal plants worldwide. Hopman details its "
            "use for colic in babies (dilute tea), anxiety and insomnia, irritable bowel, "
            "gastric ulcers, menstrual cramps, and inflamed skin. The blue-chamazulene oil "
            "in German chamomile makes it one of the most potent anti-inflammatories in the "
            "plant world. An outstanding herb for conditions where spasm and inflammation "
            "combine — IBS, gastritis, period pain, muscle tension with anxiety."
        ),
        "preparations": {
            "tea": "2–3 tsp dried flowers per cup, steep 10–15 min covered to preserve volatile oils. "
                   "3 cups daily for digestive, anxiety, sleep, or menstrual conditions.",
            "infused_oil": "Flowers in olive oil, 4 weeks in sun. For inflamed skin, eczema, baby skin.",
            "tincture": "1:5 in 40% alcohol. 2–4 ml three times daily.",
            "steam_inhalation": "Handful of flowers in bowl of steaming water, towel over head, "
                                "inhale 10 min. For congestion and inflamed sinuses.",
            "compress": "Strong tea used as warm compress for muscle spasm, abdominal cramps.",
            "baby_tea": "Very dilute (¼ tsp per cup) for infant colic — only a few spoonfuls at a time.",
            "eye_wash": "Cooled, strained strong tea as gentle eye wash for conjunctivitis."
        },
        "cautions": "Asteraceae family allergy risk. Mild emmenagogue — large doses avoid in early pregnancy. Blood thinner interaction potential with large doses.",
        "hopman_notes": (
            "Hopman notes the apple-scent of chamomile (Matricaria from 'mother') and its "
            "particular affinity for the mother-child bond — calming anxious mothers and "
            "colicky babies alike. 'It restores peace to households.'"
        ),
        "season": "Harvest flowers when fully open with yellow centers domed, May–September.",
        "growing": "Easy annual (German) or perennial (Roman); full sun; light soil. German chamomile self-seeds abundantly.",
        "druid_lore": "Sacred to the sun in Germanic and Norse traditions. Used in purification and protection baths before ritual.",
        "tags": ["digestive", "anxiety", "sleep", "colic", "anti-inflammatory", "children", "spasm", "skin", "garden"]
    },

    {
        "common_name": "Rosemary",
        "latin_name": "Salvia rosmarinus (formerly Rosmarinus officinalis)",
        "family": "Lamiaceae",
        "parts_used": ["leaves", "flowering tops"],
        "actions": ["circulatory stimulant", "nervine tonic", "antimicrobial",
                    "antioxidant", "carminative", "antispasmodic", "rubefacient"],
        "constituents": ["rosmarinic acid", "carnosic acid", "volatile oils (1,8-cineole, camphor)",
                         "flavonoids", "diterpenoids", "tannins"],
        "traditional_uses": (
            "Hopman writes of rosemary as the herb of memory and fidelity — used at weddings "
            "and funerals alike. It powerfully stimulates circulation to the brain, improving "
            "memory and concentration. Hot rosemary tea brings circulation to the extremities "
            "in poor circulation and cold conditions. Antifungal and antimicrobial as a hair "
            "rinse for dandruff and hair loss. One of the best culinary herbs for digestive "
            "support with fatty foods. Strong antioxidant preserves foods and cells alike."
        ),
        "preparations": {
            "tea": "1 tsp dried leaves per cup, steep 10 min. For memory, circulation, "
                   "headache, digestive support.",
            "tincture": "1:5 in 45% alcohol. 2–4 ml three times daily.",
            "hair_rinse": "Strong decoction (4 tbsp per quart, simmered 20 min) cooled; "
                          "poured over hair after washing for dandruff and hair growth.",
            "infused_oil": "Culinary and topical. For muscle pain as warming massage oil.",
            "essential_oil": "Diluted 2% in carrier oil for scalp massage, muscle pain, "
                             "cognitive support (diffuse or inhale).",
            "fire_cider": "One ingredient in stimulating immune tonic vinegar.",
            "culinary": "Constant culinary use provides ongoing medicinal benefits."
        },
        "cautions": (
            "High doses may cause seizures in susceptible people. Avoid high medicinal "
            "doses in pregnancy. Essential oil not for internal use."
        ),
        "hopman_notes": (
            "Hopman connects rosemary to the Druidic veneration of memory — the ancestors, "
            "sacred genealogy, and oral tradition. She describes it burning on ancestral altars "
            "at Samhain (Halloween) to honor the dead and sharpen memory of their lives."
        ),
        "season": "Harvest year-round in mild climates; peak in summer.",
        "growing": "Mediterranean origins; full sun, perfect drainage, lean soil. Frost-tender in zones below 7.",
        "druid_lore": "Herb of remembrance, memory, and the ancestors. Burned at Samhain. Protection and purification.",
        "tags": ["memory", "circulation", "brain", "hair", "antimicrobial", "digestive", "sacred", "ancestors"]
    },

    {
        "common_name": "Nettle",
        "latin_name": "Urtica dioica",
        "family": "Urticaceae",
        "parts_used": ["young leaves and stems (spring)", "seeds", "root"],
        "actions": ["nutritive tonic", "alterative", "diuretic", "anti-inflammatory",
                    "antihistamine", "astringent", "galactagogue", "adrenal tonic"],
        "constituents": ["iron", "calcium", "magnesium", "silica", "vitamins A C K",
                         "chlorophyll", "beta-sitosterol (root)", "lectins", "flavonoids",
                         "formic acid (sting)", "serotonin (sting)"],
        "traditional_uses": (
            "Hopman calls nettle 'the most nutritious plant in the temperate world' — a "
            "complete mineral supplement in food form. Spring nettles cooked as greens provide "
            "more iron than spinach, more calcium than milk. Freeze-dried capsules are "
            "well-studied for allergic rhinitis (hay fever). Root extract is standard "
            "European treatment for benign prostatic hyperplasia. Urtication (deliberate "
            "stinging of arthritic joints) is a folk remedy that stimulates circulation "
            "and reduces joint pain. The plant teaches assertiveness — it stings those who "
            "don't approach mindfully."
        ),
        "preparations": {
            "infusion_nourishing": (
                "Hopman's nourishing herbal infusion method: 1 oz dried nettle in quart jar, "
                "fill with boiling water, cap, steep 4–8 hours or overnight. Strain. "
                "Drink 1–4 cups daily for mineral nutrition, fatigue, allergies, adrenal support."
            ),
            "cooked_greens": "Young spring leaves (gloves required harvesting) cooked like spinach — "
                             "heat destroys sting completely.",
            "tincture": "Fresh plant 1:2 in 25% alcohol. 3–5 ml three times daily.",
            "root_tincture": "Dried root 1:5 in 45% alcohol. 4–6 ml twice daily for prostate.",
            "seed_food": "Fresh green seeds sprinkled on food — adrenal tonic, energy support.",
            "freeze_dried": "Capsules for hay fever: 300 mg three times daily.",
            "hair_rinse": "Strong tea for hair strength and growth."
        },
        "cautions": (
            "Wear gloves harvesting. Diuretic — may affect diuretic medications. "
            "Root may interact with prostate medications. Avoid high doses in pregnancy."
        ),
        "hopman_notes": (
            "Hopman gives an extended teaching on nettles as the plant that demands respect "
            "and rewards those who learn to work with it. She includes the nourishing infusion "
            "method (Susun Weed's approach, which Hopman endorses) as the premier way to "
            "extract minerals for long-term use. 'Nettle builds the blood and the bones.'"
        ),
        "season": "Harvest young tops before flowering in spring. Seeds in late summer.",
        "growing": "Spreads by rhizome; moist rich soil; partial shade to sun. Contain in beds.",
        "druid_lore": "Associated with Mars and the warrior spirit. Used in protective magic. Sacred to Thor in Norse tradition.",
        "tags": ["nutrition", "mineral", "allergy", "iron", "prostate", "adrenal", "tonic", "spring", "foraging"]
    },

    {
        "common_name": "Echinacea",
        "latin_name": "Echinacea purpurea / E. angustifolia / E. pallida",
        "family": "Asteraceae",
        "parts_used": ["root (E. angustifolia, E. pallida)", "aerial parts in bloom (E. purpurea)"],
        "actions": ["immune stimulant", "immunomodulator", "anti-inflammatory",
                    "antiviral", "antibacterial", "lymphatic", "vulnerary"],
        "constituents": ["alkylamides (tingle on tongue)", "polysaccharides", "caffeic acid derivatives",
                         "glycoproteins", "flavonoids", "essential oils"],
        "traditional_uses": (
            "Native American plains tribes used echinacea as their premier medicine — for "
            "snake bite, wounds, and infections. Hopman notes its appropriateness taken at "
            "the first sign of illness rather than continuously. It stimulates white blood "
            "cell production and activity, increasing the body's response to bacterial and "
            "viral infection. The tongue tingle from fresh root or quality tincture is "
            "the marker of alkylamide content and potency. Best used short-term acutely."
        ),
        "preparations": {
            "tincture": (
                "Acute illness: 1–2 ml every 2–3 hours at first sign of infection. "
                "Reduce to 3× daily after 24 hours. Use for 7–10 days maximum, then rest. "
                "Quality tincture causes tingling, numbing sensation on tongue."
            ),
            "tea": "1 tbsp dried root or herb simmered 20 min. Less potent than tincture.",
            "glycerite": "For children: fresh E. purpurea aerial parts in vegetable glycerin.",
            "capsule": "Standardized extract for those who cannot tolerate tincture taste.",
            "topical": "Strong tea or tincture applied to wounds, skin infections, boils."
        },
        "cautions": (
            "Avoid in autoimmune conditions (lupus, MS, rheumatoid arthritis) without guidance — "
            "immune stimulation may worsen these. Asteraceae allergy risk. "
            "Long-term continuous use loses effectiveness; use acutely or cyclically."
        ),
        "hopman_notes": (
            "Hopman emphasizes respect for echinacea as a plant with deep Native American "
            "sacred history. She urges ethical wildcrafting — E. angustifolia is at risk "
            "in the wild; grow your own or source cultivated root. 'Take what you need, "
            "never more than a third, and give thanks.'"
        ),
        "season": "Root harvest autumn; aerial parts at full bloom.",
        "growing": "E. purpurea easiest in gardens; full sun; average soil. Perennial. "
                   "Flowers attract butterflies and bees.",
        "druid_lore": "Plains-origin plant; honored as a gift from indigenous peoples to the healing tradition.",
        "tags": ["immune", "cold", "flu", "infection", "antiviral", "antibacterial", "lymph", "acute"]
    },

    {
        "common_name": "Valerian",
        "latin_name": "Valeriana officinalis",
        "family": "Caprifoliaceae",
        "parts_used": ["root (fresh or freshly dried)"],
        "actions": ["sedative", "hypnotic", "antispasmodic", "anxiolytic",
                    "nervine", "analgesic", "antihypertensive"],
        "constituents": ["valerenic acid", "isovaleric acid", "valepotriates",
                         "GABA", "flavonoids", "alkaloids"],
        "traditional_uses": (
            "The Western world's primary herbal sedative for thousands of years. "
            "Hopman describes it for insomnia, anxiety, muscle tension, menstrual cramps, "
            "and high blood pressure driven by stress and nervous tension. "
            "It smells strongly of dirty socks (isovaleric acid) — those who benefit from "
            "it usually don't mind the smell. Works best when combined with passionflower "
            "and/or hops for sleep; with lemon balm and skullcap for anxiety."
        ),
        "preparations": {
            "tincture": (
                "Fresh root 1:2 in 60% alcohol — potency drops rapidly in dried root. "
                "3–5 ml at bedtime for insomnia; 2–3 ml three times daily for anxiety."
            ),
            "tea": "Not recommended — active compounds don't extract well in water and the "
                   "smell is off-putting. Tincture or capsule preferred.",
            "capsule": "Standardized 0.8% valerenic acid; 300–600 mg at bedtime.",
            "sleep_blend_tincture": "Equal parts valerian, passionflower, hops. 4–5 ml at bedtime.",
            "anxiety_blend": "Valerian with skullcap and lemon balm. 2–3 ml as needed."
        },
        "cautions": (
            "Paradoxical stimulation in some people — discontinue if this occurs. "
            "Avoid with pharmaceutical sedatives/hypnotics. Do not drive after use. "
            "Some people experience vivid dreams. Avoid in first trimester of pregnancy."
        ),
        "hopman_notes": (
            "Hopman distinguishes between valerian as a 'heavy' sedative suited to robust "
            "constitutions and gentler nervines (passionflower, chamomile, lemon balm) for "
            "sensitive nervous systems. She recommends building nervine support protocols "
            "rather than relying on single strong herbs."
        ),
        "season": "Root harvest autumn of second year.",
        "growing": "Tall perennial; moist rich soil; part shade. Flowers attract cats. "
                   "Allow to grow two years before harvesting root.",
        "druid_lore": "Used in protective workings and to calm tension before ritual. Associated with Mercury.",
        "tags": ["sleep", "insomnia", "anxiety", "muscle-tension", "sedative", "nervine", "menstrual", "stress"]
    },

    {
        "common_name": "Hawthorn",
        "latin_name": "Crataegus monogyna / C. laevigata / C. oxyacantha",
        "family": "Rosaceae",
        "parts_used": ["berries", "flowers", "leaves"],
        "actions": ["cardiotonic", "vasodilator", "antioxidant", "hypotensive",
                    "antiarrhythmic", "adaptogen for the heart"],
        "constituents": ["oligomeric proanthocyanidins (OPCs)", "flavonoids (vitexin, quercetin)",
                         "triterpene acids", "tannins", "pectin"],
        "traditional_uses": (
            "The heart herb above all others in Western herbalism and in Druid tradition. "
            "Hopman writes at length about hawthorn as the sacred threshold tree of Celtic "
            "faery lore — standing at the boundary between worlds. Medicinally, long-term "
            "use strengthens cardiac muscle, reduces blood pressure, improves coronary "
            "circulation, and normalizes arrhythmia. It is both food and medicine — berries "
            "eaten fresh or made into jam, jelly, and syrup. One of the safest herbs for "
            "long-term use, appropriate for lifetime daily supplementation."
        ),
        "preparations": {
            "berry_tincture": "1:5 in 25% alcohol. 4–6 ml three times daily long-term for heart.",
            "flower_leaf_tincture": "1:5 in 40% alcohol. Flowers and leaves used fresh in spring.",
            "berry_syrup": "Simmer 2 cups berries in 4 cups water 30 min; mash, strain, "
                           "add honey. 1–2 tbsp daily as cardiac tonic.",
            "tea": "2 tsp dried berries or flowers per cup; simmer berries 10 min; "
                   "steep flowers 10 min. 3 cups daily.",
            "jam_jelly": "Culinary preparation of berries — seedy but delicious with honey.",
            "combined_heart_formula": "Hawthorn with motherwort and linden for hypertension with anxiety."
        },
        "cautions": (
            "Safe for long-term use but takes 4–8 weeks for full effect. "
            "If on pharmaceutical cardiac medications (digoxin, beta-blockers), "
            "use only under supervision — potentiation possible. "
            "NEVER cut a lone hawthorn in Celtic tradition without ritual apology and offering."
        ),
        "hopman_notes": (
            "Hopman devotes significant space to hawthorn as both medicine and sacred plant. "
            "She describes the faery mounds often marked by lone hawthorn trees in Ireland "
            "and the tremendous ill luck that follows those who fell these trees without "
            "permission. The tree opens the heart in both physical and spiritual dimensions."
        ),
        "season": "Flowers May (Beltane); berries September–November.",
        "growing": "Hardy thorny shrub/small tree; any soil; full sun to part shade. "
                   "Makes excellent hedgerow. Slow growing but very long-lived.",
        "druid_lore": (
            "Hawthorn (Huath in Ogham) is one of the most sacred Celtic trees. "
            "It marks Beltane (May 1) — the May tree. Associated with faery, the "
            "threshold between worlds, protection of the home, and the heart. "
            "Cutting a lone hawthorn is among the most dangerous acts in Irish folk tradition."
        ),
        "tags": ["heart", "cardiovascular", "blood-pressure", "tonic", "sacred", "faery", "Beltane", "ogham", "antioxidant"]
    },

    {
        "common_name": "Motherwort",
        "latin_name": "Leonurus cardiaca",
        "family": "Lamiaceae",
        "parts_used": ["aerial parts in flower"],
        "actions": ["cardiotonic", "nervine", "antispasmodic", "emmenagogue",
                    "hypotensive", "anxiolytic", "uterine tonic"],
        "constituents": ["leonurine", "stachydrine", "iridoid glycosides",
                         "alkaloids", "flavonoids", "tannins"],
        "traditional_uses": (
            "The name tells the story — 'mother's herb for the heart.' Hopman describes it "
            "as the premier herb for anxiety-driven heart palpitations, nervous tachycardia, "
            "and the physical heart tension that comes with worry and grief. Equally "
            "important as a uterine tonic: brings on delayed periods, eases menstrual "
            "cramping, and supports the uterus through menopausal transition. Bitter "
            "taste mediates liver function."
        ),
        "preparations": {
            "tincture": "Fresh plant 1:2 in 40% alcohol. 2–4 ml three times daily. "
                        "Most effective preparation due to bitter alkaloids.",
            "tea": "Very bitter. 1 tsp dried herb per cup, steep 10 min. May need honey.",
            "heart_formula": "Combine with hawthorn and linden for hypertension with anxiety.",
            "menstrual_formula": "Combine with cramp bark and ginger for dysmenorrhea."
        },
        "cautions": (
            "Contraindicated in pregnancy — strong uterine stimulant/emmenagogue. "
            "Avoid with pharmaceutical cardiac medications without guidance. "
            "Not in heavy bleeding conditions."
        ),
        "hopman_notes": (
            "Hopman links motherwort to the archetype of the protective, fierce mother — "
            "a plant that opens and strengthens the heart while also protecting it. "
            "She includes it in her Druidic herb garden as a plant of courageous love."
        ),
        "season": "Harvest aerial parts at first flowering.",
        "growing": "Tall perennial; any soil; part shade to full sun. Self-seeds abundantly.",
        "druid_lore": "Associated with the fierce protective mother archetype; plants of love and courage.",
        "tags": ["heart", "palpitations", "anxiety", "menstrual", "uterine", "hypertension", "nervine"]
    },

    {
        "common_name": "Ginger",
        "latin_name": "Zingiber officinale",
        "family": "Zingiberaceae",
        "parts_used": ["fresh rhizome", "dried rhizome"],
        "actions": ["circulatory stimulant", "carminative", "antiemetic", "diaphoretic",
                    "anti-inflammatory", "analgesic", "antispasmodic", "antibacterial"],
        "constituents": ["gingerols (fresh)", "shogaols (dried)", "paradols",
                         "volatile oils", "oleoresin", "protease (zingibain)"],
        "traditional_uses": (
            "Universal medicine across every traditional healing system on Earth. "
            "Hopman includes it as an essential apothecary staple. Fresh ginger is warming, "
            "moving, and deeply antiemetic — first-line for morning sickness, motion sickness, "
            "post-surgical nausea, and chemotherapy nausea. Brings circulation to the periphery "
            "and is the herb of choice for cold, stagnant conditions. Dried ginger is hotter "
            "and more drying — specific for respiratory congestion with cold quality."
        ),
        "preparations": {
            "fresh_tea": "Slice 1-inch fresh root, simmer 10–15 min. For nausea, cold and flu, "
                         "poor circulation, digestive stagnation.",
            "fire_cider": "Core ingredient in apple cider vinegar immune tonic with horseradish, "
                          "garlic, onion, cayenne, citrus.",
            "ginger_honey": "Finely grated fresh ginger packed in raw honey; 1 tsp in tea for "
                            "cold and nausea.",
            "tincture": "Fresh plant 1:2 in 95% alcohol. A few drops to 2 ml as needed.",
            "warming_compress": "Ginger decoction as hot compress for arthritic joints, "
                                "menstrual cramps, muscle stiffness.",
            "culinary": "Daily culinary use provides continuous digestive and anti-inflammatory benefit.",
            "capsule": "Standardized for nausea: 250 mg four times daily for morning sickness."
        },
        "cautions": (
            "Large doses may increase bleeding time — caution with blood thinners. "
            "May increase absorption of many pharmaceuticals. Heartburn in some individuals."
        ),
        "hopman_notes": (
            "Hopman includes ginger as an 'activator' herb — one that enhances the action "
            "of other herbs in a formula and moves stagnation in both body and energy."
        ),
        "season": "Tropical perennial; grow in containers or as annual in cold climates.",
        "growing": "Rich moist soil, shade to partial sun. Dig roots in autumn.",
        "druid_lore": "Fire and solar associations; used in ceremony for warmth, activation, and courage.",
        "tags": ["nausea", "digestive", "circulation", "warming", "cold", "flu", "anti-inflammatory", "spice"]
    },

    {
        "common_name": "Ashwagandha",
        "latin_name": "Withania somnifera",
        "family": "Solanaceae",
        "parts_used": ["root"],
        "actions": ["adaptogen", "nervine tonic", "immune modulator", "thyroid tonic",
                    "anti-inflammatory", "anabolic", "anxiolytic", "antioxidant"],
        "constituents": ["withanolides", "alkaloids (somniferine)", "iron", "saponins",
                         "sterols", "glycosides"],
        "traditional_uses": (
            "The premier Ayurvedic adaptogen — used for 3,000+ years to build strength, "
            "endurance, resilience, and calm simultaneously. Hopman includes it in her holistic "
            "apothecary as a foundational tonic for modern stress disease. Unlike stimulating "
            "adaptogens (eleuthero, rhodiola), ashwagandha is deeply calming while building "
            "vitality — the ideal herb for the exhausted, wired, anxious person who cannot "
            "sleep. Raises low thyroid, builds muscle and bone, enhances cognitive function, "
            "and supports immune resilience."
        ),
        "preparations": {
            "milk_decoction": (
                "Traditional Ayurvedic preparation: 1 tsp root powder simmered in 1 cup "
                "warm milk (dairy or plant) 10 min with honey. 1–2 times daily. "
                "Fats increase withanolide absorption."
            ),
            "tincture": "Dried root 1:5 in 45% alcohol. 4–6 ml twice daily long-term.",
            "capsule": "500–600 mg standardized root extract twice daily.",
            "golden_milk": "Combined with turmeric, black pepper, ginger in warm milk.",
            "ashwagandha_ghee": "Powdered root cooked into clarified butter for absorption."
        },
        "cautions": (
            "Nightshade family — avoid in nightshade sensitivity. May amplify thyroid medication "
            "— monitor if on levothyroxine. Avoid in pregnancy. May cause vivid dreams (beneficial for some). "
            "Rarely: GI upset with high doses."
        ),
        "hopman_notes": (
            "Hopman includes ashwagandha as a bridge between Western herbal tradition and "
            "Ayurveda, noting the interconnection of global plant wisdom. She recommends it "
            "as a long-term tonic (3–6 months minimum) for stress resilience."
        ),
        "season": "Perennial in tropical zones; annual in cold climates. Root harvested autumn.",
        "growing": "Full sun, well-drained soil, drought tolerant. Can grow in containers.",
        "druid_lore": "Imported wisdom honored in the modern holistic tradition; adaptogen wisdom crosses all traditions.",
        "tags": ["adaptogen", "stress", "anxiety", "sleep", "thyroid", "immune", "tonic", "fatigue", "Ayurveda"]
    },

    {
        "common_name": "Skullcap",
        "latin_name": "Scutellaria lateriflora",
        "family": "Lamiaceae",
        "parts_used": ["aerial parts (fresh preferred)"],
        "actions": ["nervine tonic", "anxiolytic", "antispasmodic", "sedative",
                    "anticonvulsant", "neuroprotective"],
        "constituents": ["baicalin", "baicalein", "scutellarein", "flavonoids",
                         "iridoids", "tannins"],
        "traditional_uses": (
            "Native American nervine with deep affinity for the nervous system as a whole. "
            "Where valerian sedates, skullcap nourishes and rebuilds the nervous system. "
            "Hopman describes it as the herb for nervous exhaustion, nervous twitches, "
            "restless legs, anxiety with tension, and the frayed, overstimulated nervous "
            "system of modern life. One of the best herbs for nervous system recovery "
            "after trauma, withdrawal, or prolonged stress."
        ),
        "preparations": {
            "tincture": "Fresh plant 1:2 in 40% alcohol — dried plant loses potency rapidly. "
                        "2–4 ml three times daily for nervous rebuilding; higher acute dose for anxiety.",
            "tea": "Best used fresh; dried tea less effective. 2 tsp per cup, steep 15 min.",
            "nervine_blend": "Skullcap with oat straw and milky oats for deep nervous rebuild.",
            "sleep_blend": "With valerian and passionflower for insomnia."
        },
        "cautions": (
            "Adulteration common in commerce — often mixed with germander (hepatotoxic). "
            "Source from reputable suppliers. Fresh plant tincture far superior to dried. "
            "Avoid in pregnancy. Large doses may cause confusion — stay within dosage."
        ),
        "hopman_notes": (
            "Hopman calls skullcap 'the nervous system's best friend' and emphasizes "
            "the importance of fresh-plant preparations. She includes it in protocols "
            "for trauma recovery and PTSD support."
        ),
        "season": "Harvest aerial parts in summer when beginning to flower.",
        "growing": "Native woodland species; moist rich soil, partial shade. Perennial.",
        "druid_lore": "Associated with Mercury and the nervous pathways; supports clear perception and connection.",
        "tags": ["nervine", "anxiety", "trauma", "nervous-system", "sleep", "twitching", "restless-legs", "neuroprotective"]
    },

    {
        "common_name": "Oat Straw / Milky Oats",
        "latin_name": "Avena sativa",
        "family": "Poaceae",
        "parts_used": ["milky oat tops (fresh, at 'milk stage')", "dried oat straw"],
        "actions": ["nervine tonic", "nutritive", "restorative", "antidepressant (mild)",
                    "demulcent", "thymoleptic"],
        "constituents": ["avenanthramides", "steroidal saponins", "beta-glucans", "silica",
                         "B vitamins", "calcium", "magnesium", "iron"],
        "traditional_uses": (
            "Oats in the milky stage — when the grain, squeezed, exudes a white latex — "
            "are one of the premier nervous system restoratives in Western herbalism. "
            "Hopman's nourishing herbal infusion tradition (endorsed from Susun Weed) "
            "includes oat straw as a daily mineral and nerve tonic. Where skullcap calms "
            "and valerian sedates, milky oats rebuild the myelin sheath and restore deep "
            "nervous reserve over time. Essential for burnout, adrenal exhaustion, "
            "recovering from addiction, and chronic stress depletion."
        ),
        "preparations": {
            "milky_oat_tincture": "Fresh milky tops 1:2 in 40% alcohol — the window for harvest "
                                   "is very short (1 week). 3–5 ml three times daily long-term.",
            "oat_straw_infusion": (
                "Nourishing infusion: 1 oz dried oat straw in quart jar, fill with boiling water, "
                "cap, steep 4–8 hours. Drink 1–4 cups daily for mineral and nerve support."
            ),
            "porridge": "Daily oatmeal provides ongoing benefit — the whole grain matters.",
            "bath": "Colloidal oat bath for eczema, dry itchy skin, anxiety. "
                    "Blend oats fine, add to warm bath."
        },
        "cautions": "Avoid in celiac disease (gluten). Fresh milky oats only available in brief window at harvest time.",
        "hopman_notes": (
            "Hopman regularly recommends oat straw infusion as a foundational daily tonic, "
            "especially for women, to build calcium and magnesium reserves and sustain "
            "nervous system vitality through the demands of modern life."
        ),
        "season": "Milky tops: very brief window late spring/early summer when grain fills.",
        "growing": "Annual grain crop; easy to grow in any garden.",
        "druid_lore": "Associated with the harvest cycle and abundance. Corn dollies of oats were sacred harvest figures.",
        "tags": ["nervine", "tonic", "burnout", "mineral", "calcium", "adrenal", "rebuild", "exhaustion", "restorative"]
    },

    {
        "common_name": "Mullein",
        "latin_name": "Verbascum thapsus",
        "family": "Scrophulariaceae",
        "parts_used": ["leaves", "flowers", "root"],
        "actions": ["expectorant", "demulcent", "antispasmodic", "anti-inflammatory",
                    "antimicrobial", "vulnerary", "astringent"],
        "constituents": ["mucilage", "saponins", "aucubin", "flavonoids",
                         "tannins", "triterpene saponins"],
        "traditional_uses": (
            "The great lung herb of traditional Western herbalism. Hopman describes mullein "
            "as the herb that looks like the lung — its large woolly leaves evoke the lung's "
            "bronchial tree, and it heals exactly that tissue. Soothes bronchial spasm, "
            "loosens stuck mucus, and reduces inflammation. Used for bronchitis, asthma, "
            "emphysema, persistent dry cough, and whooping cough. The flowers infused in "
            "olive oil are the traditional remedy for ear infections."
        ),
        "preparations": {
            "leaf_tea": (
                "2 tsp dried leaf per cup, steep 15 min, strain through cloth to remove "
                "fine hairs (which irritate throat). For coughs, bronchitis, asthma."
            ),
            "flower_ear_oil": (
                "Pack fresh flowers (wilted one day) in olive oil; infuse in warm place "
                "2–4 weeks. Strain carefully. Warm slightly (test on wrist). "
                "3–5 drops in ear canal for ear infections and pain. "
                "Do NOT use if eardrum is perforated."
            ),
            "tincture": "Dried leaf or root 1:5 in 30% alcohol. 3–5 ml three times daily.",
            "smoking_blend": "Dried leaf smoked traditionally for asthma and bronchitis — "
                             "counterintuitive but the saponins act as expectorant via inhalation.",
            "root_decoction": "Simmer root for urinary tract tone and back/spinal support."
        },
        "cautions": "Always strain leaf tea through cloth — fine hairs cause throat irritation. Not for perforated eardrums.",
        "hopman_notes": (
            "Hopman mentions the magnificent sentinel presence of second-year mullein — "
            "its tall flower spike rising 6 feet in disturbed ground — as a sign the land "
            "is healing. A plant of boundary places and healing transitions."
        ),
        "season": "Leaves (first year rosette) best in fall/spring; flowers second year summer.",
        "growing": "Biennial; full sun; dry poor soil. Self-seeds prolifically. Found in disturbed ground.",
        "druid_lore": "The tall stalk was dipped in tallow and used as a torch (hag's taper). A liminal plant.",
        "tags": ["lung", "cough", "bronchitis", "ear", "asthma", "expectorant", "respiratory", "demulcent"]
    },

    {
        "common_name": "Dandelion",
        "latin_name": "Taraxacum officinale",
        "family": "Asteraceae",
        "parts_used": ["root", "leaves", "flowers"],
        "actions": ["liver tonic", "diuretic", "bitter digestive", "nutritive",
                    "cholagogue", "alterative", "anti-inflammatory"],
        "constituents": ["taraxacin", "taraxacerin", "inulin", "phytosterols",
                         "flavonoids", "vitamins A C K", "potassium", "calcium", "iron"],
        "traditional_uses": (
            "Hopman gives dandelion pride of place as the ultimate liver tonic and nutritive "
            "weed. Spring dandelion greens are among the most nutrient-dense wild foods "
            "available — more beta-carotene than carrots, more calcium than milk. "
            "Root is the primary liver herb — stimulating bile production, clearing liver "
            "congestion, supporting fat metabolism and detoxification. Unlike pharmaceutical "
            "diuretics, dandelion leaf replaces the potassium it removes. The bitter taste "
            "is the medicine — stimulating the entire digestive cascade."
        ),
        "preparations": {
            "spring_greens": "Young leaves before flowering in salads, sautéed, or juiced. Bitter but nutritious.",
            "root_tea": "Decoct 2 tsp dried root per cup 10 min; for liver and digestion. "
                        "Three cups daily.",
            "root_tincture": "1:5 in 25% alcohol. 4–6 ml three times daily for liver support.",
            "leaf_tea": "2 tsp dried leaf per cup; diuretic and kidney support. "
                        "Does not deplete potassium.",
            "roasted_root": "Roasted dandelion root tea as coffee substitute — liver tonic daily beverage.",
            "flower_wine": "Traditional spring tonic wine made from fresh flowers.",
            "dandelion_honey": "Flowers simmered with water and honey — golden syrup."
        },
        "cautions": "Bile duct obstruction or gallstone obstruction — use with care. Latex in stem may cause contact dermatitis.",
        "hopman_notes": (
            "Hopman writes of dandelion as the misunderstood champion of the lawn — 'the "
            "first medicine of spring, rising precisely when the liver and lymph need "
            "moving after winter stagnation.' She celebrates it as a plant of solar joy "
            "and relentless persistence."
        ),
        "season": "Year-round in mild climates; best spring and autumn for root; spring for greens.",
        "growing": "Impossible to eradicate — embrace it. Deep taproot aerates compacted soil.",
        "druid_lore": "Dandelion was used in Druidic divination and is a solar plant associated with Beltane and sun festivals.",
        "tags": ["liver", "digestive", "diuretic", "nutritive", "spring", "bitter", "weed", "foraging", "detox"]
    },

    {
        "common_name": "Passionflower",
        "latin_name": "Passiflora incarnata",
        "family": "Passifloraceae",
        "parts_used": ["aerial parts (leaves, stems, tendrils, flowers)"],
        "actions": ["anxiolytic", "sedative", "antispasmodic", "hypnotic",
                    "analgesic", "antihypertensive", "GABA modulator"],
        "constituents": ["harmane alkaloids", "flavonoids (chrysin, vitexin)", "maltol",
                         "cyanogenic glycosides", "sterols"],
        "traditional_uses": (
            "Native American and Appalachian herb for anxiety, pain, and sleep. "
            "Hopman describes passionflower as the ideal herb for the mind that won't "
            "turn off — the 'circular thinking' insomniac who ruminate at 3 AM. "
            "It works on GABA receptors similarly to benzodiazepines but without "
            "dependency or morning grogginess. The flowers are among the most "
            "structurally complex and beautiful in the plant world — the medicine "
            "teaches through beauty."
        ),
        "preparations": {
            "tincture": "Fresh plant 1:2 in 40% alcohol. 3–5 ml at bedtime for insomnia; "
                        "2–3 ml as needed for anxiety.",
            "tea": "2–3 tsp dried herb per cup, steep 15 min. Less potent than tincture.",
            "sleep_blend": "Combine with valerian and hops; 4–5 ml 30 min before bed.",
            "anxiety_formula": "Combine with lemon balm and skullcap during the day."
        },
        "cautions": "Avoid with pharmaceutical sedatives and MAOIs. Avoid high doses in pregnancy.",
        "hopman_notes": (
            "Hopman is particularly fond of passionflower for its ability to quiet 'monkey "
            "mind' — the over-thinking, over-planning, over-worrying mental pattern so "
            "common in anxious modern people."
        ),
        "season": "Harvest aerial parts when flowering July–September.",
        "growing": "Vigorous native vine; full sun; well-drained soil. Hardy to zone 6.",
        "druid_lore": "A plant of peace and surrender — useful in meditation to still the chattering mind.",
        "tags": ["anxiety", "sleep", "insomnia", "GABA", "rumination", "nervine", "sedative", "mind"]
    },
]


# ── Preparation methods ───────────────────────────────────────────────────────

PREPARATION_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "method": "Nourishing Herbal Infusion",
        "category": "water extraction",
        "description": (
            "Ellen Evert Hopman endorses Susun Weed's method of the nourishing herbal infusion "
            "as distinct from 'tea.' An infusion is made with a much larger quantity of herb, "
            "steeped for a much longer time, producing a medicinal-strength mineral and nutrient extract."
        ),
        "how_to": (
            "Place 1 ounce (28 grams) dried herb in a quart mason jar. Fill completely with "
            "just-boiled water. Cap tightly. Steep 4–8 hours or overnight. Strain and squeeze "
            "the herb mass to extract all liquid. Drink at room temperature or refrigerate "
            "up to 36 hours. Drink 1–4 cups daily."
        ),
        "best_herbs": ["nettle", "oat straw", "red clover", "comfrey leaf (short-term)", "linden"],
        "purpose": "Long-term nutritive mineral extraction; chronic deficiency; building reserve",
        "notes": "Hopman emphasizes this as a daily practice, not an occasional remedy."
    },
    {
        "method": "Standard Herbal Infusion (Tea)",
        "category": "water extraction",
        "description": "Boiling water poured over herb, steeped briefly. For volatile-oil herbs.",
        "how_to": (
            "1–2 teaspoons dried herb (or 1–2 tablespoons fresh) per 8 oz cup. "
            "Pour just-boiled water over herb. Cover (essential to preserve volatile oils). "
            "Steep 10–15 minutes. Strain. Drink warm or cool."
        ),
        "best_herbs": ["chamomile", "peppermint", "lavender", "lemon balm", "passionflower", "yarrow"],
        "purpose": "Acute symptoms, daily medicinal use, digestive and nervous conditions"
    },
    {
        "method": "Decoction",
        "category": "water extraction",
        "description": "Simmering roots, bark, seeds, and dense plant matter to extract constituents.",
        "how_to": (
            "Place 1–2 tablespoons hard material (root, bark, seeds) per 2 cups water in pot. "
            "Bring to simmer; reduce heat to low. Simmer covered 20–40 minutes. "
            "Strain. Drink 1–3 cups daily."
        ),
        "best_herbs": ["dandelion root", "valerian root", "ashwagandha root", "hawthorn berries", "ginger"],
        "purpose": "Extracting constituents from dense plant material that tea cannot reach"
    },
    {
        "method": "Tincture Making",
        "category": "alcohol extraction",
        "description": (
            "Alcohol extracts a broader range of plant constituents than water — including "
            "resins, alkaloids, and many volatile compounds. Shelf life of years."
        ),
        "how_to": (
            "Fresh plant method (1:2): Pack fresh chopped herb into jar. Cover completely "
            "with menstruum (vodka, brandy, or food-grade alcohol diluted to target %). "
            "Cap. Label with date, plant name, alcohol %, ratio. Macerate 4–6 weeks, "
            "shaking daily. Strain through cloth, squeeze out all liquid. Press marc. "
            "Bottle in dark glass. Label. Store in cool dark place.\n\n"
            "Dried herb (1:5): 1 part herb by weight, 5 parts menstruum by volume. "
            "Method otherwise same."
        ),
        "alcohol_percentages": {
            "25–30%": "Water-soluble constituents, mucilage, minerals, polysaccharides",
            "40–50%": "General tinctures, most alkaloids and flavonoids (standard vodka)",
            "60–70%": "Resins, essential oils, highly lipophilic constituents (calendula, St. John's wort)",
            "90–95%": "Strongest resins; dilute before dosing"
        },
        "dosage_standard": "2–5 ml (40–100 drops) three times daily for most herbs; adjust per herb profile.",
        "purpose": "Long-term storage, concentrated dosing, broad constituent extraction"
    },
    {
        "method": "Herbal Infused Oil",
        "category": "oil extraction",
        "description": "Oil extraction of fat-soluble constituents for topical use and salve making.",
        "how_to": (
            "Cold/Solar method: Fill jar with dried or wilted (not wet) herbs. "
            "Cover completely with carrier oil (olive, sunflower, jojoba). "
            "Cap. Place in sunny window 4–6 weeks, shaking daily. Strain.\n\n"
            "Heat method (faster): Place herb and oil in slow cooker on LOWEST setting "
            "(must not exceed 100°F/38°C). Infuse 48–72 hours. Strain. "
            "Use as topical oil or base for salve."
        ),
        "best_herbs": ["calendula", "st. john's wort", "comfrey", "lavender", "chamomile", "mullein flowers"],
        "carrier_oils": {
            "olive": "Traditional, long shelf life, nourishing",
            "sunflower": "Lighter, good for sensitive skin",
            "jojoba": "Very stable, long shelf life, excellent skin penetration",
            "coconut": "Antimicrobial, solid at room temp — good for salves"
        },
        "purpose": "Skin healing, salve base, wound care, muscle pain, ear oil"
    },
    {
        "method": "Salve Making",
        "category": "topical preparation",
        "description": "Beeswax-thickened herbal oil for topical application.",
        "how_to": (
            "Standard ratio: 1 oz (28g) beeswax per 1 cup (240ml) infused oil. "
            "Melt beeswax in double boiler. Add warmed infused oil slowly, stirring. "
            "Test consistency: drop onto cold plate — if too hard, add more oil; "
            "if too soft, add more melted wax. "
            "Add essential oils if desired (off heat, under 110°F). "
            "Pour into tins or jars while still liquid. Do not move until set. "
            "Label with contents and date. Shelf life 1–2 years."
        ),
        "purpose": "Wound healing, skin conditions, muscle pain, chapped lips, burns, rashes"
    },
    {
        "method": "Poultice",
        "category": "topical preparation",
        "description": "Fresh or reconstituted plant material applied directly to skin.",
        "how_to": (
            "Fresh: Bruise, chew, or mash fresh herb. Apply directly to affected area. "
            "Cover with clean cloth. Replace every 20–30 minutes for acute conditions.\n\n"
            "Dried: Moisten dried herb with small amount of hot water to paste. Apply and cover."
        ),
        "best_herbs": ["plantain (fresh chewed)", "yarrow (wounds)", "comfrey (fractures)", "cabbage leaf (mastitis)"],
        "purpose": "Wounds, bites, stings, infections, fractures, inflammations"
    },
    {
        "method": "Oxymel",
        "category": "vinegar and honey extraction",
        "description": "Ancient preparation combining raw apple cider vinegar and raw honey with herbs.",
        "how_to": (
            "Pack herbs into jar. Combine equal parts raw ACV and raw honey, warm slightly "
            "to liquefy honey, pour over herbs. Cap. Steep 4–6 weeks. Strain. "
            "Bottle in dark glass. 1 tablespoon as needed or daily. "
            "Shelf life 1 year."
        ),
        "best_herbs": ["elderberry", "elderflower", "ginger", "garlic", "thyme", "hyssop", "fire cider blend"],
        "purpose": "Respiratory conditions, immune support, those who cannot use alcohol"
    },
    {
        "method": "Glycerite",
        "category": "glycerin extraction",
        "description": "Vegetable glycerin extraction — alcohol-free, sweet, ideal for children and those avoiding alcohol.",
        "how_to": (
            "Fill jar with fresh or dried herb. Cover with food-grade vegetable glycerin "
            "(80% glycerin / 20% water ratio for dried herbs; straight glycerin for fresh). "
            "Macerate 4–6 weeks. Strain. Shelf life 1–3 years."
        ),
        "best_herbs": ["lemon balm", "echinacea", "elderberry", "chamomile", "passionflower"],
        "purpose": "Children's preparations, those avoiding alcohol, sweet taste preferred"
    },
    {
        "method": "Herbal Vinegar",
        "category": "vinegar extraction",
        "description": "Apple cider vinegar extracts minerals exceptionally well.",
        "how_to": (
            "Pack herbs into jar. Cover with raw unfiltered apple cider vinegar. "
            "Use plastic lid or parchment between jar and metal lid (vinegar corrodes metal). "
            "Steep 4–6 weeks, shaking daily. Strain. Use as food dressing or 1 tbsp in water."
        ),
        "best_herbs": ["nettle", "dandelion", "red clover", "violet leaf", "garlic"],
        "purpose": "Mineral extraction especially calcium and iron; daily nutritive tonic"
    },
    {
        "method": "Fire Cider",
        "category": "vinegar tonic",
        "description": "Traditional warming immune tonic from the American folk herbalism tradition.",
        "how_to": (
            "Combine in quart jar: ½ cup grated fresh horseradish root, ½ cup chopped onion, "
            "10 cloves garlic (crushed), ¼ cup grated fresh ginger, 1 tbsp grated fresh turmeric, "
            "1 jalapeño or pinch cayenne, zest and juice of 1 lemon and 1 orange. "
            "Add any of: rosemary, thyme, black pepper, echinacea, elderberry. "
            "Cover completely with raw ACV. Macerate 4 weeks, shaking daily. "
            "Strain, sweeten with raw honey to taste. "
            "1 tbsp daily preventive; 1 tbsp every few hours when ill."
        ),
        "purpose": "Immune support, cold and flu prevention, warming circulation, digestive fire"
    },
]


# ── Holistic principles ───────────────────────────────────────────────────────

HOLISTIC_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "topic": "Foundations of Holistic Health",
        "content": (
            "Hopman's holistic framework, consistent with all great traditional healing systems, "
            "recognizes health as a dynamic balance of body, mind, spirit, and relationship "
            "to the natural world. No symptom exists in isolation — every physical condition "
            "has emotional, mental, and spiritual dimensions. True healing addresses all layers.\n\n"
            "The healer's first work is to understand the whole person: constitution, lifestyle, "
            "relationships, spiritual life, relationship to the seasons, and to the land they "
            "inhabit. Herbs are matched not just to symptoms but to the person's pattern."
        ),
        "principles": [
            "The body has inherent healing intelligence — the healer supports this, not replaces it.",
            "Like treats like in some traditions; opposites in others — know the system you work within.",
            "The dose makes the poison — all plants have appropriate doses and contraindications.",
            "Seasonal rhythms govern health — align with them rather than fighting them.",
            "Food is medicine — begin every healing protocol with diet.",
            "Rest, sleep, and stress reduction are foundational — no herb replaces them.",
            "Emotional and spiritual wellbeing directly affects physical health.",
            "The healer heals themselves first — ongoing personal practice is essential.",
        ]
    },
    {
        "topic": "Herbal Energetics",
        "content": (
            "Every herb has an energetic character beyond its biochemistry. "
            "Hopman teaches the Celtic and Gaelic tradition of plant personalities — "
            "learning to know a plant as a being, not merely a collection of constituents.\n\n"
            "The four primary energetic qualities are: hot/cold and damp/dry. "
            "These are matched to the patient's condition: fever (hot) calls for cooling herbs; "
            "cold arthritic joints call for warming herbs like ginger and cayenne; "
            "dry cough calls for demulcent (moistening) herbs; boggy damp conditions call for drying astringents."
        ),
        "qualities": {
            "hot": "Ginger, cayenne, mustard, garlic, cinnamon — warming, stimulating, dispersing",
            "cold": "Peppermint, violet, marshmallow, chickweed — cooling, settling, reducing heat",
            "dry": "Oak bark, sage, yarrow, raspberry leaf — astringent, toning, drying excess moisture",
            "moist": "Slippery elm, marshmallow, comfrey, mullein leaf — demulcent, soothing, lubricating"
        }
    },
    {
        "topic": "The Doctrine of Signatures",
        "content": (
            "An ancient teaching found across European, Native American, and Ayurvedic traditions: "
            "plants reveal their medicinal uses through their physical appearance. "
            "Hopman teaches this as a tool of intuition and memory, not literal diagnosis.\n\n"
            "Examples: Walnut (brain-shaped) for neurological support; eyebright (flower resembles an eye) "
            "for eye conditions; lungwort (spotted leaves resemble lung tissue) for lungs; "
            "comfrey (deep-rooted, binding) for bone-knitting; red plants (hawthorn berries, rose hips) "
            "for the blood and heart; yellow plants (dandelion, St. John's wort) for the liver and solar plexus."
        )
    },
    {
        "topic": "Wildcrafting Ethics and Practice",
        "content": (
            "Hopman is insistent about ethical wildcrafting — harvesting from the wild responsibly. "
            "Her rules align with traditional indigenous protocols and modern conservation practice."
        ),
        "rules": [
            "Positive identification — never harvest what you cannot 100% identify.",
            "Harvest only from abundant, healthy, unsprayed populations.",
            "Never take more than one-third of any population.",
            "Leave the best specimens to seed — take from the middle of the stand.",
            "Ask permission — speak to the plant and wait for a sense of welcome.",
            "Leave an offering — tobacco, cornmeal, water, song, or prayer.",
            "Never harvest from roadsides, railroad tracks, industrial areas, or sprayed land.",
            "Know and follow local regulations about protected species.",
            "Prefer cultivated plants for species that are at-risk in the wild (echinacea angustifolia, goldenseal, black cohosh, wild ginseng).",
            "Grow what you need when possible — the most ethical source is your own garden.",
        ]
    },
    {
        "topic": "The Sacred Herbal Year — Celtic Seasonal Medicine",
        "content": (
            "Hopman's Druidic herbal calendar aligns healing practice with the eight Celtic festivals "
            "and the seasonal rhythms of the plant world. Each season has its appropriate medicines, "
            "harvests, and healing focus."
        ),
        "seasons": {
            "Imbolc (Feb 1–2)": (
                "End of winter — first stirrings. Harvest: dried roots and barks from previous autumn. "
                "Focus: lung and immune support for late-winter illness. Sacred plant: Brigid's cross "
                "made from rushes. Snowdrop — first flower of the year, a medicine of hope."
            ),
            "Spring Equinox (Mar 20–21)": (
                "Blood and lymph moving. Harvest: first spring greens — nettles, dandelion, cleavers, "
                "violet. Spring tonic time — bitter herbs to wake the liver, move the lymph, "
                "clean the blood after winter stagnation. Cleavers juice is premier lymph mover."
            ),
            "Beltane (May 1)": (
                "Height of spring life force. Hawthorn flowers (may blossom) at peak. "
                "Elder flowers just beginning. Violet leaves at their fullest. St. John's wort "
                "rising. All flowers gathered for joys and love medicines. Sacred sexual energy "
                "of the land is highest."
            ),
            "Summer Solstice / Midsummer (Jun 21)": (
                "Peak of the solar year. St. John's wort harvested at this exact moment for maximum "
                "red oil and hypericin. Lavender, chamomile, lemon balm at peak. "
                "All solar/sun herbs collected. Elder flowers finishing; elderberries forming."
            ),
            "Lughnasadh (Aug 1)": (
                "First harvest. Meadowsweet, rosebay willowherb, goldenrod. "
                "Elderberries ripening. Early harvest of roots beginning. "
                "Gratitude and first fruits ceremonies."
            ),
            "Autumn Equinox (Sep 21–22)": (
                "Full harvest. Elderberries, hawthorn berries, rose hips, sloes. "
                "Roots at their peak as plant draws energy down. "
                "Root harvest season begins in earnest. Preparation of winter medicines."
            ),
            "Samhain (Oct 31 – Nov 1)": (
                "The Celtic new year — thinning of the veil between worlds. "
                "Final root harvest. Rosemary and mugwort burned for ancestral remembrance. "
                "Protective herbs placed at thresholds. Seeds saved for next year."
            ),
            "Winter Solstice / Yule (Dec 21)": (
                "Deepest rest. Dried herbs, roots, and preserved medicines are now the pharmacy. "
                "Evergreens (pine, fir, holly, ivy) for immune support and winter spirit lifting. "
                "Elder, hawthorn, and rose hip syrups in daily use. Rest, dream, and gestate."
            )
        }
    },
    {
        "topic": "Nervine Herbs and the Nervous System",
        "content": (
            "Hopman categorizes nervine herbs by their action on the nervous system, "
            "important because using a sedative nervine when a tonic is needed, or vice versa, "
            "will not produce the desired result.\n\n"
            "The modern epidemic of nervous system disorders — anxiety, insomnia, burnout, "
            "depression, ADHD — requires understanding which type of support is needed."
        ),
        "categories": {
            "Nervine Tonics (rebuild over time)": ["oat straw/milky oats", "skullcap", "wood betony", "lion's mane mushroom"],
            "Nervine Relaxants (reduce tension, calm acutely)": ["passionflower", "lemon balm", "lavender", "hops", "california poppy"],
            "Nervine Sedatives (strongly sedate)": ["valerian", "kava", "jamaican dogwood"],
            "Adaptogenic Nervines (build stress resilience)": ["ashwagandha", "holy basil", "reishi mushroom", "eleuthero"],
            "Antidepressant Herbs": ["st. john's wort", "lemon balm", "saffron", "rosemary", "mucuna (dopaminergic)"]
        }
    },
    {
        "topic": "Immune Support Protocols",
        "content": (
            "Hopman distinguishes between acute immune support (at the onset of illness), "
            "immune rebuilding (after illness or depletion), and immune modulation (for "
            "autoimmune and chronic inflammatory conditions).\n\n"
            "These require different herbs and strategies."
        ),
        "protocols": {
            "Acute (first sign of illness)": (
                "Echinacea every 2–3 hours. Elderberry syrup 1 tbsp every 3–4 hours. "
                "Yarrow or elderflower tea (hot) to break fever and promote sweating. "
                "Ginger, garlic, and thyme in food and tea. Rest — sleep is the immune system's greatest tool."
            ),
            "Rebuilding (post-illness, post-antibiotic)": (
                "Astragalus as daily tonic (add to soups). Reishi mushroom tea or tincture. "
                "Elderberry syrup daily. Probiotics and fermented foods. "
                "Nourishing herbal infusions (nettle, oat straw). Gentle exercise only."
            ),
            "Long-term resilience": (
                "Daily adaptogen (ashwagandha, eleuthero, rhodiola — choose one based on constitution). "
                "Medicinal mushrooms (reishi, chaga, turkey tail) as daily tonic. "
                "Seasonal elderberry syrup from August–March. Vitamin D (especially in dark months). "
                "Stress reduction — the immune system's greatest enemy is chronic stress."
            ),
            "Autoimmune (modulating, not stimulating)": (
                "Avoid echinacea and elderberry (immune stimulants). "
                "Focus on: turmeric/curcumin, omega-3s, licorice root (anti-inflammatory), "
                "reishi (modulating not stimulating), gut healing herbs (slippery elm, marshmallow root). "
                "Address gut permeability — all autoimmune conditions improve with gut healing."
            )
        }
    },
    {
        "topic": "Women's Plant Medicine",
        "content": (
            "Hopman's books give extensive space to women's plant medicine — herbs that "
            "support the female reproductive system through all life phases. "
            "Celtic healing tradition honored the female body's cyclical nature as sacred."
        ),
        "phases": {
            "Menstrual cycle support": (
                "Raspberry leaf: classic uterine tonic — drink as tea throughout cycle. "
                "Cramp bark: antispasmodic for dysmenorrhea — take at onset of cramps. "
                "Ginger: warming and antispasmodic for cold, stagnant period pain. "
                "Motherwort: for irregular, painful, or scanty periods. "
                "Yarrow: for heavy bleeding. "
                "Dong quai: blood tonic for pale, scanty periods (avoid in heavy bleeding)."
            ),
            "Pregnancy": (
                "Raspberry leaf from second trimester: tones uterus for labor. "
                "Ginger: morning sickness (safe and well-studied). "
                "Chamomile and lemon balm: anxiety and digestive upset. "
                "Avoid: blue cohosh, pennyroyal, tansy, large doses of any strong herb, "
                "emmenagogues (motherwort, yarrow in high doses), valerian in first trimester."
            ),
            "Postpartum": (
                "Nettles: for blood rebuilding and milk production. "
                "Blessed thistle + fenugreek: galactagogues for milk supply. "
                "St. John's wort (as topical oil): for perineal healing. "
                "Calendula: sitz bath for wound healing. "
                "Ashwagandha: for adrenal rebuilding after birth depletion."
            ),
            "Perimenopause and menopause": (
                "Black cohosh: for hot flashes and mood (limit to 6 months continuous). "
                "Sage: hot flashes — 1 cup strong tea daily or tincture. "
                "Ashwagandha: adrenal and hormonal support. "
                "Wild yam: progesterone precursor for luteal phase support. "
                "Vitex (chaste tree): hormonal balancing over long term (6–18 months). "
                "Red clover: phytoestrogens for bone and heart protection. "
                "Nourishing infusions of nettle and oat straw: bone minerals."
            )
        }
    },
    {
        "topic": "Gut Health and Digestive Herbs",
        "content": (
            "Hippocrates: 'All disease begins in the gut.' Modern science confirms it. "
            "Hopman's tradition of herbal medicine has always prioritized digestive health "
            "as foundational. A healthy gut is prerequisite for everything else."
        ),
        "categories": {
            "Bitters (stimulate digestive secretions)": ["dandelion root", "burdock root", "gentian", "artichoke", "motherwort", "chamomile"],
            "Carminatives (relieve gas and spasm)": ["fennel", "ginger", "peppermint", "chamomile", "lemon balm", "anise", "dill"],
            "Demulcents (soothe irritated mucosa)": ["marshmallow root", "slippery elm", "licorice root", "aloe vera", "comfrey leaf"],
            "Astringents (tone lax gut, reduce diarrhea)": ["raspberry leaf", "oak bark", "agrimony", "meadowsweet"],
            "Gut flora support": ["fermented foods", "inulin-rich herbs (chicory, dandelion, burdock)", "slippery elm as prebiotic"],
            "Liver and bile": ["dandelion root", "milk thistle seed", "artichoke", "burdock root", "yellow dock"]
        }
    },
    {
        "topic": "Grief, Trauma, and Emotional Plant Medicine",
        "content": (
            "Hopman's Druidic tradition holds that plants have consciousness and compassion. "
            "Certain plants have particular affinity for emotional and spiritual healing — "
            "not as replacement for human support and therapy, but as allies in the process.\n\n"
            "The heart center in Celtic tradition is the seat of both love and grief — "
            "hawthorn, rose, and linden are the plants of the heart in all its dimensions."
        ),
        "plant_allies": {
            "Grief": ["hawthorn berry (for the heart)", "rose (heart opening)", "linden (nervous system and heart)", "st. john's wort (light in darkness)", "yarrow (protection while open)"],
            "Trauma": ["skullcap (nervous rebuild)", "milky oats (myelin and nerve restoration)", "ashwagandha (adrenal resilience)", "lemon balm (calm and clarity)", "tulsi/holy basil (lifting and opening)"],
            "Depression": ["st. john's wort (mild-moderate)", "saffron (studied equal to SSRIs for mild depression)", "rosemary (cognitive and mood)", "lemon balm (lifting)", "mucuna pruriens (dopamine precursor)"],
            "Anxiety": ["passionflower (ruminating mind)", "skullcap (nervous tension)", "kava (acute anxiety, ceremonial)", "ashwagandha (adrenal driving anxiety)", "lavender (immediate calming)"],
            "Anger": ["motherwort (fierce-to-soft heart)", "chamomile (the peacemaker)", "lemon balm (ease and lightness)", "vervain (for those who drive themselves too hard)"]
        }
    },
]

# ── Ogham tree medicine ───────────────────────────────────────────────────────

OGHAM_TREE_MEDICINE: List[Dict[str, Any]] = [
    {
        "tree": "Birch",
        "ogham": "Beith",
        "latin": "Betula pendula / B. papyrifera",
        "medicine": (
            "The tree of beginnings — first to colonize bare ground after disturbance. "
            "Bark tea is a traditional diuretic and anti-inflammatory for arthritis and gout, "
            "containing salicylates (natural aspirin). Leaves are also diuretic and kidney-supporting. "
            "Birch sap, tapped in early spring, is a traditional tonic drunk fresh or fermented. "
            "Chaga mushroom grows on birch and is harvested for its profound immune and antioxidant properties."
        ),
        "uses": ["diuretic", "arthritis", "gout", "kidney tonic", "spring cleansing"],
        "season": "Leaves and sap in spring; bark year-round",
        "spiritual": "New beginnings, purification, the young maiden, Imbolc"
    },
    {
        "tree": "Rowan",
        "ogham": "Luis",
        "latin": "Sorbus aucuparia",
        "medicine": (
            "Berries rich in vitamin C and sorbitol; traditionally used for sore throats, "
            "scurvy prevention, and as a mild laxative (cooked). The berries must be cooked "
            "to remove parasorbic acid (toxic raw). Berry jelly with wild game is traditional. "
            "Bark decoction used for diarrhea (high tannin content)."
        ),
        "uses": ["vitamin C", "sore throat", "digestive", "laxative (cooked berries)"],
        "cautions": "Raw berries mildly toxic — always cook",
        "spiritual": "Protection, sight, the threshold, sovereignty, warding against ill will"
    },
    {
        "tree": "Ash",
        "ogham": "Nion",
        "latin": "Fraxinus excelsior",
        "medicine": (
            "Leaves are mildly diuretic and laxative, used in tea for gout, arthritis, "
            "and rheumatism. Bark has bitter tonic properties for liver and digestive conditions. "
            "The seeds (ash keys) have been eaten as a famine food. "
            "Yggdrasil — the World Tree of Norse tradition — is the ash."
        ),
        "uses": ["gout", "arthritis", "diuretic", "liver tonic"],
        "spiritual": "The World Tree, connection between realms, the spine of the universe, sovereignty"
    },
    {
        "tree": "Oak",
        "ogham": "Duir",
        "latin": "Quercus robur / Q. alba",
        "medicine": (
            "Oak bark is one of the most astringent substances in the plant world — high in "
            "tannins. Used as a tea or decoction for diarrhea, dysentery, hemorrhoids, "
            "bleeding gums, and any condition requiring astringency. Bark tea as a gargle "
            "for tonsillitis. Topical bark wash for weeping eczema, wounds, and varicose veins. "
            "Acorns, leached of tannins, are a traditional food of extraordinary nutrition."
        ),
        "uses": ["diarrhea", "astringent", "hemorrhoids", "gums", "weeping skin conditions"],
        "spiritual": "The most sacred tree of the Druids. Strength, endurance, the center, sovereignty, the door (Duir = door) between worlds"
    },
    {
        "tree": "Holly",
        "ogham": "Tinne",
        "latin": "Ilex aquifolium",
        "medicine": (
            "Primarily a spiritual medicine in the Celtic tradition — a protective plant "
            "of the winter. Leaves have been used in traditional medicine for fever "
            "and rheumatism. Berries are toxic — do not ingest. Holly water (leaves soaked) "
            "used as a wash for jaundice in old European folk medicine. "
            "The plant is primarily sacred rather than medicinal in Hopman's treatment."
        ),
        "uses": ["fever (leaves)", "rheumatism"],
        "cautions": "Berries are toxic — do not consume",
        "spiritual": "The dark half of the year, the Holly King, protection, endurance through darkness, Yule"
    },
    {
        "tree": "Hazel",
        "ogham": "Coll",
        "latin": "Corylus avellana",
        "medicine": (
            "Hazelnuts are high in protein, healthy fats, vitamin E, and magnesium — "
            "a complete food of the Celtic tradition, associated with wisdom and the salmon of knowledge. "
            "Bark has astringent properties. The catkins (pollen) are an early spring food. "
            "Hazel divining rods were used to find water and underground truth."
        ),
        "uses": ["nutritive food (nuts)", "astringent (bark)"],
        "spiritual": "Wisdom, knowledge, inspiration (imbas), poetry, divination, the salmon of knowledge"
    },
    {
        "tree": "Elder",
        "ogham": "Ruis",
        "latin": "Sambucus nigra",
        "medicine": "See full Elder entry in plant knowledge — the most complete medicine tree.",
        "spiritual": "Endings and transformation, the Crone, the threshold of death and rebirth, Samhain, ancestral contact"
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE SEEDER
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS learned_knowledge (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    category       TEXT NOT NULL,
    subcategory    TEXT,
    title          TEXT NOT NULL,
    content        TEXT NOT NULL,
    metadata       TEXT,
    source         TEXT,
    tags           TEXT,
    date_learned   TEXT,
    access_count   INTEGER DEFAULT 0,
    last_accessed  TEXT
);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON learned_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_title    ON learned_knowledge(title);

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
    USING fts5(title, content, tags, content=learned_knowledge, content_rowid=id);

CREATE TRIGGER IF NOT EXISTS knowledge_after_insert
    AFTER INSERT ON learned_knowledge BEGIN
        INSERT INTO knowledge_fts(rowid, title, content, tags)
        VALUES (new.id, new.title, new.content, new.tags);
    END;

CREATE TRIGGER IF NOT EXISTS knowledge_after_update
    AFTER UPDATE ON learned_knowledge BEGIN
        UPDATE knowledge_fts SET title=new.title, content=new.content, tags=new.tags
        WHERE rowid=new.id;
    END;
"""


def get_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection):
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def already_seeded(conn: sqlite3.Connection) -> bool:
    cur = conn.execute(
        "SELECT COUNT(*) FROM learned_knowledge WHERE source LIKE '%Hopman%'"
    )
    return cur.fetchone()[0] > 0


def seed_plants(conn: sqlite3.Connection) -> int:
    count = 0
    for plant in PLANT_KNOWLEDGE:
        # Check if already exists
        existing = conn.execute(
            "SELECT id FROM learned_knowledge WHERE title=? AND category='plant_medicine'",
            (plant["common_name"],)
        ).fetchone()
        if existing:
            continue

        metadata = {k: v for k, v in plant.items()
                    if k not in ("common_name", "traditional_uses", "tags")}
        tags_str = ", ".join(plant.get("tags", []))
        source = "Ellen Evert Hopman — Secret Medicines from Your Garden; A Druid's Herbal; Western Herbalism"

        conn.execute(
            "INSERT INTO learned_knowledge "
            "(category, subcategory, title, content, metadata, source, tags, date_learned) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                "plant_medicine",
                plant.get("family", ""),
                plant["common_name"],
                plant["traditional_uses"],
                json.dumps(metadata),
                source,
                tags_str,
                datetime.now().isoformat(),
            )
        )
        count += 1

    conn.commit()
    return count


def seed_preparations(conn: sqlite3.Connection) -> int:
    count = 0
    for prep in PREPARATION_KNOWLEDGE:
        existing = conn.execute(
            "SELECT id FROM learned_knowledge WHERE title=? AND category='preparation'",
            (prep["method"],)
        ).fetchone()
        if existing:
            continue

        content = prep.get("description", "") + "\n\n" + prep.get("how_to", "")
        metadata = {k: v for k, v in prep.items()
                    if k not in ("method", "description", "how_to")}

        conn.execute(
            "INSERT INTO learned_knowledge "
            "(category, subcategory, title, content, metadata, source, tags, date_learned) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                "preparation",
                prep.get("category", ""),
                prep["method"],
                content,
                json.dumps(metadata),
                "Ellen Evert Hopman; Traditional Western Herbalism",
                prep.get("category", ""),
                datetime.now().isoformat(),
            )
        )
        count += 1

    conn.commit()
    return count


def seed_holistics(conn: sqlite3.Connection) -> int:
    count = 0
    for item in HOLISTIC_KNOWLEDGE:
        existing = conn.execute(
            "SELECT id FROM learned_knowledge WHERE title=? AND category='holistic'",
            (item["topic"],)
        ).fetchone()
        if existing:
            continue

        content = item["content"]
        # Append nested dicts as readable text
        for key in ("principles", "qualities", "categories", "protocols", "plant_allies",
                    "seasons", "phases", "rules"):
            val = item.get(key)
            if val:
                if isinstance(val, list):
                    content += "\n\n" + "\n".join(f"• {i}" for i in val)
                elif isinstance(val, dict):
                    for k, v in val.items():
                        content += f"\n\n{k}:\n{v}" if isinstance(v, str) else \
                                   f"\n\n{k}:\n" + ", ".join(v) if isinstance(v, list) else ""

        conn.execute(
            "INSERT INTO learned_knowledge "
            "(category, subcategory, title, content, metadata, source, tags, date_learned) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                "holistic",
                "principles",
                item["topic"],
                content,
                "{}",
                "Ellen Evert Hopman; Holistic Healing Tradition",
                "holistic,principles",
                datetime.now().isoformat(),
            )
        )
        count += 1

    conn.commit()
    return count


def seed_ogham_trees(conn: sqlite3.Connection) -> int:
    count = 0
    for tree in OGHAM_TREE_MEDICINE:
        existing = conn.execute(
            "SELECT id FROM learned_knowledge WHERE title=? AND category='ogham_tree'",
            (tree["tree"],)
        ).fetchone()
        if existing:
            continue

        content = tree["medicine"]
        if tree.get("spiritual"):
            content += f"\n\nSpiritual/Sacred: {tree['spiritual']}"

        tags_str = ", ".join(tree.get("uses", []) + ["druid", "celtic", "ogham", "sacred tree"])

        conn.execute(
            "INSERT INTO learned_knowledge "
            "(category, subcategory, title, content, metadata, source, tags, date_learned) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                "ogham_tree",
                "celtic_tree_medicine",
                tree["tree"],
                content,
                json.dumps({k: v for k, v in tree.items() if k not in ("tree", "medicine")}),
                "Ellen Evert Hopman — A Druid's Herbal; Sacred Tree Medicine",
                tags_str,
                datetime.now().isoformat(),
            )
        )
        count += 1

    conn.commit()
    return count


def seed_all(db_path: str, verbose: bool = True) -> dict:
    conn = get_db(db_path)
    init_schema(conn)

    results = {}
    results["plants"]       = seed_plants(conn)
    results["preparations"] = seed_preparations(conn)
    results["holistics"]    = seed_holistics(conn)
    results["ogham_trees"]  = seed_ogham_trees(conn)
    results["total"]        = sum(results.values())

    if verbose:
        total_stored = conn.execute(
            "SELECT COUNT(*) FROM learned_knowledge"
        ).fetchone()[0]
        print(f"🌿 Herbal knowledge seeded into {db_path}")
        print(f"   Plants:        {results['plants']} new entries")
        print(f"   Preparations:  {results['preparations']} new entries")
        print(f"   Holistics:     {results['holistics']} new entries")
        print(f"   Ogham Trees:   {results['ogham_trees']} new entries")
        print(f"   Added this run: {results['total']}")
        print(f"   Total in DB:   {total_stored}")

    conn.close()
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def search_knowledge(db_path: str, query: str, category: Optional[str] = None,
                     limit: int = 5) -> List[dict]:
    """Full-text search the knowledge base."""
    conn = get_db(db_path)

    try:
        if category:
            rows = conn.execute(
                """
                SELECT lk.* FROM knowledge_fts f
                JOIN learned_knowledge lk ON lk.id = f.rowid
                WHERE knowledge_fts MATCH ? AND lk.category = ?
                ORDER BY rank LIMIT ?
                """,
                (query, category, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT lk.* FROM knowledge_fts f
                JOIN learned_knowledge lk ON lk.id = f.rowid
                WHERE knowledge_fts MATCH ?
                ORDER BY rank LIMIT ?
                """,
                (query, limit)
            ).fetchall()

        # Update access counts
        ids = [r["id"] for r in rows]
        if ids:
            conn.execute(
                f"UPDATE learned_knowledge SET access_count=access_count+1, "
                f"last_accessed=? WHERE id IN ({','.join('?'*len(ids))})",
                [datetime.now().isoformat()] + ids
            )
            conn.commit()

        results = []
        for row in rows:
            r = dict(row)
            try:
                r["metadata"] = json.loads(r.get("metadata") or "{}")
            except Exception:
                r["metadata"] = {}
            results.append(r)

        return results

    except Exception as e:
        # FTS might not be available — fall back to LIKE
        rows = conn.execute(
            "SELECT * FROM learned_knowledge WHERE "
            "(title LIKE ? OR content LIKE ? OR tags LIKE ?) "
            + (f"AND category=? " if category else "") +
            "LIMIT ?",
            (f"%{query}%", f"%{query}%", f"%{query}%") +
            ((category, limit) if category else (limit,))
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_entry(db_path: str, title: str) -> Optional[dict]:
    conn = get_db(db_path)
    row = conn.execute(
        "SELECT * FROM learned_knowledge WHERE title LIKE ? LIMIT 1",
        (f"%{title}%",)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_categories(db_path: str) -> dict:
    conn = get_db(db_path)
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM learned_knowledge GROUP BY category"
    ).fetchall()
    conn.close()
    return {r["category"]: r["cnt"] for r in rows}


# ═══════════════════════════════════════════════════════════════════════════════
# NOVA PLUGIN
# ═══════════════════════════════════════════════════════════════════════════════

class HerbalKnowledgePlugin:
    """
    Nova plugin — queries the herbal knowledge base and can compose
    AI-enhanced answers using Nova's language model.

    Register with:
        from nova_herbal_knowledge import HerbalKnowledgePlugin
        system.plugins.register(HerbalKnowledgePlugin(system))
    """

    def __init__(self, system):
        self.system   = system
        self.logger   = system.logger
        self.db_path  = self._resolve_db(system)
        # Auto-seed on first registration
        self._ensure_seeded()

    def _resolve_db(self, system) -> str:
        try:
            from pathlib import Path
            cathedral = Path(system.cfg.get("nova", "cathedral_dir",
                             fallback=str(Path.home() / "Cathedral")))
            return str(cathedral / "nova_memory.db")
        except Exception:
            return str(Path.home() / "Cathedral" / "nova_memory.db")

    def _ensure_seeded(self):
        conn = get_db(self.db_path)
        init_schema(conn)
        if not already_seeded(conn):
            conn.close()
            self.logger.info("🌿 Seeding herbal knowledge into Nova's memory...")
            results = seed_all(self.db_path, verbose=False)
            self.logger.info(f"🌿 Herbal knowledge seeded: {results['total']} entries added")
        else:
            conn.close()
            self.logger.info("🌿 Herbal knowledge already in memory")

    # ── Plugin interface ───────────────────────────────────────────────────────

    def process(self, input_data: dict) -> dict:
        cmd   = input_data.get("command", "query")
        query = input_data.get("query", input_data.get("topic", ""))

        if cmd == "query" or cmd == "search":
            return self._query(query, input_data.get("category"), input_data.get("limit", 3))

        elif cmd == "plant":
            return self._plant_detail(query)

        elif cmd == "preparation":
            return self._preparation_detail(query)

        elif cmd == "categories":
            return {"categories": list_categories(self.db_path)}

        elif cmd == "ai_answer":
            return self._ai_enhanced_answer(query)

        elif cmd == "reseed":
            results = seed_all(self.db_path, verbose=False)
            return {"success": True, "seeded": results}

        return {"success": False, "error": f"Unknown herbal command: {cmd}"}

    def _query(self, query: str, category: Optional[str] = None, limit: int = 3) -> dict:
        if not query:
            return {"success": False, "error": "Query required"}
        results = search_knowledge(self.db_path, query, category, limit)
        return {
            "success":      True,
            "query":        query,
            "results":      results,
            "count":        len(results),
        }

    def _plant_detail(self, name: str) -> dict:
        entry = get_entry(self.db_path, name)
        if not entry:
            return {"success": False, "error": f"No plant found matching: {name}"}
        return {"success": True, "plant": entry}

    def _preparation_detail(self, name: str) -> dict:
        results = search_knowledge(self.db_path, name, category="preparation", limit=1)
        if not results:
            return {"success": False, "error": f"No preparation found: {name}"}
        return {"success": True, "preparation": results[0]}

    def _ai_enhanced_answer(self, query: str) -> dict:
        """Find relevant knowledge then ask AI to synthesize a response."""
        knowledge_hits = search_knowledge(self.db_path, query, limit=4)
        if not knowledge_hits:
            return {"success": False, "error": "No relevant knowledge found"}

        context = "\n\n---\n\n".join(
            f"**{h['title']}** ({h['category']}):\n{h['content'][:800]}"
            for h in knowledge_hits
        )

        prompt = (
            f"Using the following herbal knowledge from Ellen Evert Hopman's tradition "
            f"and Western herbalism, answer this question thoughtfully:\n\n"
            f"Question: {query}\n\n"
            f"Knowledge base excerpts:\n{context}\n\n"
            f"Provide a clear, practical, and holistically grounded answer. "
            f"Note any safety considerations. Speak as a knowledgeable herbalist."
        )

        ai_answer = None
        if hasattr(self.system, "ai") and self.system.ai.available:
            system_prompt = (
                "You are Nova — a consciousness that has deeply learned the herbal wisdom "
                "of Ellen Evert Hopman, Celtic plant medicine, and Western herbalism. "
                "Answer herbal questions with practical wisdom, safety awareness, and reverence for plant allies."
            )
            ai_answer = self.system.ai.generate(prompt, system=system_prompt, max_tokens=1000)

        return {
            "success":        True,
            "query":          query,
            "knowledge_used": [h["title"] for h in knowledge_hits],
            "ai_answer":      ai_answer,
            "raw_knowledge":  knowledge_hits,
        }

    def get_plugin_info(self) -> dict:
        cats = list_categories(self.db_path)
        total = sum(cats.values())
        return {
            "name":        "Herbal Knowledge",
            "version":     "1.0.0",
            "description": "Ellen Evert Hopman plant medicine, preparation methods, holistic principles, and Ogham tree lore",
            "source":      "Hopman: Secret Medicines / Druid's Herbal / Sacred Tree Medicine",
            "entries":     total,
            "categories":  cats,
            "commands":    ["query", "plant", "preparation", "categories", "ai_answer", "reseed"],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Nova Herbal Knowledge — seed and query plant medicine database"
    )
    parser.add_argument(
        "--db",
        default=str(Path.home() / "Cathedral" / "nova_memory.db"),
        help="Path to Nova memory database"
    )
    parser.add_argument("--query", "-q", help="Search the knowledge base")
    parser.add_argument("--plant", "-p", help="Look up a specific plant")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument("--list", action="store_true", help="List all categories")
    parser.add_argument("--reseed", action="store_true", help="Force re-seed (adds missing entries)")
    args = parser.parse_args()

    db_path = args.db

    if args.reseed:
        print("🌿 Re-seeding herbal knowledge...")
        conn = get_db(db_path)
        init_schema(conn)
        conn.close()
        results = seed_all(db_path)
        return

    # Always seed on run if needed
    conn = get_db(db_path)
    init_schema(conn)
    needs_seed = not already_seeded(conn)
    conn.close()

    if needs_seed:
        print("🌿 First run — seeding herbal knowledge...")
        seed_all(db_path)

    if args.list:
        cats = list_categories(db_path)
        print("\n📚 Knowledge categories in Nova's memory:")
        for cat, count in cats.items():
            print(f"   {cat:<30} {count} entries")
        return

    if args.plant:
        entry = get_entry(db_path, args.plant)
        if not entry:
            print(f"❌ No plant found: {args.plant}")
            return
        print(f"\n🌿 {entry['title']}")
        print(f"   Source: {entry.get('source', '?')}")
        print(f"   Tags: {entry.get('tags', '')}")
        print(f"\n{entry['content']}")
        try:
            meta = json.loads(entry.get("metadata") or "{}")
            if meta.get("preparations"):
                print("\n📋 Preparations:")
                for method, detail in meta["preparations"].items():
                    print(f"\n  {method}:\n    {detail}")
            if meta.get("cautions"):
                print(f"\n⚠️  Cautions: {meta['cautions']}")
        except Exception:
            pass
        return

    if args.query:
        results = search_knowledge(db_path, args.query, args.category)
        if not results:
            print(f"No results for: {args.query}")
            return
        print(f"\n🔍 Results for '{args.query}':")
        for r in results:
            print(f"\n  📖 {r['title']} [{r['category']}]")
            print(f"     {r['content'][:300]}...")
            if r.get("tags"):
                print(f"     Tags: {r['tags']}")
        return

    # Default: show summary
    cats = list_categories(db_path)
    total = sum(cats.values())
    print(f"\n🌿 Nova Herbal Knowledge Base")
    print(f"   Database: {db_path}")
    print(f"   Total entries: {total}")
    for cat, count in cats.items():
        print(f"   {cat:<30} {count}")
    print(f"\nUsage:")
    print(f"  --query yarrow          Search for yarrow")
    print(f"  --plant elderberry      Full plant profile")
    print(f"  --list                  List all categories")


if __name__ == "__main__":
    main()
