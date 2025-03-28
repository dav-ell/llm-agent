# agent.py (refactored)
import logging
from logging.handlers import RotatingFileHandler
from tool_processor import ToolProcessor
from prompt_manager import PromptManager
from model_runner import ModelRunner
from tools import AVAILABLE_TOOLS, SHELL_TOOL_SPEC, RUN_PYTHON_TOOL_SPEC
from prompts import (
    TASK_COMPLETE_TAG,
    TASK_COMPLETE_DEFAULT_RESULT,
    MAX_ITERATIONS_MESSAGE,
    EXAMPLE_USER_MESSAGE,
    FEEDBACK_AGENT_SYSTEM_PROMPT
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_handler = RotatingFileHandler("agent_context.log", maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.propagate = False

class TaskAgent:
    """Main agent class coordinating task execution"""
    
    def __init__(self, model: str = 'llama3.2:3b', max_iterations: int = 10):
        """Initialize the task agent"""
        self.tools = [SHELL_TOOL_SPEC, RUN_PYTHON_TOOL_SPEC]
        self.max_iterations = max_iterations
        self.tool_processor = ToolProcessor(AVAILABLE_TOOLS)
        self.prompt_manager = PromptManager(self.tools)
        self.model_runner = ModelRunner(model)
        self.feedback_runner = ModelRunner(model)
    
    def add_user_message(self, content: str):
        """Add initial user instruction"""
        self.prompt_manager.add_user_instruction(content)
    
    def should_continue(self, content: str) -> bool:
        """Check if the task should continue"""
        return TASK_COMPLETE_TAG not in content.lower() and self.max_iterations > 0
    
    def get_feedback(self, context_messages):
        """Get feedback from the feedback agent with logging"""
        feedback_messages = [{
            'role': 'system',
            'content': FEEDBACK_AGENT_SYSTEM_PROMPT
        }]
        feedback_messages.extend(context_messages)
        
        full_response = ""
        print("Feedback agent: ", end="", flush=True)
        for token in self.feedback_runner.generate_tokens(feedback_messages):
            full_response += token
            print(token, end="", flush=True)
        return full_response
    
    def print_context(self, messages, iteration):
        """Print the current message context"""
        print("-----------------------------")
        for msg in messages:
            print(f"{msg['role']}: {msg.get('content', '')}")
        print("-----------------------------")
        print(f"LLM Output (iteration #{iteration}): ", end="", flush=True)

    def process_tool_call(self, tool_call, tool_call_text):
        """Handle a processed tool call"""
        logger.info("Tool processed with buffer: %s", tool_call_text)
        self.prompt_manager.append_assistant_content(tool_call_text)
        self.prompt_manager.complete_current_assistant()
        self.prompt_manager.add_tool_output_as_user_message(tool_call.name, tool_call.output)
        feedback = self.get_feedback(self.prompt_manager.get_messages())
        print("\n----------")
        print(f"Command output: {tool_call.output}")
        print("\n----------")
        self.prompt_manager.add_feedback_as_user_message(feedback)
        print()

    def handle_generation_output(self, token_buffer, iteration):
        """Process the model's output and handle tool calls"""
        updated_buffer, tool_processed, tool_call = self.tool_processor.process_text(token_buffer)
        if tool_processed and tool_call:
            self.process_tool_call(tool_call, token_buffer)
            return True, ""
        return False, token_buffer

    def process_iteration(self, iteration):
        """Process a single iteration of the main loop"""
        messages = self.prompt_manager.get_messages()
        logger.info("Messages before generation: %s", messages)
        self.print_context(messages, iteration)
        
        token_buffer = ""
        try:
            for token in self.model_runner.generate_tokens(messages):
                token_buffer += token
                print(token, end="", flush=True)
                
                tool_processed, token_buffer = self.handle_generation_output(token_buffer, iteration)
                if tool_processed:
                    return False  # Continue to next iteration after tool processing
            
            # Check remaining buffer after generation
            tool_processed, token_buffer = self.handle_generation_output(token_buffer, iteration)
            if not tool_processed and token_buffer:
                self.prompt_manager.append_assistant_content(token_buffer)
            
            print()
            return self.check_completion()

        except Exception as e:
            return self.handle_error(e)

    def check_completion(self):
        """Check if the task is complete and return the result if so"""
        messages = self.prompt_manager.get_messages()
        assistant_msgs = [m for m in messages if m['role'] == 'assistant']
        logger.info("Messages after generation: %s", messages)
        
        if assistant_msgs and not self.should_continue(assistant_msgs[-1]['content']):
            content = assistant_msgs[-1]['content'].lower()
            task_complete_idx = content.find(TASK_COMPLETE_TAG)
            result = (assistant_msgs[-1]['content'][task_complete_idx + len(TASK_COMPLETE_TAG):].strip() 
                     or TASK_COMPLETE_DEFAULT_RESULT)
            logger.info("Task complete with result: %s", result)
            return result
        return None

    def handle_error(self, error):
        """Handle execution errors"""
        logger.error("Error during execution: %s", str(error))
        error_msg = f"\nError during execution: {str(error)}"
        self.prompt_manager.append_assistant_content(error_msg)
        self.prompt_manager.complete_current_assistant()
        feedback = self.get_feedback(self.prompt_manager.get_messages())
        print("\n----------")
        print(f"Command output: {error_msg}")
        print("\n----------")
        self.prompt_manager.add_feedback_as_user_message(feedback)
        return self.prompt_manager.get_messages()[-1]['content']

    def run(self) -> str:
        """Execute the task with streaming and tool processing"""
        logger.info('Initial prompt: %s', self.prompt_manager.get_messages()[1]['content'])
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info('Iteration %d:', iteration)
            
            result = self.process_iteration(iteration)
            if result is not None:
                return result
        
        logger.info("Maximum iterations reached")
        print("Maximum iterations reached")
        self.prompt_manager.append_assistant_content(MAX_ITERATIONS_MESSAGE)
        self.prompt_manager.complete_current_assistant()
        return self.prompt_manager.get_messages()[-1]['content']

if __name__ == "__main__":
    agent = TaskAgent(model="gemma3:27b", max_iterations=25)
    agent.add_user_message(EXAMPLE_USER_MESSAGE)
    result = agent.run()