# daily-lessons

A command-line tool that generates one deep daily learning lesson on a randomly selected topic, saves it as a dark-mode HTML page and Markdown file, and opens it in your browser.

Topics span physics, mathematics, medicine, chemistry, philosophy, history, linguistics, geography, paleontology, literature, and more — picked randomly each day from `domain_catalog.json`, which you can edit freely.

Each lesson follows a structured progression:

> **Hook** → **Prerequisites** → **Part I: Foundations** → **Part II: Mechanisms** → **Part III: Advanced Territory** → **Key Takeaways** → **Further Depth** → **Wikipedia & YouTube resources**

---

## What it looks like

Each lesson is a self-contained HTML page with a dark theme, domain-specific accent color, reading progress bar, and a tabbed resource section (Wikipedia + YouTube).

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/daily-lessons.git
cd daily-lessons
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Open `.env` and add your API key:

```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get a free key at [openrouter.ai](https://openrouter.ai). The default model is `deepseek/deepseek-chat` which is very affordable. Any OpenAI-compatible provider works — see `.env.example` for options including OpenAI and local Ollama models.

### 4. Run

```bash
python daily_lessons.py
```

A browser window opens with today's lesson. Files are saved to `~/knowledge_history/lessons/`.

---

## Schedule it

**Linux / macOS** — add to crontab (`crontab -e`):
```
0 7 * * * /usr/bin/python3 /path/to/daily_lessons.py
```

**Windows** — use Task Scheduler: create a Basic Task, trigger Daily at 07:00, action = `python C:\path\to\daily_lessons.py`.

---

## Customize topics

Edit `domain_catalog.json` to add, remove, or rebalance the topic catalog. The structure is:

```json
{
  "CATEGORY NAME": {
    "Subcategory": ["topic 1", "topic 2", "topic 3"]
  }
}
```

The model reads this catalog in full and picks one topic per day, actively avoiding recent repeats.

---

## Output structure

```
~/knowledge_history/
├── knowledge.db          ← SQLite: all lesson metadata + concept graph
├── lessons/
│   ├── 2025-03-01_the_higgs_mechanism.html
│   ├── 2025-03-01_the_higgs_mechanism.md
│   └── ...
└── logs/
    └── daily_lesson.log
```

---

## Compatible providers

| Provider | BASE_URL | Notes |
|----------|----------|-------|
| OpenRouter | `https://openrouter.ai/api/v1` | Access to 100+ models |
| OpenAI | `https://api.openai.com/v1` | Use `gpt-4o` or `gpt-4-turbo` |
| Ollama | `http://localhost:11434/v1` | Local models, set `API_KEY=ollama` |

---

## Requirements

- Python 3.9+
- An API key for any OpenAI-compatible LLM provider
- A browser
