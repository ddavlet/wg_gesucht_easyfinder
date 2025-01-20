# Munich Property Finder Bot

Welcome to the Munich Property Finder Bot! This bot is designed to help you find the perfect flat or house for rent or purchase in Munich.

## Features

- **Property Search**: Search for properties based on your criteria using the ImmoScout24 API.
- **Notifications**: Get notified when new offers match your preferences.
- **Multiple Finders**: Set up multiple finders to search for different types of properties or areas.
- **User Profile**: Manage your profile information and preferences.
- **Language Support**: Choose your preferred language from English, German, or Russian.

## Commands

- `/start`: Start the bot and see available commands.
- `/stop`: Pause notifications.
- `/delete_account`: Delete your account and all associated data.
- `/set_language`: Change the bot's language.
- `/set_address`: Set your preferred address for property searches.
- `/set_new_finder`: Create a new property search filter.
- `/help`: Get help and information about the bot.

## Getting Started

1. **Installation**: Clone the repository and install the required dependencies.
2. **Configuration**: Set up your environment variables for language files and API tokens.

### Required Environment Variables

- `LANGUAGE_FILE_EN`: Path to the English language file.
- `LANGUAGE_FILE_DE`: Path to the German language file.
- `LANGUAGE_FILE_RU`: Path to the Russian language file.
- `TOKEN`: Your bot's API token for authentication with the Telegram Bot API.

3. **Run the Bot**: Start the bot using the command `python main.py`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

