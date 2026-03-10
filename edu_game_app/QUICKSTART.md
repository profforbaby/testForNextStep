# Quick Start Guide - Learn & Play

Get your child's educational app up and running in 5 minutes!

## 1. Install Python Dependencies

```bash
cd edu_game_app
pip install -r requirements.txt
```

## 2. (Optional) Set Up OpenAI API Key

For unlimited AI-generated content:

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Get key from: https://platform.openai.com/api-keys
nano .env  # or use any text editor
```

**Skip this step** if you want to use pre-made content only.

## 3. Run the App

```bash
python app.py
```

## 4. First Time Setup

When the app launches:

1. The default child name is "Student"
2. Default parent password is `parent123`
3. No games are configured yet

## 5. Configure Parent Settings

1. In the app, click **Settings → Parent Controls**
2. Enter password: `parent123`
3. **Settings Tab**: Change child's name
4. **Allowed Games Tab**: Add games from `/Applications`
   - Click "Add Game"
   - Navigate to `/Applications`
   - Select games like Minecraft.app, Roblox.app, etc.
5. Click "Close"

## 6. Test the App

1. Click **"Start Reading"** - Get a reading passage
2. Click **"Read Aloud"** - Hear the passage (optional)
3. Click **"Take Quiz"** - Answer 5 questions
4. **Score 80%+** - Earn 60 minutes of game time!
5. Click **"Play Games"** - Launch an allowed game

## Default Settings

- **Parent Password**: `parent123`
- **Passing Score**: 80% (4 out of 5 questions)
- **Time Reward**: 60 minutes per passed quiz
- **Starting Level**: Level 1 (easiest)

## Important Notes

⚠️ **To close the app**: You need the parent password!
- This prevents children from closing it themselves
- Default password: `parent123`

⚠️ **OpenAI API costs**:
- Each passage generation costs ~$0.01-0.02
- Consider this when setting up
- Or skip API and use pre-made content

## Troubleshooting

**Can't install dependencies?**
```bash
# Try upgrading pip first
pip install --upgrade pip
pip install -r requirements.txt
```

**App won't start?**
- Check Python version: `python --version` (should be 3.11+)
- Check dependencies: `pip list`
- Look for error messages

**No sound for TTS?**
- Check macOS System Preferences → Accessibility → Spoken Content
- Make sure system TTS is enabled

## Next Steps

- Read the full [README.md](README.md) for detailed instructions
- Set up auto-launch on startup (see README)
- Configure allowed games
- Review progress reports in Parent Controls

## Support

Check the main README.md for:
- Detailed feature descriptions
- Advanced configuration
- Auto-launch setup
- Game time management
- Progress tracking

---

Happy Learning! 📚✨
