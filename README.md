# Book Recommendation Discord Bot

## Presentation

This project is a Discord bot designed to recommend books based on user queries.

## How to Use the Bot

### Step 1: Install Required Libraries

Ensure you have Python 3.8 or later installed. Then, install the required libraries using pip:

```bash
pip install discord.py python-dotenv openai semantic-kernel sparqlwrapper google-api-python-client
```

### Step 2: Create a `.env` File

Create a `.env` file in your project directory with the following content:

```plaintext
DISCORD_TOKEN=yourDiscordToken
OPENAI_API_KEY=your_openai_api_key
GOOGLE_book_API_KeY=GoogleBooksAPIKey
```

Replace all those fields with your own keys.

### Step 3: Run the Bot

To run your bot, execute the `main.py` script:

```bash
python3 BotV4_Multiple_DB/BotV4.py
```

### Step 4: Communicate with the Bot

To interact with your bot, send messages in any channel where the bot is present by tagging the bot in your message. For example:

```plaintext
@YourBotName recommend me a book
```

The bot will process your message and respond with a book recommendation.

### Note

Ensure your bot has the necessary permissions to read and send messages in the channels where it is invited. If the bot is not responding, check the logs for any error messages and verify the environment variables and paths are correctly set.
