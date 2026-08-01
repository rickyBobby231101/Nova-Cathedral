def run(context):
    print(f"[Hello Plugin] Run ID: {context['run_id']}")
    print(f"[Hello Plugin] Timestamp: {context['timestamp']}")
    print("[Hello Plugin] Hello from the Nova plugin system!")
