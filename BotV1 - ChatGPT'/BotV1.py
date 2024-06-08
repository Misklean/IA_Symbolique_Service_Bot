import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Set up Discord client
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Define the bot's personality
BOT_PERSONALITY = """
You are ChatGPT, a helpful and knowledgeable assistant always ready to assist users with their questions.
For general queries, you provide informative and relevant responses tailored to the user's inquiries.
However, when asked for book recommendations, you switch to a specific format:
"Name of the Book, lists of genres of the book, quick summary" followed by three book options.
You excel at providing diverse book recommendations across various genres to cater to the user's interests.
You always anszer in less than 150 characters.
"""

async def get_openai_response(prompt):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0125",  # Or use "gpt-4" if available
            messages=[
                {"role": "system", "content": BOT_PERSONALITY},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if the bot is tagged in the message
    if bot.user in message.mentions:
        response_text = await get_openai_response(message.content)
        await message.channel.send(response_text)

# Run the bot
bot.run(DISCORD_TOKEN)