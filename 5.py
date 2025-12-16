from openai import OpenAI
import base64
# Установите ваш API ключ
api_key = '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'
client = OpenAI(api_key=api_key)
# Генерация изображения
response = client.images.generate(
    model="gpt-image-1",
    prompt="A futuristic city with flying cars and neon lights",
    size="1024x1024"
)

image_base64 = response.data[0].b64_json
image_bytes = base64.b64decode(image_base64)

with open("result.png", "wb") as f:
    f.write(image_bytes)

print("Изображение сохранено: result.png")