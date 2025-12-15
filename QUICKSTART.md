# Quick Start Guide

## Prerequisites

1. **Python 3.9+** installed
2. **Telegram Bot Token** from [@BotFather](https://t.me/botfather)
3. **Google AI API Key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
4. **Oxford Cardiology PDF** in `data/` folder

## Setup Steps

### 1. Clone and Navigate

```bash
git clone <your-repo>
cd cardiology-rag-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_AI_API_KEY=your_google_api_key_here
```

### 5. Add PDF Document

```bash
mkdir -p data
# Copy your Oxford Cardiology PDF to data/oxford_cardiology.pdf
```

### 6. Build Vector Store

```bash
python setup.py
```

This will:
- Extract text from PDF
- Generate embeddings
- Build ChromaDB vector store
- Test the RAG pipeline

Expected output:
```
📚 Processing document...
   ✅ Created XXX chunks

🔢 Generating embeddings...
   ✅ Generated XXX embeddings

💾 Building vector store...
   ✅ Vector store built successfully
   📊 Total documents: XXX

🧪 Testing RAG pipeline...
   ✅ RAG pipeline working
```

### 7. Run the Bot

```bash
python -m src.telegram_bot
```

You should see:
```
Bot is running! Press Ctrl+C to stop.
```

### 8. Test Your Bot

Open Telegram and:
1. Find your bot by username
2. Send `/start`
3. Ask a question: "What is atrial fibrillation?"

## Using Make Commands

If you have `make` installed:

```bash
# Install dependencies
make install

# Setup vector store
make setup

# Run the bot
make run

# Run tests
make test

# View logs
make logs
```

## Docker Deployment

### Build and Run

```bash
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f
```

### Stop

```bash
docker-compose down
```

## Troubleshooting

### "No text extracted from PDF"

- Check PDF is not corrupted
- Try a different PDF reader to verify content
- Check PDF is not image-only (requires OCR)

### "GOOGLE_AI_API_KEY not found"

- Verify `.env` file exists
- Check API key is correct
- Test API key at [Google AI Studio](https://makersuite.google.com)

### "TELEGRAM_BOT_TOKEN not found"

- Verify token from @BotFather
- Check `.env` file format
- No quotes around token value

### "Collection is empty"

- Run `python setup.py` first
- Check PDF processing completed successfully
- Verify `chroma_db` directory exists

### Bot not responding

- Check bot is running: `ps aux | grep telegram_bot`
- View logs: `tail -f logs/telegram_bot.log`
- Verify Telegram token is correct
- Check internet connection

### Slow responses

- Reduce `chunk_size` in `config/config.yaml`
- Decrease `top_k` retrieval results
- Enable caching in config
- Use faster embedding model

## Next Steps

1. **Customize prompts** in `config/config.yaml`
2. **Add more documents** to vector store
3. **Adjust chunk size** for better retrieval
4. **Enable streaming** for faster responses
5. **Add user analytics** tracking
6. **Deploy to cloud** (Heroku, AWS, etc.)

## Getting Help

- Check logs in `logs/` directory
- Review configuration in `config/config.yaml`
- Test components individually:
  - `python -m src.document_processor`
  - `python -m src.embeddings`
  - `python -m src.rag_pipeline`

## Common Commands

```bash
# Check vector store stats
python -c "from src.vector_store import VectorStore; vs = VectorStore(); print(vs.get_collection_stats())"

# Test RAG query
python -c "from src.rag_pipeline import RAGPipeline; p = RAGPipeline(); print(p.query('What is atrial fibrillation?'))"

# Clear vector store
python -c "from src.vector_store import VectorStore; vs = VectorStore(); vs.reset()"
```

## Support

For issues and questions, please open an issue on GitHub or contact the maintainer.
