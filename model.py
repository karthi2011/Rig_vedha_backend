import os
import google.generativeai as genai

genai.configure(api_key='AIzaSyDtYU2G1Nlzanf6FdhtwcEayy_Vh7hug5M'
)

# Get generator
models_gen = genai.list_models()

# Convert to list to print nicely
models = list(models_gen)

for model in models:
    print(model)
