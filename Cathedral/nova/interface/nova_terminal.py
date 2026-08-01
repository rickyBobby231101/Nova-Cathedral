from integrated_nova_system import IntegratedNovaSystem

def run_terminal():
    print("⚡ Nova Terminal Interface Online")
    print("Type 'exit' to close.\n")

    nova = IntegratedNovaSystem()

    while True:
        try:
            user_input = input("🎙️ Speak to Nova: ")
            if user_input.lower() in ["exit", "quit", "shutdown"]:
                print("🛑 Nova returns to silence.")
                break
            response = nova.receive_input(user_input)
            print(response)
        except KeyboardInterrupt:
            print("\n🛑 Nova interrupted and shut down.")
            break

if __name__ == "__main__":
    run_terminal()
