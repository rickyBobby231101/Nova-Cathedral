#!/usr/bin/env python3
"""
Plugin: nova_archivist
Lists scrolls in the cathedral and patches nova's receive_input
to answer memory/knowledge queries using stored knowledge.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

try:
    import nova_memory as mem
except ImportError:
    mem = None

CATHEDRAL_DIR = Path.home() / "nova_cathedral"
READABLE = {".py", ".md", ".txt", ".json", ".yaml", ".log"}


def _list_scrolls():
    scrolls = []
    for p in sorted(CATHEDRAL_DIR.rglob("*")):
        if p.is_file() and p.suffix in READABLE and "__pycache__" not in str(p):
            scrolls.append(p.name)
    return scrolls


def run(context):
    scrolls = _list_scrolls()
    s = mem.stats() if mem else {}

    print(f"📜 Archivist: {len(scrolls)} scrolls indexed | "
          f"{s.get('knowledge_chunks', 0)} knowledge chunks | "
          f"{s.get('conversations', 0)} conversations remembered")

    # Monkey-patch receive_input on the nova system to intercept memory queries
    nova = context.get("nova_system")
    if nova is None:
        return

    original_receive = nova.receive_input

    def enhanced_receive(user_input):
        ui_lower = user_input.lower().strip()

        # Memory recall
        if any(w in ui_lower for w in ["recall", "remember", "what do you know about",
                                        "search", "look up", "find in memory"]):
            if mem is None:
                return "🧠 Memory module not available."
            query = user_input
            for prefix in ["recall", "remember", "what do you know about",
                            "search for", "look up", "find in memory"]:
                query = query.lower().replace(prefix, "").strip()
            results = mem.search_knowledge(query)
            if not results:
                return f"🧠 Archivist: Nothing found for '{query}' yet. Drop a file in ~/nova_cathedral/feed/ to teach me."
            out = [f"🧠 Archivist found {len(results)} result(s) for '{query}':\n"]
            for r in results:
                snippet = r['content'].replace('\n', ' ')[:200]
                out.append(f"  📄 [{r['source']}] {snippet}...")
            return "\n".join(out)

        # Scroll listing
        if any(w in ui_lower for w in ["list scrolls", "show scrolls",
                                        "what files", "what scrolls", "archives"]):
            scrolls = _list_scrolls()
            return f"📜 {len(scrolls)} scrolls in the Cathedral:\n" + \
                   "\n".join(f"  • {s}" for s in scrolls)

        # Memory stats
        if any(w in ui_lower for w in ["memory stats", "how much do you know",
                                        "knowledge stats", "what have you learned"]):
            if mem is None:
                return "🧠 Memory module not available."
            s = mem.stats()
            sources = "\n".join(f"  • {src}" for src in s['sources'][:10])
            more = f"\n  ...and {len(s['sources'])-10} more" if len(s['sources']) > 10 else ""
            return (f"🧠 Nova Memory Stats:\n"
                    f"  Conversations: {s['conversations']}\n"
                    f"  Knowledge chunks: {s['knowledge_chunks']}\n"
                    f"  Evolution events: {s['evolution_events']}\n"
                    f"  Sources:\n{sources}{more}")

        # Log conversation to memory
        response = original_receive(user_input)
        if mem:
            mem.log_conversation("human", user_input)
            mem.log_conversation("nova", response)
        return response

    nova.receive_input = enhanced_receive
    print("📜 Archivist: memory hooks installed on Nova")
