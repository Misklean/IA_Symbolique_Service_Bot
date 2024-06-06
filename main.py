import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import openai
from openai import OpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig

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

# Define the request settings for Semantic Kernel
req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
req_settings.max_tokens = 150
req_settings.temperature = 0.7
req_settings.top_p = 0.8

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



# Function to generate book recommendations
async def get_book_recommendations(preferences: str) -> str:
    prompt = BOOK_RECOMMENDATION_PROMPT.format(preferences=preferences)
    
    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        name="book_recommendation",
        template_format="semantic-kernel",
        execution_settings=req_settings,
    )

    function = kernel.add_function(
        function_name="recommend_books",
        plugin_name="book_recommendation_plugin",
        prompt_template_config=prompt_template_config,
    )

    result = await kernel.invoke(function)
    return result

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
        if "greet" in message.content.lower():
            # Use the greeting plugin to greet the user
            await message.channel.send("Greeting !")
        else:
            # Default behavior using OpenAI response
            recommendations = await get_book_recommendations(message.content.lower())
            await message.channel.send(recommendations)

# Function to get a response from OpenAI
async def get_openai_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are ChatGPT, a helpful and knowledgeable assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# Run the bot
bot.run(DISCORD_TOKEN)
