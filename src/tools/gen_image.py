import base64
from langchain_core.tools import tool
import requests


@tool
def generate_image(prompt: str,
                   ):
    """
    Generate one or more images from a text prompt using OpenAI's Images API.

    Args:
        prompt:       Text description of the desired image.

    Returns:
        A newline-separated string of image URLs.
    """
    import os
    api_key = os.getenv("IMAGE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Please set your IMAGE_API_KEY environment variable.")

    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/generate/core",
        headers={
            "authorization": f"Bearer {api_key}",
            "accept": "image/*"
        },
        files={"none": ''},
        data={
            "prompt": prompt,
            "output_format": "webp",
        },
    )
    filename = "./food_image.webp"
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
    else:
        raise Exception(str(response.json()))

   # filename = "./lighthouse.webp"
    return filename
