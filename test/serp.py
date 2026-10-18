import os
import serpapi

api_key = os.environ.get("SERPAPI_API_KEY", "")
client = serpapi.Client(api_key=api_key)
results = client.search({
  "engine": "google",
  "q": "Entertainment"
})

print(results)