# Cardiology RAG Telegram Bot

A Retrieval-Augmented Generation (RAG) system for the Oxford Handbook of Cardiology, powered by Google Gemini 2.5 Flash and deployed as a Telegram bot.

## Features

- 📚 **RAG Pipeline**: Semantic search over cardiology handbook content
- 🤖 **Gemini 2.5 Flash**: Advanced LLM for medical question answering
- 💬 **Telegram Bot**: Easy-to-use interface for medical queries
- 🔍 **Vector Search**: Fast and accurate context retrieval using ChromaDB
- 📊 **Conversation History**: Maintains context across conversations
- 🌐 **Multilingual Support**: Ready for Uzbek, Russian, and English

## Architecture

```
User Question (Telegram)
    ↓
Question Processing & Embedding
    ↓
Vector DB Search (ChromaDB)
    ↓
Context Retrieval (Top-K chunks)
    ↓
Gemini 2.5 Flash (with context)
    ↓
Response to User
```

## Project Structure

```
cardiology-rag-bot/
├── data/
│   └── oxford_cardiology.pdf          # Source document
├── src/
│   ├── __init__.py
│   ├── document_processor.py          # PDF processing & chunking
│   ├── embeddings.py                  # Embedding generation
│   ├── vector_store.py                # ChromaDB vector store
│   ├── rag_pipeline.py                # RAG query pipeline
│   ├── llm_client.py                  # Gemini API client
│   └── telegram_bot.py                # Telegram bot interface
├── tests/
│   └── test_rag.py                    # Unit tests
├── notebooks/
│   └── rag_evaluation.ipynb          # RAG evaluation notebook
├── config/
│   └── config.yaml                    # Configuration file
├── requirements.txt
├── .env.example
├── setup.py
└── README.md
```

## Installation

### Prerequisites

- Python 3.9+
- Telegram Bot Token (from @BotFather)
- Google AI API Key (for Gemini 2.5 Flash)

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd cardiology-rag-bot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Process the document and build vector store**
```bash
python -m src.document_processor
```
> ⚠️ If the PDF fails to yield any text chunks, open it in Preview/Adobe to confirm it isn’t a scanned image. Run OCR (e.g., Adobe OCR or `ocrmypdf original.pdf ocr.pdf`) to embed selectable text, update `data/oxford_cardiology.pdf`, then rerun the setup step.

6. **Run the bot**
```bash
python -m src.telegram_bot
```

## Configuration

Edit `config/config.yaml` to customize:

- Chunk size and overlap
- Number of retrieved contexts (top-k)
- Embedding model
- LLM parameters (temperature, max tokens)
- Bot behavior

## Usage

### Basic Commands

- `/start` - Initialize the bot
- `/help` - Get help information
- `/clear` - Clear conversation history
- `/stats` - Get bot statistics

### Example Queries

```
Q: What are the symptoms of atrial fibrillation?
Q: Explain the management of acute coronary syndrome
Q: What are the indications for coronary angiography?
```

## RAG Pipeline Details

### 1. Document Processing

- Extracts text from PDF
- Splits into semantic chunks (500-1000 tokens with 100 token overlap)
- Preserves document structure and metadata

### 2. Embedding Generation

- Uses `text-embedding-004` from Google AI
- Generates 768-dimensional embeddings
- Batched processing for efficiency

### 3. Vector Store

- ChromaDB for persistent vector storage
- Cosine similarity search
- Metadata filtering capabilities

### 4. Query Pipeline

```python
# Query flow
1. User question → Embed question
2. Search vector store → Retrieve top-k relevant chunks
3. Build context from chunks
4. Send to Gemini with prompt template
5. Stream response back to user
```

### 5. LLM Integration

- Model: `gemini-2.5-flash`
- Temperature: 0.3 (for consistent medical responses)
- Safety settings: Configured for medical content
- Streaming enabled for better UX

## Prompt Engineering

The system uses a carefully crafted prompt template:

```
You are a medical assistant specializing in cardiology...
Context from Oxford Handbook of Cardiology:
{context}

Question: {question}

Provide accurate, evidence-based answers...
```

## Development

### Running Tests

```bash
pytest tests/
```

### Evaluating RAG Performance

```bash
jupyter notebook notebooks/rag_evaluation.ipynb
```

### Adding New Documents

```python
from src.document_processor import DocumentProcessor

processor = DocumentProcessor()
processor.process_document("path/to/new/document.pdf")
```

## Deployment

### Docker

```bash
docker build -t cardiology-bot .
docker run -d --env-file .env cardiology-bot
```

### Cloud Deployment

- **Heroku**: See `Procfile`
- **AWS**: Use EC2 or ECS
- **Google Cloud**: Use Cloud Run

## Performance Optimization

- **Caching**: Frequently asked questions cached
- **Batch Processing**: Embeddings generated in batches
- **Connection Pooling**: Efficient API usage
- **Async Operations**: Non-blocking I/O

## Monitoring

- Log all queries and responses
- Track response times
- Monitor API usage
- Alert on errors

## Security

- API keys stored in environment variables
- No logging of sensitive information
- Rate limiting implemented
- Input sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file

## Acknowledgments

- Oxford Handbook of Cardiology
- Google Gemini API
- Telegram Bot API
- ChromaDB

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Email: your.email@example.com

## Roadmap

- [ ] Multi-document support
- [ ] Advanced filtering (by topic, severity)
- [ ] Voice message support
- [ ] Image analysis integration
- [ ] Multi-language UI
- [ ] Analytics dashboard
- [ ] Export conversation to PDF
