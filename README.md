# Munich Property Finder Bot

Welcome to the Munich Property Finder Bot! This bot is designed to help you find the perfect flat or house for rent or purchase in Munich.

## Features

- **Property Search**: Search for properties based on your criteria using the ImmoScout24 API.
- **Notifications**: Get notified when new offers match your preferences.
- **Multiple Finders**: Set up multiple finders to search for different types of properties or areas.
- **User Profile**: Manage your profile information and preferences.
- **Language Support**: Choose your preferred language from English, German, Russian, Greek, Turkish, Uzbek, Tajik, and Ukrainian.

## Current limitations


**WIP:**

I'm trying to make parser work indepedently, but I still face issues with recapcha. If you know how to solve recapcha, you are welcome to contribute. The deployment is not automated yet. If you have any questions, you can open question or text me directly. Overall it works fine and OK for personal use.

## Commands

- `/start`: Start the bot and see available commands.
- `/stop`: Pause notifications.

## Getting Started

1. **Installation**: Clone the repository and install the required dependencies.
2. **Configuration**: Set up your environment variables for language files, API tokens, and database connection.

### Required Environment Variables

#### Telegram Configuration
- `TELEGRAM_BOT_TOKEN`: Your bot's API token for authentication with the Telegram Bot API.

#### Language Files
- `LANGUAGE_FILE_EN`: Path to the English language file
- `LANGUAGE_FILE_DE`: Path to the German language file
- `LANGUAGE_FILE_RU`: Path to the Russian language file
- `LANGUAGE_FILE_EL`: Path to the Greek language file
- `LANGUAGE_FILE_TR`: Path to the Turkish language file
- `LANGUAGE_FILE_UZ`: Path to the Uzbek language file
- `LANGUAGE_FILE_TG`: Path to the Tajik language file
- `LANGUAGE_FILE_UK`: Path to the Ukrainian language file

#### MongoDB Configuration
- `MONGODB_URI`: MongoDB connection URI
- `MONGO_DB_NAME`: Name of the MongoDB database
- `MONGO_DB_ADMIN_USERNAME`: MongoDB admin username
- `MONGO_DB_ADMIN_PASSWORD`: MongoDB admin password
- `MONGO_HOST`: MongoDB host address
- `MONGO_PORT`: MongoDB port

#### Additional Settings
- `PARSER_INTERVAL`: Interval for parsing property listings (in milliseconds)
- `GOOGLE_MAPS_API_KEY`: API key for Google Maps services
- `TRANSLATOR_API_KEY`: API key for translation services

3. **Database Setup**: Ensure MongoDB is running and accessible with the provided credentials.
4. **Run the Bot**: Start the bot using the command `python main.py`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

