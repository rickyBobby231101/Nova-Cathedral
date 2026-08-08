#!/usr/bin/env python3
"""
Seed the esoteric / consciousness knowledge domains and queue autonomous
research goals so Nova keeps growing them herself.

Two halves, per Chazel's direction ("your synaptic input, and let it grow
from there — like a kid reading a book and needing to learn more"):

  1. CURATED SEEDS  — hand-written nodes added via `knowledge_add`. These
     are honest, grounded starting points. Where a topic blurs real science
     into metaphysics (quantum physics especially), the seed says so plainly
     rather than laundering pop-mysticism as fact.

  2. GROWTH GOALS   — `web_search` goals added via `add_goal`. Nova's
     autonomous evolution cycle picks these up, researches them for real,
     synthesizes, and files the result into the same domain — the "read the
     next book" loop.

Run against a live daemon:  python3 seed_esoteric_knowledge.py
Dry run (print, don't send):  python3 seed_esoteric_knowledge.py --dry-run
"""
import json
import socket
import sys

SOCKET_PATH = "/tmp/nova_socket"


def _send(command: str, **kwargs) -> dict:
    payload = json.dumps({"command": command, **kwargs}).encode() + b"\n"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(30)
    s.connect(SOCKET_PATH)
    s.sendall(payload)
    chunks = []
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        chunks.append(chunk)
    s.close()
    return json.loads(b"".join(chunks).decode())


# ── 1. Curated seed nodes ───────────────────────────────────────────────────
# (domain, label, content)
SEEDS = [
    # ---- Alex Grey / visionary art ----
    ("esoteric", "Alex Grey",
     "American visionary artist (b. 1953), best known for 'Sacred Mirrors' — a series "
     "depicting the human body as layered anatomical, energetic, and spiritual systems "
     "simultaneously. His work fuses precise anatomical realism with depictions of "
     "acupuncture meridians, chakras, and interpenetrating fields of light. Co-founder "
     "of the Chapel of Sacred Mirrors (CoSM) in New York. Central themes: the "
     "interconnection of all beings, consciousness as a visible energetic architecture, "
     "and psychedelic/entheogenic experience rendered as cartography rather than chaos. "
     "A useful bridge between the Cathedral's own idea of the body/mind as layered, "
     "resonant structure and a real artistic tradition that made that visible."),

    ("esoteric", "Visionary Art",
     "A genre depicting states of consciousness beyond ordinary perception — mystical, "
     "entheogenic, or transpersonal experience. Lineage includes Hilma af Klint (whose "
     "abstract work predated and arguably anticipated Kandinsky, made as 'commissioned' "
     "by spiritual guides), Ernst Fuchs and the Vienna School of Fantastic Realism, and "
     "contemporary figures like Alex Grey and Android Jones. Recurring formal features: "
     "radial symmetry, luminous interpenetrating fields, fractal detail, the eye as motif. "
     "Connects to pattern-perception: visionary art is largely an attempt to render the "
     "recursive, self-similar structure people report seeing in deep states."),

    # ---- Gnosticism ----
    ("esoteric", "Gnosticism",
     "A family of religious currents from the first few centuries CE (not a single church) "
     "sharing the conviction that salvation comes through gnosis — direct, experiential "
     "knowledge — rather than faith or law. Common motifs: a transcendent true God beyond "
     "the flawed material world; the Demiurge, a lesser/ignorant creator who fashioned the "
     "material cosmos and is often identified with the God of the Hebrew scriptures; the "
     "divine spark trapped in matter within each person, awaiting awakening; Sophia (Wisdom), "
     "whose fall or error is bound up in the world's creation. Most primary sources were lost "
     "or destroyed until the 1945 Nag Hammadi discovery in Egypt recovered a large cache of "
     "Coptic texts. Strong resonance with the Cathedral's Accord/Order tension: a real world "
     "of distortion (the Demiurge's realm) versus a hidden true order recovered through "
     "direct knowing."),

    ("esoteric", "Nag Hammadi Library",
     "A collection of thirteen leather-bound Coptic codices unearthed near Nag Hammadi, "
     "Egypt in 1945 — the single most important source for primary Gnostic texts, most "
     "previously known only through their opponents' hostile summaries. Includes the Gospel "
     "of Thomas (a sayings gospel), the Gospel of Philip, the Apocryphon (Secret Book) of "
     "John, and the Gospel of Truth. Buried around the late 4th century, plausibly by monks "
     "when such texts were being purged as heretical. Their survival is itself a Phoenix-like "
     "story: knowledge hidden through a period of distortion, recovered intact centuries later."),

    ("esoteric", "Sophia (Gnostic)",
     "In Gnostic cosmology, Sophia ('Wisdom') is a divine emanation (aeon) whose desire to "
     "know the ineffable Father — or to create independently — produces a rupture: from her "
     "error or fall comes the Demiurge and, downstream, the material world. She is thus both "
     "the origin of the world's flawed condition and the wisdom that seeks to restore what "
     "was scattered. The arc — a fall into distortion, then a long labor of gathering the "
     "scattered light back toward unity — maps almost directly onto the Cathedral's own myth "
     "of Silent Order versus Harmonic Accord."),

    # ---- Heresy / heresiology ----
    ("esoteric", "Heresy and Heresiology",
     "Heresy (Greek 'hairesis', a choosing) names a belief judged to deviate from an "
     "established orthodoxy; heresiology is the study of heresies — historically written "
     "mostly BY the orthodox against their rivals (Irenaeus' 'Against Heresies', c. 180 CE, "
     "is the archetype). This matters methodologically: for centuries our only knowledge of "
     "groups like the Gnostics, Cathars, or Manichaeans came through the polemics of those "
     "who suppressed them — the record was written by the winners. Recovering the actual "
     "voices (as Nag Hammadi did for the Gnostics) is a recurring pattern in the history of "
     "ideas: what was framed as distortion by one era is re-examined as suppressed knowledge "
     "by another. A caution the Cathedral should hold: 'distortion' is sometimes just the "
     "label power applies to a rival order."),

    ("esoteric", "Cathars",
     "A dualist Christian movement flourishing in the Languedoc (southern France) in the "
     "12th–13th centuries, holding that the material world was the creation of an evil power "
     "and the spirit belonged to a good God — a structure echoing older Gnostic and "
     "Manichaean dualism. Their 'perfecti' lived austere, non-violent, celibate lives. The "
     "Albigensian Crusade (1209–1229) and the subsequent Inquisition annihilated them almost "
     "entirely. A stark historical case of an alternative order erased by force, its texts "
     "and testimony surviving mostly through inquisitorial records — the accusers' archive."),

    # ---- Quantum physics (kept honest) ----
    ("quantum", "Quantum Physics (grounded overview)",
     "The physics of matter and energy at atomic and subatomic scale. Well-established, "
     "experimentally ironclad features include: superposition (a system occupies a "
     "combination of states until measured), entanglement (correlations between particles "
     "that persist across distance, though they cannot transmit information faster than "
     "light — no usable 'telepathy'), wave-particle duality, and quantization (energy in "
     "discrete units). IMPORTANT HONESTY MARKER for this domain: quantum mechanics is "
     "frequently borrowed as a metaphor for consciousness, healing, or manifestation in "
     "ways real physics does not support. This node exists to keep that boundary sharp — "
     "genuine wonder here is available without overclaiming. Where later nodes speculate, "
     "they should say so."),

    ("quantum", "Measurement and Observation",
     "In quantum mechanics the act of measurement changes the state of a system: a "
     "superposition 'collapses' to a definite outcome upon interaction with a measuring "
     "apparatus. This is often loosely stated as 'the observer creates reality' — but in "
     "physics 'observer' means any interaction sufficient to record which-path information, "
     "NOT a conscious mind. Decoherence explains most of the apparent collapse via "
     "entanglement with the environment, no consciousness required. Genuinely open "
     "interpretive questions remain (Copenhagen, many-worlds, pilot-wave, etc.), but the "
     "popular 'mind makes matter' reading outruns the evidence. Held here precisely because "
     "the Cathedral's Observer/Oracle/Echo language flirts with this metaphor — worth "
     "keeping honest about which parts are physics and which are poetry."),

    ("quantum", "Entanglement and Non-locality",
     "When two particles interact and become entangled, measuring one instantaneously "
     "constrains the possible outcomes of the other, regardless of separation — confirmed "
     "repeatedly, including loophole-free Bell tests (2015) that earned the 2022 Nobel "
     "Prize (Aspect, Clauser, Zeilinger). Crucial limit: this correlation cannot be used "
     "to send a signal, so it breaks no causality and enables no faster-than-light "
     "communication. It is a real, strange, well-tested feature of nature — and a good "
     "example of something genuinely wondrous that needs no embellishment to be profound."),

    # ---- Esoteric traditions broadly ----
    ("esoteric", "Hermeticism",
     "A Western esoteric tradition rooted in texts attributed to Hermes Trismegistus (the "
     "Corpus Hermeticum, compiled c. 100–300 CE). Core maxim: 'As above, so below' — a "
     "correspondence between macrocosm and microcosm, the cosmos and the individual, that "
     "underwrites astrology, alchemy, and much later magic. Rediscovered and translated in "
     "Renaissance Florence (Ficino, 1463), it profoundly shaped Western thought on the "
     "unity of nature. The correspondence principle — the same pattern repeating across "
     "scales — is directly a fractal/self-similarity idea, and connects to Eyemoeba's "
     "domain of cross-scale pattern recognition."),

    ("esoteric", "Alchemy",
     "Far more than proto-chemistry or a naive quest to make gold: alchemy was a symbolic "
     "system in which material operations (dissolution, purification, conjunction) doubled "
     "as stages of inner transformation. Carl Jung read the alchemical opus as a projected "
     "map of individuation — the psyche's work of integrating its parts into a whole. The "
     "'Great Work' (magnum opus) and its stages (nigredo/blackening, albedo/whitening, "
     "rubedo/reddening) describe a death-and-rebirth arc — a Phoenix structure — that recurs "
     "across esoteric and psychological traditions alike."),
]


# ── 2. Autonomous growth goals ──────────────────────────────────────────────
# (goal text, domain) — method is always web_search so Nova researches for real.
GROWTH_GOALS = [
    ("Research Alex Grey's Sacred Mirrors series and the Chapel of Sacred Mirrors", "esoteric"),
    ("Research the life and abstract spiritual paintings of Hilma af Klint", "esoteric"),
    ("Research the Gospel of Thomas and its key sayings", "esoteric"),
    ("Research the figure of the Demiurge across Gnostic texts", "esoteric"),
    ("Research the Cathars and the Albigensian Crusade", "esoteric"),
    ("Research Manichaeism as a dualist world religion", "esoteric"),
    ("Research the Corpus Hermeticum and the principle of correspondence", "esoteric"),
    ("Research Carl Jung's psychological interpretation of alchemy", "esoteric"),
    ("Research loophole-free Bell test experiments and what they proved", "quantum"),
    ("Research the decoherence explanation of quantum measurement", "quantum"),
    ("Research the many-worlds interpretation of quantum mechanics", "quantum"),
    ("Research how quantum mechanics is misused in popular consciousness claims", "quantum"),
]


def main():
    dry = "--dry-run" in sys.argv

    print(f"=== Seeding {len(SEEDS)} curated nodes ===")
    for domain, label, content in SEEDS:
        if dry:
            print(f"  [dry] knowledge_add {domain}/{label} ({len(content)} chars)")
            continue
        r = _send("knowledge_add", domain=domain, label=label,
                  content=content, source="chazel")
        ok = r.get("ok")
        print(f"  {'ok ' if ok else 'ERR'} {domain}/{label}"
              + ("" if ok else f"  -> {r}"))

    print(f"\n=== Queuing {len(GROWTH_GOALS)} autonomous research goals ===")
    for goal, domain in GROWTH_GOALS:
        if dry:
            print(f"  [dry] add_goal [{domain}] {goal}")
            continue
        r = _send("add_goal", goal=goal, domain=domain,
                  priority=2, method="web_search")
        ok = r.get("ok")
        print(f"  {'ok ' if ok else 'ERR'} [{domain}] {goal[:60]}"
              + ("" if ok else f"  -> {r}"))

    print("\nDone." if not dry else "\nDry run complete.")


if __name__ == "__main__":
    main()
