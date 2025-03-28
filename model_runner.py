from ollama import chat
import logging
from typing import Generator, List, Dict, Any

class ModelRunner:
    """Handles model interaction and token generation using chat interface"""
    
    def __init__(self, model: str = 'llama3.2:3b'):
        """Initialize model runner
        
        Args:
            model (str): Model identifier
        """
        self.model = model
        self.logger = logging.getLogger(__name__)
        self.messages: List[Dict[str, str]] = []
    
    def generate_tokens(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Generate tokens from the model using chat interface
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            
        Yields:
            str: Individual tokens
        """
        try:
            # Update the message history with new messages
            self.messages = messages.copy()
            
            # Make chat request with streaming
            response = chat(
                model=self.model,
                messages=self.messages,
                stream=True,
                # options={
                #     "num_ctx": 40_000
                # }
            )
            
            # Collect full response for history
            full_response = ""
            for part in response:
                token = part['message']['content']
                full_response += token
                yield token
            
            # Add assistant response to history
            self.messages.append({
                'role': 'assistant',
                'content': full_response
            })
            
        except Exception as e:
            self.logger.error("Generation error: %s", str(e))
            raise
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the current message history
        
        Returns:
            List[Dict[str, str]]: List of message dictionaries
        """
        return self.messages
    
    def clear_history(self) -> None:
        """Clear the message history"""
        self.messages = []