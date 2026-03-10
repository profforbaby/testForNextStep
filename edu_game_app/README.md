# Learn & Play - Educational App for Children

An educational application designed for Primary 1 (6-7 years old) children that encourages reading through gamification. Children earn game time by completing reading comprehension quizzes.

## Features

- **AI-Generated Content**: Unlimited reading passages tailored to your child's level using OpenAI API
- **Adaptive Difficulty**: Automatically adjusts difficulty based on performance (Levels 1-3)
- **Text-to-Speech**: Built-in reading assistance with adjustable speed
- **Quiz System**: 5 multiple-choice questions per passage, 80% required to pass
- **Game Time Rewards**: Earn 60 minutes of game time for each passed quiz
- **Parent Controls**: Password-protected settings and game management
- **Progress Tracking**: Detailed reports on reading progress and performance
- **Custom Game Launcher**: Control which games children can access

## Installation

### Prerequisites

- Python 3.11 or higher
- macOS (optimized for Mac Mini)
- OpenAI API key (optional, for AI-generated content)

### Step 1: Install Dependencies

```bash
cd edu_game_app
pip install -r requirements.txt
```

### Step 2: Set Up OpenAI API Key (Optional)

1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a `.env` file:

```bash
cp .env.example .env
```

3. Edit `.env` and add your API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Note**: The app will work without an API key using pre-made content, but won't have unlimited variety.

### Step 3: Run the Application

```bash
python app.py
```

## Usage

### For Children

1. **Start the app**: Launch the application
2. **Click "Start Reading"**: Get a new reading passage
3. **Read the passage**: Use "Read Aloud" button if needed
4. **Take the quiz**: Answer 5 questions about the passage
5. **Earn game time**: Score 80% or higher to earn 60 minutes
6. **Play games**: Click "Play Games" when you have time available

### For Parents

#### Accessing Parent Controls

1. Click **Settings → Parent Controls** in the menu
2. Enter password (default: `parent123`)
3. Access settings, game management, and reports

#### Parent Panel Features

**Settings Tab**:
- Change child's name
- Configure API key

**Allowed Games Tab**:
- Add games from `/Applications` folder
- Remove games from allowed list
- Only listed games can be launched

**Progress Report Tab**:
- View all quiz attempts
- See scores, difficulty levels, and time spent
- Export reports to text files

**Time Management Tab**:
- View current game time balance
- Manually adjust time (for special circumstances)
- Reset time to 0

## Configuration

### Default Password

- **Parent Password**: `parent123`
- To change: Edit in `config/settings.json`

### Difficulty Levels

- **Level 1**: 30-50 words, simple sentences, basic sight words
- **Level 2**: 50-80 words, compound sentences, more vocabulary
- **Level 3**: 80-100 words, descriptive language, challenging words

### Auto-Adjustment Rules

- **Level Up**: 3 consecutive quizzes with 90%+ score
- **Level Down**: 2 consecutive quizzes with <70% score

### Quiz Settings

- **Passing Score**: 80% (4 out of 5 questions)
- **Questions per Quiz**: 5
- **Time Earned**: 60 minutes per passed quiz

## Setting Up Auto-Launch on Startup

### macOS

1. Open **System Preferences → Users & Groups**
2. Select your child's user account
3. Click **Login Items** tab
4. Click **+** button
5. Navigate to the app and add it

Or create a launch agent:

1. Create file: `~/Library/LaunchAgents/com.eduapp.learnandplay.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.eduapp.learnandplay</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/edu_game_app/app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

2. Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.eduapp.learnandplay.plist
```

## Game Configuration

### Adding Allowed Games

1. Open Parent Controls (password required)
2. Go to "Allowed Games" tab
3. Click "Add Game"
4. Navigate to `/Applications`
5. Select game (e.g., Minecraft.app, Roblox.app)

**Supported formats**:
- macOS `.app` bundles
- Regular executables

### How Game Time Works

1. Child completes quiz with ≥80% score
2. Earns 60 minutes of game time
3. Time accumulates (can save up to 3 hours)
4. "Play Games" button becomes enabled
5. Child selects game to launch
6. Timer counts down
7. Game closes automatically when time expires

## Troubleshooting

### "OpenAI API key is required" Error

- Create `.env` file with your API key
- Or set environment variable: `export OPENAI_API_KEY=your-key`
- App will use fallback content if API key is missing

### Text-to-Speech Not Working

- Check system TTS is enabled in System Preferences
- Try adjusting speed with the slider
- Restart the application

### Can't Close Application

- Application requires parent password to close (security feature)
- Default password: `parent123`
- This prevents children from closing the app

### Games Not Launching

- Ensure game is in "Allowed Games" list
- Check game path is correct
- Verify game time balance is > 0
- Check game is not already running

## File Structure

```
edu_game_app/
├── app.py                  # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .env.example           # Environment variables template
├── config/
│   └── settings.json      # App configuration
├── data/
│   ├── models.py          # Data models
│   ├── database.py        # SQLite database
│   └── __init__.py
├── core/
│   ├── content_generator.py  # AI content generation
│   ├── tts_engine.py         # Text-to-speech
│   ├── difficulty.py         # Adaptive difficulty
│   ├── quiz_engine.py        # Quiz logic
│   ├── game_controller.py    # Game management
│   └── __init__.py
├── gui/
│   ├── main_window.py     # Main application window
│   ├── reading_widget.py  # Reading passage display
│   ├── quiz_widget.py     # Quiz interface
│   ├── timer_widget.py    # Game time display
│   ├── parent_panel.py    # Parent controls
│   └── __init__.py
└── resources/             # Icons and images (future)
```

## Database

The app uses SQLite database (`edu_app.db`) to store:
- Child profile and progress
- Reading passages and questions
- Quiz attempts and scores
- Game time balance and usage

**Backup**: Regularly backup `edu_app.db` file to preserve progress.

## Security Features

1. **Password-protected closure**: Prevents children from closing app
2. **Password-protected settings**: Only parents can change settings
3. **Game whitelist**: Only approved games can be launched
4. **Time enforcement**: Automatic game closure when time expires

## Tips for Parents

1. **Start at Level 1**: Even if your child reads well, start easy to build confidence
2. **Review progress weekly**: Check the Progress Report tab regularly
3. **Adjust games wisely**: Only allow age-appropriate games
4. **Encourage reading aloud**: Use the TTS feature for pronunciation help
5. **Celebrate milestones**: The app shows achievement messages
6. **Set daily limits**: Use manual time adjustment if needed

## Customization

### Change Parent Password

Edit `config/settings.json`:

```json
{
  "parent_password": "your-new-password"
}
```

### Adjust Time Rewards

Edit `config/settings.json`:

```json
{
  "time_per_quiz": 30  // Change from 60 to 30 minutes
}
```

### Modify Passing Score

Edit `config/settings.json`:

```json
{
  "quiz_passing_score": 0.7  // Change from 0.8 (80%) to 0.7 (70%)
}
```

## Future Enhancements

Potential features for future versions:
- Multiple child profiles
- Reading streak rewards
- Achievement badges
- Reading comprehension analytics
- Voice recording for reading practice
- Multiplayer quiz mode
- Integration with school curriculum

## Support

For issues or questions:
1. Check this README
2. Review error messages in the app
3. Check database permissions
4. Verify API key is set correctly

## License

This application is for personal/educational use.

## Credits

- Built with Python and PyQt6
- AI content powered by OpenAI GPT-4
- Text-to-speech using pyttsx3
- Icons: (to be added)

---

**Version**: 1.0.0
**Last Updated**: 2024
**Tested on**: macOS 12+, Python 3.11+
