"""
LLM client for Google Gemini API.
"""
import os
from typing import Optional, Generator, Dict, Any
import time

import google.generativeai as genai
from loguru import logger


class GeminiClient:
    """Client for interacting with Google Gemini models."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.95,
        top_k: int = 40
    ):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Google AI API key
            model_name: Name of the Gemini model
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
        """
        self.api_key = api_key or os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key:
            raise ValueError("Google AI API key not found")
        
        genai.configure(api_key=self.api_key)
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.top_k = top_k
        
        # Configure generation settings
        self.generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k
        )
        
        # Configure safety settings for medical content
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"  # Allow medical discussions
            }
        ]
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        logger.info(f"GeminiClient initialized with model: {model_name}")
    
    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Generate a response from the model.
        
        Args:
            prompt: User prompt/question
            system_instruction: Optional system instruction
            stream: Whether to stream the response
            
        Returns:
            Generated response text
        """
        try:
            content = prompt
            if system_instruction:
                content = f"{system_instruction.strip()}\n\n{prompt}"
            
            if stream:
                response = self.model.generate_content(
                    content,
                    stream=True
                )
                full_response = ""
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                return full_response
            else:
                response = self.model.generate_content(
                    content
                )
                return response.text
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def generate_response_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from the model.
        
        Args:
            prompt: User prompt/question
            system_instruction: Optional system instruction
            
        Yields:
            Response text chunks
        """
        try:
            content = prompt
            if system_instruction:
                content = f"{system_instruction.strip()}\n\n{prompt}"
            
            response = self.model.generate_content(
                content,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            raise
    
    def chat(
        self,
        messages: list,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Have a multi-turn conversation.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_instruction: Optional system instruction
            
        Returns:
            Generated response
        """
        try:
            if system_instruction:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            # Start chat session
            chat = model.start_chat(history=[])
            
            # Add message history
            for msg in messages[:-1]:
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Send final message and get response
            response = chat.send_message(messages[-1]['content'])
            return response.text
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4


def main():
    """Example usage of GeminiClient."""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Setup logging
    logger.add(
        "logs/llm_client.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )
    
    try:
        print("\n" + "="*80)
        print("Gemini Client Test")
        print("="*80)
        
        # Initialize client
        client = GeminiClient(temperature=0.3)
        
        # Test basic generation
        print("\n1. Testing Basic Generation")
        print("-" * 80)
        
        prompt = "What is atrial fibrillation? Explain in 2-3 sentences."
        response = client.generate_response(prompt)
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")
        
        # Test with system instruction
        print("\n2. Testing with System Instruction")
        print("-" * 80)
        
        system_instruction = """You are a medical assistant specializing in cardiology.
        Provide clear, accurate, evidence-based information."""
        
        prompt = "What are the main risk factors for heart disease?"
        response = client.generate_response(
            prompt,
            system_instruction=system_instruction
        )
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")
        
        # Test streaming
        print("\n3. Testing Streaming Response")
        print("-" * 80)
        
        prompt = "Explain the pathophysiology of heart failure."
        print(f"Prompt: {prompt}")
        print("Streaming response: ", end="", flush=True)
        
        for chunk in client.generate_response_stream(prompt, system_instruction):
            print(chunk, end="", flush=True)
        print("\n")
        
        # Test token counting
        print("\n4. Testing Token Counting")
        print("-" * 80)
        
        text = "Coronary artery disease is a condition where the arteries supplying blood to the heart become narrowed or blocked."
        token_count = client.count_tokens(text)
        print(f"Text: {text}")
        print(f"Token count: {token_count}")
        
        print("\n✅ All Gemini client tests passed!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
