# prompt_manager.py (updated)
from typing import List, Dict, Any
import json
from prompts import (
    SYSTEM_PROMPT_TOOLS_INTRO,
    SYSTEM_PROMPT_FORMATTING,
    SIMULATED_USER_CONTINUATION,  # Keep for reference but won't be used
    TOOL_OUTPUT_PREFIX
)

class PromptManager:
    """Manages prompt formatting and context accumulation using message dictionaries"""
    
    def __init__(self, tools: List[Dict[str, Any]], context_tail_length: int = 250):
        """Initialize prompt manager"""
        self.tools = tools
        self.context_tail_length = context_tail_length
        self.messages: List[Dict[str, str]] = [
            {
                'role': 'system',
                'content': f"""{SYSTEM_PROMPT_TOOLS_INTRO}
{json.dumps(self.tools, indent=2)}

{SYSTEM_PROMPT_FORMATTING}"""
            }
        ]
    
    def add_user_instruction(self, content: str):
        """Add initial user instruction"""
        self.messages.append({
            'role': 'user',
            'content': content
        })
    
    def append_assistant_content(self, content: str):
        """Append content to the current assistant message"""
        assistant_msgs = [m for m in self.messages if m['role'] == 'assistant']
        if assistant_msgs and not assistant_msgs[-1].get('completed', False):
            assistant_msgs[-1]['content'] += content
        else:
            self.messages.append({
                'role': 'assistant',
                'content': content,
                'completed': False
            })
    
    def complete_current_assistant(self):
        """Mark the current assistant message as complete"""
        assistant_msgs = [m for m in self.messages if m['role'] == 'assistant']
        if assistant_msgs and not assistant_msgs[-1].get('completed', False):
            assistant_msgs[-1]['completed'] = True
    
    def add_tool_output_as_user_message(self, tool_name: str, output: str):
        """Add tool output as a new user message"""
        self.messages.append({
            'role': 'user',
            'content': f"{tool_name}{TOOL_OUTPUT_PREFIX}{output}"
        })
    
    def add_feedback_as_user_message(self, feedback: str):
        """Add feedback agent response as a user message"""
        self.messages.append({
            'role': 'user',
            'content': feedback
        })
    
    def get_context_tail(self) -> str:
        """Get the last portion of the most recent assistant content"""
        assistant_msgs = [m for m in self.messages if m['role'] == 'assistant']
        if not assistant_msgs:
            return ""
        content = assistant_msgs[-1]['content']
        return (content[-self.context_tail_length:] 
                if len(content) > self.context_tail_length 
                else content)
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get the current message array"""
        return self.messages