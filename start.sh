#!/bin/bash
# Automated setup script for Cardiology RAG Bot

set -e

echo "=================================================="
echo "Cardiology RAG Bot - Automated Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo -e "${RED}Error: Python 3.9+ required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version${NC}"

# Check if .env exists
echo ""
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your API keys:${NC}"
    echo "   1. TELEGRAM_BOT_TOKEN (from @BotFather)"
    echo "   2. GOOGLE_AI_API_KEY (from Google AI Studio)"
    echo ""
    echo -e "${YELLOW}Press Enter after updating .env file...${NC}"
    read
fi

# Check if API keys are set
source .env
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo -e "${RED}Error: TELEGRAM_BOT_TOKEN not set in .env${NC}"
    exit 1
fi

if [ -z "$GOOGLE_AI_API_KEY" ] || [ "$GOOGLE_AI_API_KEY" = "your_google_ai_api_key_here" ]; then
    echo -e "${RED}Error: GOOGLE_AI_API_KEY not set in .env${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Environment configured${NC}"

# Create virtual environment
echo ""
echo -e "${YELLOW}Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check if PDF exists
echo ""
echo -e "${YELLOW}Checking for PDF document...${NC}"
if [ ! -f "data/oxford_cardiology.pdf" ]; then
    echo -e "${RED}Error: PDF not found at data/oxford_cardiology.pdf${NC}"
    echo "Please add the Oxford Cardiology PDF to the data/ directory"
    exit 1
fi
echo -e "${GREEN}✓ PDF document found${NC}"

# Check if vector store exists
echo ""
if [ ! -d "chroma_db" ] || [ -z "$(ls -A chroma_db)" ]; then
    echo -e "${YELLOW}Building vector store (this may take a few minutes)...${NC}"
    python setup.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Vector store built successfully${NC}"
    else
        echo -e "${RED}Error: Failed to build vector store${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Vector store exists${NC}"
fi

# All done
echo ""
echo "=================================================="
echo -e "${GREEN}Setup Complete! 🎉${NC}"
echo "=================================================="
echo ""
echo "To start the bot, run:"
echo -e "${YELLOW}  source venv/bin/activate${NC}"
echo -e "${YELLOW}  python -m src.telegram_bot${NC}"
echo ""
echo "Or use Make:"
echo -e "${YELLOW}  make run${NC}"
echo ""
echo "Or use Docker:"
echo -e "${YELLOW}  docker-compose up -d${NC}"
echo ""
echo "=================================================="
