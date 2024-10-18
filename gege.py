"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""

import os

import google.generativeai as genai

genai.configure(api_key=os.environ["API_KEY"])

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

# TODO Make these files available on the local file system
# You may need to update the file paths
files = [
  upload_to_gemini('C:\\Users\\User\\제미나이 프로젝트\\gemini\\uploads\\gemini_logo_color.jpg', mime_type="image/jpeg"),
  upload_to_gemini('C:\\Users\\User\\제미나이 프로젝트\\gemini\\uploads\\gemini_logo_color.jpg', mime_type="image/jpeg"),
  upload_to_gemini('C:\\Users\\User\\제미나이 프로젝트\\gemini\\uploads\\gemini_logo_color.jpg', mime_type="image/jpeg"),
]


response = model.generate_content([
  "Extract the objects in the provided image and output them in a list in alphabetical order",
  "Image: ",
  files[0],
  "List of Objects: - airplane\n- coffee cup\n- eiffel tower\n- globe\n- keyboard\n- mouse\n- money\n- notebook\n- passport\n- pen\n- sunglasses\n- shopping cart\n- tablet",
  "Image: ",
  files[1],
  "List of Objects: - gardening gloves\n- rake\n- shovel\n- plants\n- pots\n- watering can",
  "Image: ",
  files[2],
  "List of Objects: ",
])

print(response.text)