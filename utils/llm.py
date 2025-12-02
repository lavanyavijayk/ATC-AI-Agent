# from openai import OpenAI

# client = OpenAI(
#   base_url = "https://integrate.api.nvidia.com/v1",
#   api_key = "$NVIDIA_API_KEY"
# )

# completion = client.chat.completions.create(
#   model="qwen/qwen3-next-80b-a3b-thinking",
#   messages=[{"role":"user","content":""}],
#   temperature=0.6,
#   top_p=0.7,
#   max_tokens=4096,
#   stream=True
# )

# for chunk in completion:
#   reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
#   if reasoning:
#     print(reasoning, end="")
#   if chunk.choices[0].delta.content is not None:
#     print(chunk.choices[0].delta.content, end="")

API_KEY = "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"
# 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

import requests
import json

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer {API_KEY}",
    "Content-Type": "application/json",
    # "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    # "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  data=json.dumps({
    "model": "meta-llama/llama-3.3-70b-instruct:free",
    "messages": [
      {
        "role": "user",
        "content": "What is the meaning of life?"
      }
    ]
  })
)
# import pdb; pdb.set_trace()
print(response)
