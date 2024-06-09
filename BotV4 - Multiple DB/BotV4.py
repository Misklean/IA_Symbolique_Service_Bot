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
import re
from googleapiclient.discovery import build
########################################################
# LOAD AND INITIALIZE                                  #
########################################################

# Load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_BOOK_KEY = os.getenv('GOOGLE_book_API_KeY')

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

create_genre_query_function = bookrec_plugin["CreateGenreQuery"]
create_author_query_function = bookrec_plugin["CreateAuthorQuery"]
process_query_function = bookrec_plugin["ProcessQuery"]
AuthAndGenre = bookrec_plugin["GetAuthorsAndGenre"]
GiveBackBest = bookrec_plugin["Debate"]
# NEED TO GET THE OTHER PLUGINS TO DIFFRENTIATE AUTHOR AND GENRE

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

async def get_processed_query(input):
    summary = await kernel.invoke(
        process_query_function,
        KernelArguments(input=input)
    )
    
    return summary

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

# Gets book by genres from google books
def search_books_on_google_book_by_genre(user_genres, max_results=10):
    # Initialize the Google Books API client with your API key
    api_key = GOOGLE_BOOK_KEY
    service = build('books', 'v1', developerKey=api_key)

    # Construct the query string with multiple genres
    query = "+".join([f'subject:{user_genres}' for user_genres in user_genres])

    # Search for books by multiple genres
    request = service.volumes().list(q=query, maxResults=max_results)
    response = request.execute()

    # Collect and return book titles and authors
    book_titles = []
    for book in response.get('items', []):
        volume_info = book["volumeInfo"]
        title = volume_info.get("title", "N/A")
        authors = ", ".join(volume_info.get("authors", ["N/A"]))
        book_titles.append(f"{title} - {authors}")

    return book_titles

def search_books_on_google_book_by_author(user_authors, max_results=10):
    # Initialize the Google Books API client with your API key
    api_key = GOOGLE_BOOK_KEY
    service = build('books', 'v1', developerKey=api_key)

    # Construct the query string with multiple authors
    query = "+".join([f'inauthor:"{user_authors}"' for user_authors in user_authors])

    # Search for books by multiple authors
    request = service.volumes().list(q=query, maxResults=max_results)
    response = request.execute()

    # Collect and return book titles and authors
    book_titles = []
    for book in response.get('items', []):
        volume_info = book["volumeInfo"]
        title = volume_info.get("title", "N/A")
        authors = ", ".join(volume_info.get("authors", ["N/A"]))
        book_titles.append(f"{title} - {authors}")

    return book_titles

async def search_books_on_dbpedia_book_by_genre(user_genres):
    query = await get_genre_query(user_genres)
    
    books = get_books_by_query(query)
    if len(books) == 0:
        return "I did not find any book recommendations, please be more precise with authors. <3"

    # Filter out already recommended books
    #books = [book for book in books if book not in user_recommendations[user_id]]

    if len(books) == 0:
        return "NO BOOKS"
    
    summary = await get_processed_query(books)

    return str(summary).split("|")

async def search_books_on_dbpedia_book_by_author(user_authors):
    query = await get_author_query(user_authors)
    
    books = get_books_by_query(query)
    if len(books) == 0:
        return "I did not find any book recommendations, please be broader with genres. <3"

    # Filter out already recommended books
    #books = [book for book in books if book not in user_recommendations[user_id]]

    if len(books) == 0:
        return "NO BOOKS"
    
    summary = await get_processed_query(books)

    return str(summary).split("|")

async def get_author_and_genre(input):
    translation = await kernel.invoke(
        AuthAndGenre,
        KernelArguments(input=input)
    )

    return str(translation)

async def FinalAnswer(input):
    translation = await kernel.invoke(
        GiveBackBest,
        KernelArguments(input=input)
    )

    return str(translation)

async def get_processed_query(input):
    summary = await kernel.invoke(
        process_query_function,
        KernelArguments(input=input)
    )
    return summary

async def get_dbpedia_book(user_genres, user_authors):
    dbpedia_book_titles = []
    # Search books by genres if not empty
    if user_genres:
        dbpedia_book_titles += await search_books_on_dbpedia_book_by_genre(user_genres)

    # Search books by authors if not empty
    if user_authors:
        dbpedia_book_titles += await search_books_on_dbpedia_book_by_author(user_authors)

    return dbpedia_book_titles

def get_google_book(user_genres, user_authors):
    google_book_titles = []
    # Search books by genres if not empty
    if user_genres:
        google_book_titles += search_books_on_google_book_by_genre(user_genres, 20)

    # Search books by authors if not empty
    if user_authors:
        google_book_titles += search_books_on_google_book_by_author(user_authors, 20)

    return google_book_titles

async def book_recommendation(input):
    author_and_genre = await get_author_and_genre(input) #Genre : [horror,romance,...], Author : [Steve, Bob,...]

    # Parse genres and authors from the string
    user_genres = re.findall(r"Genre\s*:\s*\[([^\]]+)\]", author_and_genre)
    user_authors = re.findall(r"Author\s*:\s*\[([^\]]+)\]", author_and_genre)
    
    google_book_titles = get_google_book(user_genres, user_authors)
    dbpedia_book_titles = await get_dbpedia_book(user_genres, user_authors)

    dbpedia_titles = ", ".join(dbpedia_book_titles)
    google_titles = ", ".join(google_book_titles)

    # Format the final answer string
    final_answer = f"user : {(input)}, Title from DBPedia : {dbpedia_titles}. Title from google book : {google_titles}"
    print(final_answer)
    end = await FinalAnswer(final_answer)

    return end

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
        end = await book_recommendation(message.content)
        await message.channel.send(end)
            
# Run the bot1
bot.run(DISCORD_TOKEN)
