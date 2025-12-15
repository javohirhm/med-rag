"""
Telegram bot interface for the Cardiology RAG system.
"""
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.constants import ChatAction, ParseMode
from dotenv import load_dotenv
from loguru import logger
import yaml

from .rag_pipeline import RAGPipeline


class CardiologyBot:
    """Telegram bot for cardiology Q&A using RAG."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the bot.
        
        Args:
            config_path: Path to configuration file
        """
        load_dotenv()
        
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment")
        
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize RAG pipeline
        logger.info("Initializing RAG pipeline...")
        self.rag_pipeline = RAGPipeline(config_path=config_path)
        
        # User conversation history
        self.user_history: Dict[int, list] = {}
        
        # Bot statistics
        self.stats = {
            'total_queries': 0,
            'total_users': set(),
            'start_time': datetime.now()
        }
        
        logger.info("Cardiology Bot initialized successfully")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        user_id = user.id
        
        self.stats['total_users'].add(user_id)
        
        greeting = self.config['prompts']['greeting']
        
        await update.message.reply_text(
            greeting,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"User {user_id} ({user.username}) started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🏥 **Cardiology Assistant Help**

**What I can do:**
• Answer questions about cardiovascular medicine
• Provide information from the Oxford Handbook of Cardiology
• Explain medical terms and conditions
• Discuss treatment approaches

**How to use:**
Just send me your question in plain text!

**Example questions:**
• "What is atrial fibrillation?"
• "Explain the symptoms of heart failure"
• "What are the risk factors for coronary artery disease?"

**Commands:**
/start - Start the bot
/help - Show this help message
/clear - Clear conversation history
/stats - View bot statistics

**Important:**
⚠️ This bot provides educational information only.
For medical advice, always consult healthcare professionals.
In emergencies, call emergency services immediately!
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command to clear conversation history."""
        user_id = update.effective_user.id
        
        if user_id in self.user_history:
            del self.user_history[user_id]
            await update.message.reply_text(
                "✅ Conversation history cleared!"
            )
        else:
            await update.message.reply_text(
                "ℹ️ No conversation history to clear."
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command to show bot statistics."""
        uptime = datetime.now() - self.stats['start_time']
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        # Get RAG stats
        rag_stats = self.rag_pipeline.get_stats()
        
        stats_text = f"""
📊 **Bot Statistics**

**Usage:**
• Total queries: {self.stats['total_queries']}
• Total users: {len(self.stats['total_users'])}
• Uptime: {hours}h {minutes}m

**RAG System:**
• Documents indexed: {rag_stats['vector_store']['total_documents']}
• Embedding model: {rag_stats['embedding_model'].split('/')[-1]}
• LLM model: {rag_stats['llm_model']}
• Retrieval top-K: {rag_stats['top_k']}
        """
        
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages and provide answers."""
        user = update.effective_user
        user_id = user.id
        question = update.message.text
        
        logger.info(f"Query from {user_id}: {question[:100]}...")
        
        # Update stats
        self.stats['total_queries'] += 1
        self.stats['total_users'].add(user_id)
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        
        try:
            # Check if streaming is enabled
            enable_streaming = self.config.get('telegram', {}).get('streaming', False)
            
            if enable_streaming:
                # Stream response
                await self._handle_streaming_response(update, question)
            else:
                # Non-streaming response
                await self._handle_regular_response(update, question)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error processing your question. "
                "Please try again or rephrase your question."
            )
    
    async def _handle_regular_response(self, update: Update, question: str):
        """Handle non-streaming response."""
        # Query RAG pipeline
        result = self.rag_pipeline.query(
            question=question,
            stream=False,
            return_context=False
        )
        
        answer = result['answer']
        num_docs = result['retrieved_docs']
        
        # Format response
        response = f"{answer}\n\n_Retrieved from {num_docs} relevant sections_"
        
        # Split long messages
        if len(response) > 4096:
            # Split into chunks
            chunks = [response[i:i+4096] for i in range(0, len(response), 4096)]
            for chunk in chunks:
                await update.message.reply_text(
                    chunk,
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_streaming_response(self, update: Update, question: str):
        """Handle streaming response."""
        # Query RAG pipeline with streaming
        result = self.rag_pipeline.query(
            question=question,
            stream=True,
            return_context=False
        )
        
        # Send initial message
        message = await update.message.reply_text("💭 Thinking...")
        
        # Stream response
        full_response = ""
        chunk_buffer = ""
        last_update = datetime.now()
        
        for chunk in result['answer']:
            chunk_buffer += chunk
            full_response += chunk
            
            # Update message every 1 second or when buffer is large enough
            time_diff = (datetime.now() - last_update).total_seconds()
            if len(chunk_buffer) > 100 or time_diff > 1.0:
                try:
                    await message.edit_text(
                        full_response,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    chunk_buffer = ""
                    last_update = datetime.now()
                except Exception:
                    # Ignore telegram errors during streaming
                    pass
        
        # Final update
        footer = f"\n\n_Retrieved from {result['retrieved_docs']} relevant sections_"
        try:
            await message.edit_text(
                full_response + footer,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    def run(self):
        """Run the bot."""
        logger.info("Starting Cardiology Bot...")
        
        # Create application
        app = Application.builder().token(self.bot_token).build()
        
        # Register command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("clear", self.clear_command))
        app.add_handler(CommandHandler("stats", self.stats_command))
        
        # Register message handler
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))
        
        # Register error handler
        app.add_error_handler(self.error_handler)
        
        # Set bot commands
        async def post_init(app: Application):
            commands = [
                BotCommand("start", "Start the bot"),
                BotCommand("help", "Get help"),
                BotCommand("clear", "Clear conversation history"),
                BotCommand("stats", "View statistics")
            ]
            await app.bot.set_my_commands(commands)
        
        app.post_init = post_init
        
        # Start bot
        logger.info("Bot is running! Press Ctrl+C to stop.")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point."""
    # Setup logging
    logger.add(
        "logs/telegram_bot.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    
    try:
        bot = CardiologyBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
