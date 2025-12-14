# LinkedIn Insights Microservice

A robust backend microservice to fetch, store, and query LinkedIn company page insights.
Built with **SOLID principles** and modern **design patterns**.

## Features

- 🔍 **Scrape LinkedIn Pages**: Automatically fetch company page details, posts, comments, and employees
- 💾 **Persistent Storage**: SQL database (MySQL/SQLite) with proper relational schema
- 🤖 **AI-Powered Summaries**: Generate insights using Google Gemini (Bonus Feature)
- ⚡ **Caching with TTL**: Redis/in-memory caching with 5-minute TTL (Bonus Feature)
- 🚀 **RESTful APIs**: Well-designed endpoints with pagination and filtering
- 📖 **Auto Documentation**: Swagger UI via FastAPI
- 🐳 **Docker Support**: Full containerization with MySQL and Redis
- 📐 **SOLID Architecture**: Clean, maintainable, and extensible code

## Architecture & Design Patterns

### SOLID Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **S**ingle Responsibility | Each class has one job (e.g., `PageRepository` only handles page data access) |
| **O**pen/Closed | Add new cache backends or AI providers without modifying existing code |
| **L**iskov Substitution | `RedisCacheStrategy` and `MemoryCacheStrategy` are interchangeable |
| **I**nterface Segregation | Small, focused interfaces (`ICacheStrategy`, `IAIProvider`) |
| **D**ependency Inversion | High-level modules depend on abstractions via FastAPI `Depends()` |

### Design Patterns Used

```
┌─────────────────────────────────────────────────────────────────┐
│                    DESIGN PATTERNS                              │
├─────────────────────────────────────────────────────────────────┤
│  Strategy Pattern (Cache)          Factory Pattern (AI)        │
│  ┌───────────────────┐             ┌───────────────────┐       │
│  │  ICacheStrategy   │             │ AIProviderFactory │       │
│  └─────────┬─────────┘             └─────────┬─────────┘       │
│       ┌────┴────┐                       ┌────┴────┐            │
│   ┌───────┐ ┌────────┐             ┌────────┐ ┌────────┐       │
│   │ Redis │ │ Memory │             │ Gemini │ │ OpenAI │       │
│   └───────┘ └────────┘             └────────┘ └────────┘       │
├─────────────────────────────────────────────────────────────────┤
│  Repository Pattern                Dependency Injection        │
│  ┌───────────────────┐             ┌───────────────────┐       │
│  │  IPageRepository  │             │  FastAPI Depends  │       │
│  └─────────┬─────────┘             │  get_ai_provider  │       │
│       ┌────┴────┐                  │  get_cache_strategy│      │
│   ┌───────────────┐                │  get_page_service │       │
│   │SQLPageRepository│              └───────────────────┘       │
│   └───────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Project Structure (SOLID)

```
app/
├── core/                      # Abstractions & DI
│   ├── interfaces.py          # Protocol definitions (ISP)
│   └── dependencies.py        # FastAPI DI container (DIP)
│
├── services/
│   ├── cache/                 # Strategy Pattern
│   │   ├── base.py            # ICacheStrategy
│   │   ├── redis_cache.py     # RedisCacheStrategy
│   │   ├── memory_cache.py    # MemoryCacheStrategy
│   │   └── cache_manager.py   # Factory + Facade
│   │
│   ├── ai/                    # Factory Pattern
│   │   ├── base.py            # BaseAIProvider
│   │   ├── gemini_provider.py # Concrete implementation
│   │   └── ai_factory.py      # AIProviderFactory
│   │
│   └── page_service.py        # Service Layer
│
├── repositories/              # Repository Pattern
│   ├── page_repository.py
│   └── post_repository.py
│
└── routers/                   # API Layer (SRP)
    ├── pages.py
    └── ai.py                  # Uses Dependency Injection
```

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: MySQL (production) / SQLite (development)
- **ORM**: SQLAlchemy with async support
- **Caching**: Redis with in-memory fallback (Strategy Pattern)
- **AI**: Google Gemini (Factory Pattern)
- **Scraping**: Selenium + BeautifulSoup
- **Validation**: Pydantic



## Quick Start

### Prerequisites

- Python 3.10+
- MySQL (for production) or SQLite (for development - no setup needed!)
- Chrome/Chromium browser (for Selenium)

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd linkedin-insights
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database** (optional - SQLite works out of the box):
   
   For **SQLite** (default, no setup needed):
   ```bash
   # The database file will be created automatically
   # DATABASE_URL=sqlite+aiosqlite:///./linkedin_insights.db
   ```
   
   For **MySQL**:
   ```bash
   # Create the database first
   mysql -u root -p -e "CREATE DATABASE linkedin_insights;"
   
   # Set environment variable
   export DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/linkedin_insights
   ```

5. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Using Docker

```bash
# Start with Docker Compose (includes MySQL)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## API Endpoints

### Core Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pages/{page_id}` | GET | Get page details (scrapes if not in DB) |
| `/api/v1/pages/` | GET | Search pages with filters |
| `/api/v1/pages/{page_id}/posts` | GET | Get paginated posts |
| `/api/v1/pages/{page_id}/people` | GET | Get employees |
| `/api/v1/pages/{page_id}/comments` | GET | Get comments on posts |
| `/health` | GET | Health check endpoint |

### AI & Analytics (Bonus)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ai/summary/{page_id}` | GET | Get AI-powered page summary |
| `/api/v1/ai/cache/stats` | GET | Get cache statistics |
| `/api/v1/ai/cache/clear` | DELETE | Clear cached data |

### Query Parameters

**Search Pages** (`/api/v1/pages/`):
- `name`: Partial match on page name
- `industry`: Filter by industry
- `min_followers`: Minimum follower count
- `max_followers`: Maximum follower count
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10)

**AI Summary** (`/api/v1/ai/summary/{page_id}`):
- `include_posts`: Include posts in analysis (default: true)
- `include_employees`: Include employees in analysis (default: true)
- `skip_cache`: Force regenerate summary (default: false)


## Database Schema

```sql
-- Pages table
CREATE TABLE pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id VARCHAR(255) UNIQUE NOT NULL,
    linkedin_id VARCHAR(255),
    name VARCHAR(500) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    profile_picture_url VARCHAR(2000),
    description TEXT,
    website VARCHAR(1000),
    industry VARCHAR(255),
    follower_count INTEGER DEFAULT 0,
    headcount VARCHAR(100),
    specialities JSON,
    founded VARCHAR(50),
    headquarters VARCHAR(500),
    company_type VARCHAR(255),
    created_at DATETIME,
    updated_at DATETIME,
    scraped_at DATETIME
);

-- Posts table
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id VARCHAR(255) UNIQUE NOT NULL,
    page_id VARCHAR(255) REFERENCES pages(page_id),
    content TEXT,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    media_url VARCHAR(2000),
    media_type VARCHAR(50),
    post_url VARCHAR(2000),
    posted_at DATETIME,
    scraped_at DATETIME
);

-- Comments table
CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id VARCHAR(255) UNIQUE NOT NULL,
    post_id VARCHAR(255) REFERENCES posts(post_id),
    page_id VARCHAR(255) NOT NULL,
    author_name VARCHAR(500) NOT NULL,
    author_profile_url VARCHAR(1000),
    author_headline VARCHAR(500),
    content TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    commented_at DATETIME,
    scraped_at DATETIME
);

-- Employees table
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id VARCHAR(255) REFERENCES pages(page_id),
    name VARCHAR(500) NOT NULL,
    designation VARCHAR(500),
    location VARCHAR(500),
    profile_url VARCHAR(1000),
    profile_picture_url VARCHAR(2000),
    scraped_at DATETIME
);
```

## Project Structure

```
linkedin-insights/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # SQLAlchemy connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── repositories/        # Data access layer
│   └── routers/             # API endpoints
├── tests/                   # Test files
├── postman/                 # Postman collection
├── requirements.txt         # Dependencies
├── docker-compose.yml       # Docker setup
└── README.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./linkedin_insights.db` |
| `SCRAPER_HEADLESS` | Run browser headless | `true` |
| `SCRAPER_TIMEOUT` | Scraper timeout (seconds) | `30` |
| `DEBUG` | Enable debug mode | `true` |
| `GEMINI_API_KEY` | Google Gemini API key (for AI features) | `None` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CACHE_TTL` | Cache TTL in seconds | `300` (5 minutes) |
| `CACHE_ENABLED` | Enable/disable caching | `true` |


## Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Postman Collection

Import the Postman collection from `postman/LinkedIn_Insights.postman_collection.json` to test all endpoints.

## Limitations & Scraper Behavior

### LinkedIn Login Wall Detection

LinkedIn aggressively gates company pages behind authentication. The scraper includes validation guards to detect and handle this:

**Detection Mechanism:**
- Checks for login wall keywords ("Sign in", "Join LinkedIn", etc.)
- Validates company name is not a login page artifact
- Prevents storing invalid/garbage data

**Graceful Degradation:**
When a login wall is detected, the API returns:
```json
{
  "detail": {
    "error": "LinkedIn login wall detected",
    "message": "Page requires authentication to access full data",
    "page_id": "example-company",
    "url": "https://www.linkedin.com/company/example-company/",
    "retryable": false,
    "note": "LinkedIn aggressively gates company pages"
  }
}
```

**Why This Matters:**
- ✅ No invalid data is stored in the database
- ✅ Clear error messages for API consumers  
- ✅ Distinguishes between scraping errors and access restrictions

### Other Limitations

- **Rate Limiting**: LinkedIn may temporarily block repeated requests
- **Public Data Only**: Only publicly visible information is extracted
- **Dynamic Content**: Some data requires JavaScript rendering and may be incomplete
- **Comments**: Require complex browser interaction and are not fully supported

### Recommended Usage

For reliable data, consider:
1. **Manual Data Entry**: Add known company data directly to the database
2. **LinkedIn API**: Apply for official LinkedIn API access for production use
3. **Cached Results**: The system caches successful scrapes and serves from database

## License

MIT
