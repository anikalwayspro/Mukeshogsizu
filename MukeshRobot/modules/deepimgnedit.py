from MukeshRobot import pbot as mukesh  # Bot's client
from pyrogram import filters  # Pyrogram filters
from pyrogram.types import Message

import requests
from io import BytesIO
import pymongo

# For /help menu
__mod_name__ = "Image Generator and Editor"
__help__ = """
This module uses the DeepAI API to generate and edit images.

Commands:
/generate_image <text> - Generate an image based on the provided text.
/edit_image <text> - Reply to an image to edit it, optionally with text.
"""

API_KEY = '828195c8-896f-461b-9e0b-ca55203f3a44'

# Connect to the new MongoDB database for DeepAI operations
deepai_client = pymongo.MongoClient("mongodb+srv://deepaidb:51354579914@deepaidb.imzonfj.mongodb.net/?retryWrites=true&w=majority&appName=deepaidb")
deepai_db = deepai_client["deepai_db"]
image_generation_collection = deepai_db["image_generation"]
image_editing_collection = deepai_db["image_editing"]

@mukesh.on_message(filters.command("generate_image") & filters.text)
async def generate_image_command(_, message):
    text = message.text.split(' ', 1)[1] if ' ' in message.text else None

    if not text:
        await message.reply_text("Please provide the text to generate an image.")
        return

    # Make the API request to DeepAI
    try:
        response = requests.post(
            "https://api.deepai.org/api/text2img",
            data={'text': text},
            headers={'api-key': API_KEY}
        )
        response_json = response.json()

        if 'output_url' in response_json:
            image_url = response_json['output_url']

            # Download the generated image
            generated_image = requests.get(image_url).content

            # Save the generated image URL to the database
            image_generation_collection.insert_one({'text': text, 'image_url': image_url})

            # Send the generated image
            await message.reply_photo(BytesIO(generated_image))
        else:
            await message.reply_text("Sorry, something went wrong. Please try again.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

@mukesh.on_message(filters.command("edit_image"))
async def edit_image_command(_, message):
    if message.reply_to_message and message.reply_to_message.photo:
        await edit_image_reply(_, message)
    else:
        await message.reply_text("Please reply to an image to edit it. You can optionally provide text.")

async def edit_image_reply(_, message: Message):
    # Get the photo file ID
    photo_id = message.reply_to_message.photo.file_id

    # Get the file object
    photo = await message.reply_to_message.download()

    # Extract optional text from the command
    text = message.text.split(' ', 1)[1] if ' ' in message.text else None

    # Prepare the data for the API request
    data = {'text': text} if text else {}

    # Make the API request to DeepAI
    try:
        response = requests.post(
            "https://api.deepai.org/api/image-editor",
            files={'image': open(photo, 'rb')},
            data=data,
            headers={'api-key': API_KEY}
        )
        response_json = response.json()

        if 'output_url' in response_json:
            edited_image_url = response_json['output_url']

            # Download the edited image
            edited_image = requests.get(edited_image_url).content

            # Save the edited image URL to the database
            image_editing_collection.insert_one({'text': text, 'edited_image_url': edited_image_url})

            # Send the edited image
            await message.reply_photo(BytesIO(edited_image))
        else:
            await message.reply_text("Sorry, something went wrong. Please try again.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")
