#!/bin/bash

# ThreatScope Graceful Installation Script
# This script sets up the virtual environment, installs dependencies, and pulls AI models.
set -e

# Terminal Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}[*] Starting ThreatScope Installation...${NC}\n"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[-] Python 3 is not installed. Please install Python 3.8+ and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Python 3 detected.${NC}"

# 2. Setup Virtual Environment
echo -e "\n${BLUE}[*] Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# 3. Install Python Dependencies
echo -e "\n${BLUE}[*] Installing Python dependencies (CrewAI, Pydantic, etc.)...${NC}"
pip install --upgrade pip
pip install crewai pydantic jinja2 beautifulsoup4 flake8

# 4. Install Node.js Dependencies (ESLint)
echo -e "\n${BLUE}[*] Checking for npm to install ESLint...${NC}"
if command -v npm &> /dev/null; then
    echo -e "${GREEN}[+] npm detected. Installing ESLint globally...${NC}"
    npm install -g eslint
else
    echo -e "${YELLOW}[!] npm is not installed. ESLint parsing for JavaScript/TypeScript will be gracefully disabled during scans.${NC}"
fi

# 5. Check and Pull Ollama Models
echo -e "\n${BLUE}[*] Checking for Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}[+] Ollama detected. Pulling required AI models (this may take a moment)...${NC}"
    
    # Check if Ollama service is running by attempting to list models
    if ollama list >/dev/null 2>&1; then
        echo -e "    ${BLUE}-> Pulling qwen2.5:7b...${NC}"
        ollama pull qwen2.5:7b
        echo -e "    ${BLUE}-> Pulling nomic-embed-text...${NC}"
        ollama pull nomic-embed-text
    else
        echo -e "${YELLOW}[!] Ollama is installed but the service does not appear to be running.${NC}"
        echo -e "    Please start the Ollama application or daemon, then run:"
        echo -e "    ${NC}ollama pull qwen2.5:7b && ollama pull nomic-embed-text${NC}"
    fi
else
    echo -e "${RED}[!] Ollama is not installed.${NC}"
    echo -e "    ThreatScope requires Ollama for local LLM inference."
    echo -e "    Please download it from https://ollama.com/, start the service, and run:"
    echo -e "    ${NC}ollama pull qwen2.5:7b && ollama pull nomic-embed-text${NC}"
fi

echo -e "\n============================================="
echo -e "${GREEN}[+] Installation Complete!${NC}"
echo -e "============================================="
echo -e "${BLUE}[*] To start ThreatScope, run the following commands:${NC}\n"
echo -e "    ${GREEN}source venv/bin/activate${NC}"
echo -e "    ${GREEN}python main.py${NC}\n"
