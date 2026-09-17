from darukaa.conversation import pipeline
from darukaa.conversation.controller import detect_named_domain


def main() -> None:
    db, store = pipeline.bootstrap()
    session_id = "cli"
    print("Darukaa.Earth AI Biodiversity Intelligence — type a message, or 'quit' to exit.")
    while True:
        message = input("> ").strip()
        if message.lower() in ("quit", "exit"):
            break
        named_domain = detect_named_domain(message)
        result = pipeline.run_turn(db, store, session_id, updates={}, named_domain=named_domain)
        if result["type"] in ("clarification", "no_match"):
            print(result["message"])
        else:
            print(f"\nWhat: {result['what']}")
            print(f"Why: {result['why']}")
            print(f"Impacted metrics: {', '.join(result['impacted_metrics'])}")
            print(f"Time horizon: {result['time_horizon']}  Confidence: {result['confidence']}")
            print(f"Limitations: {result['limitations']}")
            print("Evidence: " + "; ".join(e["source"] for e in result["evidence"]))


if __name__ == "__main__":
    main()
