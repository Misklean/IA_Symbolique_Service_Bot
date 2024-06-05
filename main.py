import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google.cloud import dialogflow_v2 as dialogflow
import uuid

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
PROJECT_ID = os.getenv('PROJECT_ID')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Set up Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS

# Set up Discord client
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Set up Dialogflow client
session_client = dialogflow.SessionsClient()

async def detect_intent_texts(project_id, session_id, text, language_code):
    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(request={"session": session, "query_input": query_input})
    return response.query_result.fulfillment_text

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    session_id = str(uuid.uuid4())
    response_text = await detect_intent_texts(PROJECT_ID, session_id, message.content, 'en-US')
    await message.channel.send(response_text)

# Run the bot
bot.run(DISCORD_TOKEN)
