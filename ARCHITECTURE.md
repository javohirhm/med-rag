# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                      (Telegram Client)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Telegram Bot Layer                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Command Handlers (/start, /help, /clear, /stats)     │  │
│  │  • Message Processing                                     │  │
│  │  • Streaming Response Management                         │  │
│  │  • Error Handling                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     RAG Pipeline Core                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Query Processing                                     │  │
│  │  2. Context Retrieval                                    │  │
│  │  3. Response Generation                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬────────────────────────────────────────┬──────────────┘
          │                                        │
          ▼                                        ▼
┌──────────────────────┐              ┌──────────────────────────┐
│   Vector Store       │              │    LLM Client            │
│   (ChromaDB)         │              │  (Gemini 2.5 Flash)      │
│                      │              │                          │
│  • Embeddings        │              │  • Text Generation       │
│  • Similarity Search │              │  • Streaming Support     │
│  • Metadata Filter   │              │  • Safety Settings       │
└──────────┬───────────┘              └──────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│   Document Processing                │
│                                      │
│  • PDF Extraction                   │
│  • Text Chunking                    │
│  • Embedding Generation             │
└──────────────────────────────────────┘
```

## Component Details

### 1. Document Processing Pipeline

**Components:**
- `DocumentProcessor`: PDF text extraction and chunking
- `EmbeddingGenerator`: Google AI embeddings

**Flow:**
```
PDF → Extract Text → Clean Text → Chunk → Generate Embeddings → Store
```

**Key Parameters:**
- Chunk Size: 800 characters
- Chunk Overlap: 200 characters
- Embedding Model: text-embedding-004 (768-dim)

### 2. Vector Store (ChromaDB)

**Purpose:** Efficient similarity search over document chunks

**Features:**
- Persistent storage
- Cosine similarity search
- Metadata filtering
- HNSW indexing for speed

**Operations:**
- `add_documents()`: Bulk insert with embeddings
- `search()`: k-NN similarity search
- `get_collection_stats()`: Monitoring

### 3. RAG Pipeline

**Core Logic:**
```python
def query(question):
    # 1. Embed query
    query_embedding = embed(question)
    
    # 2. Retrieve context
    docs = vector_store.search(query_embedding, top_k=5)
    context = format_context(docs)
    
    # 3. Generate answer
    prompt = f"Context: {context}\nQuestion: {question}"
    answer = llm.generate(prompt)
    
    return answer
```

**Configuration:**
- Top-K: 5 documents
- Similarity Threshold: 0.7
- Temperature: 0.3 (for consistency)

### 4. LLM Integration

**Model:** Gemini 2.5 Flash

**Advantages:**
- Fast inference
- Long context (1M tokens)
- Multilingual support
- Medical content safety

**Generation Config:**
```yaml
temperature: 0.3
max_tokens: 2048
top_p: 0.95
top_k: 40
```

### 5. Telegram Bot

**Features:**
- Command handling
- Streaming responses
- Conversation history
- Error recovery
- Statistics tracking

**Commands:**
- `/start`: Initialize
- `/help`: Show help
- `/clear`: Reset history
- `/stats`: Show statistics

## Data Flow

### Query Processing

```
User Message
    ↓
[1] Telegram API receives message
    ↓
[2] Bot handler processes command/text
    ↓
[3] RAG Pipeline: embed query
    ↓
[4] Vector Store: similarity search
    ↓
[5] Retrieve top-K relevant chunks
    ↓
[6] Format context with metadata
    ↓
[7] LLM: generate answer with context
    ↓
[8] Stream response back to user
    ↓
User receives answer
```

### Setup/Initialization

```
PDF Document
    ↓
[1] Extract text (pdfplumber)
    ↓
[2] Clean & normalize text
    ↓
[3] Split into chunks (800 chars, 200 overlap)
    ↓
[4] Generate embeddings (batch process)
    ↓
[5] Store in ChromaDB with metadata
    ↓
Ready for queries
```

## Performance Optimization

### Embedding Generation
- Batch processing (32 texts/batch)
- Rate limiting (0.1s delay between requests)
- Retry logic with exponential backoff

### Vector Search
- HNSW indexing for O(log n) search
- Configurable search parameters
- Metadata filtering for targeted search

### LLM Generation
- Streaming for better UX
- Context length optimization
- Caching frequent queries

### Bot Response
- Async message handling
- Typing indicators
- Message chunking for long responses

## Scalability Considerations

### Current Capacity
- ~10,000 document chunks
- 5-10 concurrent users
- ~100 queries/hour

### Scaling Options

**Horizontal:**
- Multiple bot instances
- Load balancer
- Shared vector store

**Vertical:**
- Larger vector store
- GPU acceleration
- Increased API limits

**Optimization:**
- Query result caching
- Embedding precomputation
- CDN for static assets

## Security & Privacy

### API Keys
- Environment variables
- Never in code/logs
- Rotation policy

### User Data
- No personal data stored
- Conversation history in memory
- GDPR compliant

### Content Safety
- Medical content filters
- Inappropriate content blocking
- Disclaimer in every response

## Monitoring & Logging

### Metrics Tracked
- Total queries
- Response times
- Error rates
- User count
- API usage

### Logs
- Request/response pairs
- Error traces
- System events
- Performance metrics

### Log Files
- `telegram_bot.log`: Bot operations
- `rag_pipeline.log`: RAG queries
- `document_processing.log`: Setup logs
- `setup.log`: Initialization logs

## Error Handling

### Graceful Degradation
- Vector store unavailable → Fallback message
- LLM API error → Retry with backoff
- Embedding failure → Skip problematic text

### User Communication
- Clear error messages
- Suggested actions
- Support contact info

## Configuration Management

### Files
- `config/config.yaml`: Main configuration
- `.env`: Secrets and API keys
- `requirements.txt`: Dependencies

### Hot Reload
- Config changes without restart
- Dynamic parameter adjustment
- A/B testing support

## Deployment Options

### Development
```bash
python -m src.telegram_bot
```

### Production

**Docker:**
```bash
docker-compose up -d
```

**Cloud:**
- Heroku: `git push heroku main`
- AWS ECS: Container deployment
- Google Cloud Run: Serverless

### CI/CD Pipeline
1. Code push
2. Run tests
3. Build Docker image
4. Deploy to staging
5. Run integration tests
6. Deploy to production

## Future Enhancements

### Planned Features
- [ ] Multi-document support
- [ ] Voice message handling
- [ ] Image analysis (ECG, X-rays)
- [ ] User feedback collection
- [ ] A/B testing framework
- [ ] Advanced analytics

### Potential Improvements
- RAG optimization (reranking)
- Better chunking strategies
- Multi-language support
- Context compression
- Fine-tuned embeddings
