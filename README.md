# Book Recommendation Discord Bot

## Presentation

This project is a Discord bot designed to recommend books based on user queries.

## How to Use the Bot

### Step 1: Install Required Libraries

Ensure you have Python 3.8 or later installed. Then, install the required libraries using pip:

```bash
pip install discord.py python-dotenv openai==0.27.0

```

### Step 2: Create a `.env` File

Create a `.env` file in your project directory with the following content:

```plaintext
DISCORD_TOKEN=yourDiscordToken
PROJECT_ID=a-novel-a-day-boredom-at--ogfn
GOOGLE_APPLICATION_CREDENTIALS=path/to/dialogflow-key.json
OPENAI_API_KEY=your_openai_api_key
```

Replace `yourDiscordToken` with your actual Discord bot token and `path/to/dialogflow-key.json` with the path to your Dialogflow service account JSON key file.

### Step 3: Save the Dialogflow Key File

Save the JSON key data you received from Google Cloud into a file named `dialogflow-key.json` and place it in the specified path in your `.env` file.

### Step 4: Run the Bot

To run your bot, execute the `main.py` script:

```bash
python main.py
```

### Step 5: Communicate with the Bot

To interact with your bot, send messages in any channel where the bot is present by tagging the bot in your message. For example:

```plaintext
@YourBotName recommend me a book
```

The bot will process your message and respond with a book recommendation.

### Note

Ensure your bot has the necessary permissions to read and send messages in the channels where it is invited. If the bot is not responding, check the logs for any error messages and verify the environment variables and paths are correctly set.