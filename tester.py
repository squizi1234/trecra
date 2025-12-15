from openai import OpenAI
with open("result.txt", encoding="utf-8") as f:
    for line in f:
        #print()
        #print(line)
        try:    
            api_key = line.strip()
            print(api_key)
            client = OpenAI(api_key=api_key)


            response = client.responses.create(
                model="gpt-4o-mini",
                input="ку"
            )
        except Exception as e:
            print(f"Error with API key {api_key}: {e}")
            continue

print(response.usage)
