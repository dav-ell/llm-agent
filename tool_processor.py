import re
import json
import time
import logging
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass

@dataclass
class ToolCall:
    """Represents a single tool call with its metadata"""
    id: str
    name: str
    content: str  # Changed from args_str to content for multi-line support
    start_pos: int
    end_pos: int
    output: Optional[str] = None
    executed: bool = False

class ToolProcessor:
    """Handles detection and execution of tool calls in text content"""
    
    def __init__(self, available_functions: Dict[str, callable]):
        """Initialize with available functions
        
        Args:
            available_functions (Dict[str, callable]): Dictionary of tool name to function
        """
        self.available_functions = available_functions
        # Updated pattern for multi-line tool calls: [tool_name]|||content|||
        self.tool_pattern = r'\[(\w+)\]\|\|\|(.*?)\|\|\|'
        self.logger = logging.getLogger(__name__)
        self.executed_tools: Dict[str, ToolCall] = {}  # Track tool calls by ID
    
    def find_unexecuted_tool_calls(self, text: str) -> List[ToolCall]:
        """Find all tool calls that haven't been executed yet
        
        Args:
            text (str): Text to search for tool calls
            
        Returns:
            List[ToolCall]: List of unexecuted tool calls
        """
        tool_calls = []
        for match in re.finditer(self.tool_pattern, text, re.DOTALL):
            tool_name = match.group(1)
            content = match.group(2).strip()
            start_pos = match.start()
            tool_id = f"tool_{start_pos}"  # Unique ID based on position
            
            if tool_id not in self.executed_tools:
                self.logger.info('Found new tool call: %s at position %d', match.group(), start_pos)
                tool_calls.append(ToolCall(
                    id=tool_id,
                    name=tool_name,
                    content=content,
                    start_pos=start_pos,
                    end_pos=match.end()
                ))
        
        return tool_calls
    
    def execute_tool(self, tool_call: ToolCall) -> str:
        """Execute a tool call and return the output limited to first 1000 characters
        
        Args:
            tool_call (ToolCall): The tool call to execute
            
        Returns:
            str: Tool execution output truncated to 1000 characters (if longer) and wrapped in <<< >>>
        """
        if function_to_call := self.available_functions.get(tool_call.name):
            try:
                # Try to parse content as JSON first (for backward compatibility)
                try:
                    args = json.loads(tool_call.content)
                except json.JSONDecodeError:
                    # If not JSON, treat as plain string appropriate to the tool
                    if tool_call.name == 'shell':
                        args = {'command': tool_call.content}
                    elif tool_call.name == 'run_python':
                        args = {'code': tool_call.content}
                    else:
                        raise ValueError("Content must be valid JSON for this tool")
                
                self.logger.info('Calling function: %s with ID: %s', tool_call.name, tool_call.id)
                self.logger.info('Arguments: %s', args)
                output = function_to_call(**args)
                self.logger.info('Function output: %s', output)
                # Truncate output to first 1000 characters if longer
                output_str = str(output).strip() if output else 'no output'
                truncated_output = output_str[:1000] if len(output_str) > 1000 else output_str
                formatted_output = f"<<< {truncated_output} >>>"
                return formatted_output
            except Exception as e:
                error_message = f"Error executing tool {tool_call.name}: {str(e)}"
                self.logger.error(error_message)
                # Truncate error message to first 1000 characters if longer
                truncated_error = error_message[:1000] if len(error_message) > 1000 else error_message
                return f"<<< {truncated_error} >>>"
        error_message = f"Error: Function {tool_call.name} not found"
        self.logger.error(error_message)
        # Truncate error message to first 1000 characters if longer
        truncated_error = error_message[:1000] if len(error_message) > 1000 else error_message
        return f"<<< {truncated_error} >>>"
    
    def process_text(self, text: str) -> Tuple[str, bool, Optional[ToolCall]]:
        """Process tool calls in the text and append outputs directly
        
        Args:
            text (str): Text to process
            
        Returns:
            Tuple[str, bool, Optional[ToolCall]]: (text with outputs appended, was_processed, executed_tool_call)
        """
        unexecuted_calls = self.find_unexecuted_tool_calls(text)
        if not unexecuted_calls:
            return text, False, None
            
        # Process the first unexecuted tool call
        tool_call = unexecuted_calls[0]
        output = self.execute_tool(tool_call)
        
        # Update tool call tracking
        tool_call.output = output
        tool_call.executed = True
        self.executed_tools[tool_call.id] = tool_call
        
        # Append output directly below tool call
        updated_text = f"{text}\n{tool_call.name} output:\n{output}"
        
        return updated_text, True, tool_call