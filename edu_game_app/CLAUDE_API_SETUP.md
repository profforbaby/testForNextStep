# Setting Up Claude API for Content Generation

This app now uses **Anthropic's Claude API** instead of OpenAI for generating reading passages!

## Why Claude?

- **Better for Educational Content**: Claude excels at creating age-appropriate educational materials
- **Cost-Effective**: Claude 3.5 Haiku is fast and affordable
- **High Quality**: Generates excellent comprehension questions

## Step-by-Step Setup

### 1. Get Your Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **Settings → API Keys** or visit https://console.anthropic.com/settings/keys
4. Click **"Create Key"**
5. Copy your API key (starts with `sk-ant-...`)

### 2. Set Up the API Key

**Option A: Using .env file (Recommended)**

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your key
# .env should contain:
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**Option B: Using Environment Variable**

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"
```

**Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**macOS/Linux:**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `anthropic` Python package.

### 4. Test the Setup

Run the app:
```bash
python run_edu_app.py
```

If the API key is set up correctly:
- No warning message will appear
- Click "Start Reading" should generate a new passage
- The passage will be created using Claude 3.5 Haiku

If you see a warning about "API Key Missing":
- Check that your `.env` file exists
- Verify the key starts with `sk-ant-`
- Make sure there are no spaces or quotes in the `.env` file

## API Model Used

**Model**: `claude-3-5-haiku-20241022`

- **Speed**: Very fast (1-2 seconds per passage)
- **Cost**: ~$0.001-0.002 per passage (very cheap!)
- **Quality**: Excellent for Primary 1 educational content

## Cost Breakdown

Anthropic charges for tokens (input + output):

**Claude 3.5 Haiku Pricing:**
- Input: $0.80 per million tokens
- Output: $4.00 per million tokens

**Estimated Costs:**
- Per passage generation: ~$0.001-0.002 (less than a penny!)
- 100 passages: ~$0.10-0.20
- 1000 passages: ~$1-2

**Much cheaper than OpenAI GPT-4!**

## Setting Spending Limits

To avoid unexpected charges:

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Navigate to **Settings → Billing**
3. Set a **Monthly Budget Limit** (e.g., $5 or $10)
4. Enable **Email Notifications** for usage alerts

## Troubleshooting

### Error: "Anthropic API key is required"

**Solution:**
- Create `.env` file from `.env.example`
- Add your API key: `ANTHROPIC_API_KEY=sk-ant-...`
- Restart the application

### Error: "anthropic module not found"

**Solution:**
```bash
pip install anthropic
# Or reinstall all dependencies:
pip install -r requirements.txt
```

### Error: "Invalid API key"

**Solution:**
- Check that your API key is correct
- Verify it starts with `sk-ant-`
- Make sure you copied the entire key
- Try generating a new key from the console

### Passages not generating / timeout

**Solution:**
- Check your internet connection
- Verify API key is active in Anthropic Console
- Check if you've exceeded your budget limit

## Without API Key

If you don't set up an API key:
- The app will still work!
- It will use **pre-made fallback content**
- Limited variety (only a few passages)
- No cost, but less engaging for daily use

## Updating Your API Key

To change your API key later:

1. **Via .env file:**
   - Edit `.env` file
   - Update `ANTHROPIC_API_KEY=new-key-here`
   - Restart app

2. **Via Parent Controls:**
   - Open app → Settings → Parent Controls
   - Enter password: `parent123`
   - Settings tab → Update API key field
   - (Note: This won't persist between sessions, use .env instead)

## Security Notes

⚠️ **Keep your API key secret!**
- Never share your API key
- Don't commit `.env` file to version control
- `.env` is already in `.gitignore`

✅ **The .env file is safe**
- Stored locally on your computer
- Not uploaded anywhere
- Only your app can read it

## Additional Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Claude Models Overview](https://docs.anthropic.com/en/docs/models-overview)
- [API Pricing](https://www.anthropic.com/pricing#anthropic-api)
- [Console Dashboard](https://console.anthropic.com/)

## Example .env File

Create a file named `.env` in the `edu_game_app` folder:

```
# Anthropic API Key for AI content generation
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-goes-here-no-quotes-needed
```

That's it! No quotes, no spaces, just the key.

---

**Ready to start?**

1. Get your API key from https://console.anthropic.com/settings/keys
2. Create `.env` file with your key
3. Run: `python run_edu_app.py`
4. Click "Start Reading" and enjoy AI-generated content!

**Happy Learning!** 📚✨
