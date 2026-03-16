# Learn & Play - Educational App for Children

An educational application designed for Primary school children that encourages reading through gamification. Children earn game time by completing reading comprehension quizzes.

## Features

- **AI-Generated Content**: Unlimited reading passages tailored to your child's level using Anthropic Claude API
- **Adaptive Difficulty**: Automatically adjusts difficulty based on performance (Levels 1–4)
- **Text-to-Speech**: Built-in reading assistance with adjustable speed
- **Quiz System**: 5 multiple-choice questions per passage, 80% required to pass
- **Game Time Rewards**: Earn 60 minutes of game time for each passed quiz
- **Daily Reset**: Game time resets to 0 every time the app is opened — child must earn time each day
- **Parent Controls**: Password-protected settings and game management
- **Progress Tracking**: Detailed reports on reading progress and performance
- **Game Blocking**: Automatically closes blocked games/apps when time runs out

---

## Platform Support

| Platform | Supported | Notes |
|----------|-----------|-------|
| Windows 10/11 | ✅ Yes | Run via `python run_edu_app.py` |
| macOS 12+ | ✅ Yes | Run via `python run_edu_app.py` or `run_app.sh` |

**`run_app.sh` and `setup_mac_autostart.sh` are macOS-only scripts — ignore them on Windows.**

---

## Installation

### Prerequisites

- Python 3.11 or higher
- Anthropic API key (optional — app works offline with built-in passages)

### Step 1: Install Dependencies

```bash
pip install -r edu_game_app/requirements.txt
```

On Windows, also install `pyttsx3` for text-to-speech:

```bash
pip install pyttsx3
```

### Step 2: Set Up Anthropic API Key (Optional)

1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Create a `.env` file inside the `edu_game_app/` folder:

```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**Note**: The app works without an API key using 26 built-in offline passages (Levels 1–4). The API key enables unlimited AI-generated passages.

### Step 3: Run the Application

```bash
python run_edu_app.py
```

Run this from the project root directory (the folder containing `run_edu_app.py`).

---

## Usage

### For Children

1. **Start the app** — launch with `python run_edu_app.py`
2. **Click "Start Reading"** — get a reading passage
3. **Read the passage** — use "Read Aloud" button if needed
4. **Take the quiz** — answer 5 questions about the passage
5. **Earn game time** — score 80% or higher to earn 60 minutes
6. **Play games** — click "Play Games" when you have time available

### For Parents

#### Accessing Parent Controls

1. Click **Settings → Parent Controls** in the menu
2. Enter password (default: `parent123`)
3. Access settings, game management, and reports

#### Parent Panel Features

**Settings Tab**: Change child's name, configure API key

**Allowed Games Tab**: Add/remove games the child is allowed to launch

**Progress Report Tab**: View quiz history, scores, difficulty levels, and time spent

**Time Management Tab**: View balance, manually adjust time, reset to 0

---

## Difficulty Levels

| Level | Words | Description | Suitable For |
|-------|-------|-------------|--------------|
| 1 | 30–50 | Simple sentences, basic sight words | Primary 1–2 |
| 2 | 50–80 | Compound sentences, common vocabulary | Primary 2–3 |
| 3 | 80–100 | Descriptive language, varied sentence structures | Primary 4–5 |
| 4 | 200–300 | Inference, vocabulary-in-context, critical thinking | Primary 6 / PSLE |

**Default starting level**: 4 (Primary 6)

### Auto-Adjustment Rules

- **Level Up**: 3 consecutive quizzes with 90%+ score
- **Level Down**: 2 consecutive quizzes with below 70% score

---

## Game Blocking

When a child's game time runs out, the app automatically closes blocked applications:

- **Browsers**: Chrome, Firefox, Edge, Opera, Brave, Safari
- **Games**: Minecraft Education Edition, Steam, Astroneer, GeForce NOW, CrossOver

---

## Setting Up Auto-Launch on Startup

### Windows

#### Method 1: Using the Startup Folder (Easiest)

A `run_app.bat` file is included in the project root. Use it to launch the app automatically on login.

1. Locate `run_app.bat` in the project folder (e.g. `C:\Users\YourName\PycharmProjects\testForNextStep\run_app.bat`)
2. Right-click `run_app.bat` → **Send to** → **Desktop (create shortcut)**
3. Press **Windows Key + R**, type `shell:startup`, click **OK** — this opens the user startup folder
4. Move or paste the shortcut from your Desktop into that startup folder

The app will now launch automatically every time Windows starts.

To test it without restarting, double-click `run_app.bat` directly.

### macOS

Run the provided setup script:

```bash
bash setup_mac_autostart.sh
```

Or manually add the app to **System Preferences → Users & Groups → Login Items**.

---

## Troubleshooting

### "API key not found" Warning

The app will still run using built-in offline passages. To enable AI content, add your Anthropic API key to `edu_game_app/.env`.

### Text-to-Speech Not Working (Windows)

Install pyttsx3:
```bash
pip install pyttsx3
```

### Text-to-Speech Not Working (macOS)

Check that **System Preferences → Accessibility → Spoken Content** is enabled.

### Still Showing Level 1 / "My Dog Max" Passage

The existing profile in the database may be saved at Level 1. The app now auto-upgrades any profile below Level 4 on startup. If this persists, delete `edu_app.db` and restart — a fresh profile will be created at Level 4.

### Can't Close Application

The app requires the parent password to close (security feature). Default password: `parent123`.

### Games Not Launching

- Ensure the game is in the "Allowed Games" list (Parent Controls)
- Verify the game time balance is greater than 0
- Check the game path is correct

---

## File Structure

```
testForNextStep/
├── run_edu_app.py              # Main entry point — run this
├── run_app.bat                 # Windows: double-click to launch, or use for auto-start
├── edu_game_app/
│   ├── requirements.txt        # Python dependencies
│   ├── README.md               # This file
│   ├── .env                    # API key (create this yourself)
│   ├── run_app.sh              # macOS-only launch script
│   ├── data/
│   │   ├── models.py           # Data models
│   │   ├── database.py         # SQLite database + seed passages
│   │   └── __init__.py
│   ├── core/
│   │   ├── content_generator.py   # AI content generation (Anthropic)
│   │   ├── tts_engine.py          # Text-to-speech (macOS: say, Windows: pyttsx3)
│   │   ├── difficulty.py          # Adaptive difficulty (Levels 1–4)
│   │   ├── quiz_engine.py         # Quiz logic
│   │   ├── game_controller.py     # Game launching and blocking
│   │   └── __init__.py
│   └── gui/
│       ├── main_window.py         # Main application window
│       ├── reading_widget.py      # Reading passage display
│       ├── quiz_widget.py         # Quiz interface
│       ├── timer_widget.py        # Game time display
│       ├── parent_panel.py        # Parent controls
│       └── __init__.py
└── setup_mac_autostart.sh      # macOS-only auto-start setup
```

---

## Database

The app uses SQLite (`edu_app.db`) stored in the project root. It contains:
- Child profile and current level
- Built-in seed passages (26 passages across Levels 1–4)
- Quiz attempts and scores
- Game time balance and session history

**Backup**: Copy `edu_app.db` to preserve your child's progress.

**Reset**: Delete `edu_app.db` to start fresh.

---

## Security Features

1. **Password-protected closure** — prevents children from closing the app
2. **Password-protected settings** — only parents can change settings
3. **Game whitelist** — only approved games can be launched
4. **Time enforcement** — automatic game closure when time expires
5. **Daily reset** — game time is zeroed each time the app starts

---

## Credits

- Built with Python and PyQt6
- AI content powered by Anthropic Claude
- Text-to-speech: macOS built-in `say` command / `pyttsx3` on Windows
- Database: SQLite

---

**Version**: 2.0.0
**Last Updated**: March 2026
**Tested on**: Windows 11, macOS 12+, Python 3.11+
