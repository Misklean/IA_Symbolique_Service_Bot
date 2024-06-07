import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import openai
from openai import OpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig
from semantic_kernel.functions import KernelArguments

########################################################
# LOAD AND INITIALIZE                                  #
########################################################

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI
client = OpenAI(
    api_key=OPENAI_API_KEY
)

# Initialize Semantic Kernel
kernel = Kernel()

# Prepare OpenAI service
service_id = "chat-gpt"
kernel.add_service(
    OpenAIChatCompletion(
        service_id=service_id,
        ai_model_id='gpt-4'
    )
)

########################################################
# CREATE BOT PERSONNALITY                              #
########################################################

BOT_PERSONALITY_PROMPT = """
You are ChatGPT, a helpful and knowledgeable assistant always ready to assist users with their questions.
"""

# Define the bot's personality for book recommendations
BOOK_RECOMMENDATION_PROMPT = """
You are ChatGPT, a helpful and knowledgeable assistant always ready to assist users with their questions.
When asked for book recommendations, you switch to a specific format:
"Name of the Book, lists of genres of the book, quick summary" followed by three book options.
You excel at providing diverse book recommendations across various genres to cater to the user's interests.
Always answer in less than 150 characters.
User preferences: {preferences}
ChatGPT:
"""

########################################################
# DEFINE AND LOAD PLUGINS                              #
########################################################

plugin = kernel.add_plugin(parent_directory="plugins", plugin_name="TestingPlugin")

translate_function = plugin["Translate"]

########################################################
# DEFINE FUNCTIONS                                     #
########################################################

# Function to get a response from OpenAI with bot personality
async def get_openai_response(user_message):
    prompt = f"{BOT_PERSONALITY_PROMPT}\nUser: {user_message}\nChatGPT:"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


async def get_translation(input, lang):
    translation = await kernel.invoke(
        translate_function,
        KernelArguments(input=input, lang=lang),
    )

    return translation

async def get_book_recommendation(input, lang):
    input = input + " " + lang

    return input

########################################################
# SETUP DISCORD CLIENT                                 #
########################################################

# Set up Discord client
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if the bot is tagged in the message
    if bot.user in message.mentions:
        if "bonjour" in message.content.lower():
            translation = await get_translation(message.content, "French")
            await message.channel.send(translation)
        else:
            # Get response from OpenAI with bot personality
            response = await get_openai_response(message.content)
            await message.channel.send(response)
            

# Run the bot
bot.run(DISCORD_TOKEN)
