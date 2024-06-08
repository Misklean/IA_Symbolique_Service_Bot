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
from SPARQLWrapper import SPARQLWrapper, JSON

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
        ai_model_id='gpt-3.5-turbo-0125'
    )
)

genres = []

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

transalte_plugin = kernel.add_plugin(parent_directory="plugins", plugin_name="TestingPlugin")
bookrec_plugin = kernel.add_plugin(parent_directory="plugins", plugin_name="BookRecommendationPlugin")

translate_function = transalte_plugin["Translate"]
create_query_function = bookrec_plugin["CreateQuery"]
process_query_function = bookrec_plugin["ProcessQuery"]

# NEED TO GET THE OTHER PLUGINS TO DIFFRENTIATE AUTHOR AND GENRE

########################################################
# DEFINE FUNCTIONS                                     #
########################################################

# Function to get a response from OpenAI with bot personality
async def get_openai_response(user_message):
    prompt = f"{BOT_PERSONALITY_PROMPT}\nUser: {user_message}\nChatGPT:"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
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
        KernelArguments(input=input, lang=lang)
    )

    return translation

async def get_query(input):
    query = await kernel.invoke(
        create_query_function,
        KernelArguments(input=input, genres=genres)
    )
    print(query)
    return query

def get_books_by_query(query):
    # Create a SPARQLWrapper instance
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

    # Convert query to Unicode string
    query = str(query)

    # Set the query
    sparql.setQuery(query)

    # Set the return format
    sparql.setReturnFormat(JSON)

    # Execute the query and parse the results
    results = sparql.query().convert()

    books = []
    for result in results["results"]["bindings"]:
        book_title = result["title"]["value"]
        books.append(book_title)
    print(books)
    return books

async def get_processed_query(input):
    summary = await kernel.invoke(
        process_query_function,
        KernelArguments(input=input)
    )
    print(summary)
    return summary

async def get_book_recommendation(input):
    query = await get_query(input)
    books = get_books_by_query(query)
    summary = await get_processed_query(books)

    return summary

def get_genres():
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    query = """
    SELECT ?genre ?genreLabel (COUNT(?book) AS ?bookCount)
    WHERE {
    ?book a dbo:Book .
    ?book dbo:literaryGenre ?genre .
    ?genre rdfs:label ?genreLabel .
    FILTER (lang(?genreLabel) = 'en')
    }
    GROUP BY ?genre ?genreLabel
    ORDER BY DESC(?bookCount)
    LIMIT 50
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    genre_labels = []
    for result in results["results"]["bindings"]:
        genre_label = result["genreLabel"]["value"]
        genre_labels.append(genre_label)
    
    return genre_labels

########################################################
# SETUP DISCORD CLIENT                                 #
########################################################

# Set up Discord client
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    global genres
    # Call the function and print the list of genres
    genres = get_genres()
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
            summary = await get_book_recommendation(message.content)
            await message.channel.send(summary)
            
# Run the bot1
bot.run(DISCORD_TOKEN)
