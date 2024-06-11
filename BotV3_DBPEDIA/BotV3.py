import os
import re
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

# Dictionary to track user recommendations
user_recommendations = {}

########################################################
# DEFINE AND LOAD PLUGINS                              #
########################################################

transalte_plugin = kernel.add_plugin(parent_directory="plugins", plugin_name="TestingPlugin")
bookrec_plugin = kernel.add_plugin(parent_directory="plugins", plugin_name="BookRecommendationPlugin")

translate_function = transalte_plugin["Translate"]
create_genre_query_function = bookrec_plugin["CreateGenreQuery"]
create_author_query_function = bookrec_plugin["CreateAuthorQuery"]
process_query_function = bookrec_plugin["ProcessQueryFinalSummary"]
genre_or_author_function = bookrec_plugin["GenreOrAuthor"]

########################################################
# DEFINE FUNCTIONS                                     #
########################################################

async def get_genre_query(input):
    query = await kernel.invoke(
        create_genre_query_function,
        KernelArguments(input=input, genres=genres)
    )
    
    return query


async def get_author_query(input):
    query = await kernel.invoke(
        create_author_query_function,
        KernelArguments(input=input)
    )
    
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
    
    return books

async def get_processed_query(input):
    summary = await kernel.invoke(
        process_query_function,
        KernelArguments(input=input)
    )
    
    return summary

async def get_preference_type(input):
    pref_type = await kernel.invoke(
        genre_or_author_function,
        KernelArguments(input=input)
    )
    
    return str(pref_type)

async def get_book_recommendation(input, user_id):
    global user_recommendations

    pref_type = await get_preference_type(input)
    if pref_type == "AUTHOR":
        query = await get_author_query(input)
    elif pref_type == "GENRE":
        query = await get_genre_query(input)
    else:
        return "Please only talk about Books with me <3"

    books = get_books_by_query(query)
    if len(books) == 0:
        return "I did not find any book recommendations, please be more precise with authors, and broader with genres. <3"

    # Filter out already recommended books
    books = [book for book in books if book not in user_recommendations[user_id]]

    if len(books) == 0:
        return "NO BOOKS"
    
    summary = await get_processed_query(books)

    return str(summary)

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

def extract_books_from_summary(summary):
    print(summary)
    # Regex to find book names in quotes
    book_pattern = r'"([^"]+)"'
    books = re.findall(book_pattern, summary)
    return books

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

    user_id = message.author.id

    # Check if the bot is tagged in the message
    if bot.user in message.mentions:
        # Initialize user in dictionary if not present
        if user_id not in user_recommendations:
            user_recommendations[user_id] = []

        # Get response from OpenAI with bot personality
        summary = await get_book_recommendation(message.content, user_id)

        # Extract books from summary
        recommended_books = extract_books_from_summary(summary)

        # Update user recommendations
        user_recommendations[user_id].extend(recommended_books)
        print(user_recommendations[user_id])

        await message.channel.send("Bot Number 1: \n" + summary)
            
# Run the bot1
bot.run(DISCORD_TOKEN)