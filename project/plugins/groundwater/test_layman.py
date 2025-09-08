from groundwater_plugin import answer_question

# Test user-friendly layman questions
print("=" * 60)
print("TESTING USER-FRIENDLY GROUNDWATER CHATBOT")
print("=" * 60)

test_questions = [
    "groundwater level in chennai",
    "water situation in tamil nadu", 
    "rainfall in andhra pradesh",
    "how much water is available in mumbai",
    "tell me about water in karnataka",
    "what areas have good water?",
    "show me water data for south india"
]

for question in test_questions:
    print(f"\n🗣️ User asks: \"{question}\"")
    print("─" * 50)
    try:
        answer = answer_question(question)
        print(f"🤖 Bot responds:\n{answer}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("\n" + "=" * 60)
