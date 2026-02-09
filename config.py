import os

# --- Gemini ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# --- RSS Feeds ---
AI_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
]

CRYPTO_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
]

MARKET_FEEDS = [
    "https://techcrunch.com/category/fintech/feed/",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
]

# --- Hacker News ---
HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
HN_AI_MIN_POINTS = 50
HN_CRYPTO_MIN_POINTS = 30

AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "gpt", "claude", "gemini",
    "machine learning", "deep learning", "neural", "transformer", "openai",
    "anthropic", "model", "training", "inference", "agent", "rag",
    "fine-tune", "diffusion", "multimodal",
]

CRYPTO_KEYWORDS = [
    "crypto", "bitcoin", "ethereum", "blockchain", "defi", "web3",
    "token", "nft", "solana", "layer 2", "zk", "rollup", "dao",
    "stablecoin", "wallet", "mining", "staking",
]

# --- YC ---
YC_API_URL = "https://yc-oss.github.io/api/companies/all.json"
YC_RECENT_BATCHES = [
    "W26", "S25", "X26", "W25", "S26",
    "Winter 2026", "Summer 2025", "Winter 2025", "Summer 2026",
]
YC_SECTOR_PRIORITY = {"ai": 3, "crypto": 1, "fintech": 1}
YC_COMPANIES_PER_DAY = 5

YC_AI_TAGS = [
    "artificial intelligence", "machine learning", "deep learning",
    "generative ai", "nlp", "computer vision", "ai",
]
YC_CRYPTO_TAGS = [
    "crypto", "blockchain", "defi", "web3", "cryptocurrency",
]
YC_FINTECH_TAGS = [
    "fintech", "payments", "banking", "insurance", "lending",
]

# --- Paths ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
ARCHIVE_DIR = os.path.join(OUTPUT_DIR, "archive")
STATE_FILE = os.path.join(PROJECT_DIR, "state.json")
LOG_DIR = os.path.join(PROJECT_DIR, "logs")
TEMPLATE_DIR = os.path.join(PROJECT_DIR, "builder", "templates")

# --- GitHub Pages ---
GITHUB_PAGES_URL = "https://realadii.github.io/morning-wire/"
GITHUB_REPO = "RealAdii/morning-wire"

# --- Email ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = os.environ.get("MW_EMAIL_FROM", "")
EMAIL_TO = os.environ.get("MW_EMAIL_TO", "")
EMAIL_APP_PASSWORD = os.environ.get("MW_EMAIL_APP_PASSWORD", "")

# --- Limits ---
MAX_ARTICLES_PER_FEED = 15
AI_SIGNAL_TOP_N = 7
MARKET_WIRE_TOP_N = 5
ARTICLE_AGE_HOURS = 48  # wider window to ensure content
