from openai import OpenAI

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
def testerapi(api=None):

	for i, line in enumerate(api, start=1):
		api_key = line.strip()

		try:
			client = OpenAI(api_key=api_key)

			response = client.responses.create(
				model="gpt-4o-mini",
				input="ку"
			)

			print(f"{GREEN}[{i}] KEY WORKS ✅{RESET}  ")
			return True
		except Exception as e:
			print(f"{RED}[{i}] KEY FAILED ❌{RESET} {api_key}")
			return False
def testerfile(file="result.txt"):
	with open("result.txt", encoding="utf-8") as f:
		for i, line in enumerate(f, start=1):
			api_key = line.strip()

			try:
				client = OpenAI(api_key=api_key)

				response = client.responses.create(
					model="gpt-4o-mini",
					input="ку"
				)

				print(f"{GREEN}[{i}] KEY WORKS ✅{RESET}  ")
				return True
			except Exception as e:
				print(f"{RED}[{i}] KEY FAILED ❌{RESET} {api_key}")
				continue
				return False


if __name__ == "__main__":
	testerfile()