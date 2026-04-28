from openai import OpenAI

# Initialize client
client = OpenAI(api_key="sk-proj-73z-Rt8cBbyRSSaDf079xaiVciuvAXA4IZAhvr" \
"iRoDbwb956gv5bfahboe1KXn2yGqoXB-9onCT3BlbkFJ7hjGBFPgPdKSXlr" \
"F68wObM5cVKK4Uvr7ozHYFmk4QYFY-FKeughQggLXGEli38QRchxiChPrsA")

print("Terminal ChatGPT (type 'exit' to quit)\n")

messages = [
    {"role": "system", "content": "You are a helpful assistant."}
]

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    # Add user message
    messages.append({"role": "user", "content": user_input})

    # Get response
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages
    )

    reply = response.choices[0].message.content

    print("Bot:", reply, "\n")

    # Save conversation
    messages.append({"role": "assistant", "content": reply})