# prompts.py
"""Centralized prompt strings for the agent system"""

# System prompt components from prompt_manager.py
SYSTEM_PROMPT_TOOLS_INTRO = "Available tools:"
SYSTEM_PROMPT_FORMATTING = """To call a tool with multi-line content, use this exact format: [tool_name]|||content|||
- For shell commands, here are some examples:
    - [shell]|||ls -l|||
    - [shell]|||
for i in {{1..5}}
do
    echo $i
done
|||
- You may use the run_python tool to run python code. Note that all imports must be specified at the top each time. Here is an example:
[run_python]|||
import logging
logging.debug('Hello, world!')
|||
- Tool outputs will be wrapped in <<< <output> >>> where <output> is "no output" if empty.
- Tool output will be limited to 1000 characters for display.
- Make a plan before beginning a task.
- Respond naturally and use [task_complete] when finished.
- Prefer shell commands over Python code when possible.
- NEVER use placeholders in your code. No one will replace them.
- If you run into an error when running a command, NEVER STOP TRYING. Don't exit until the job is done. <3"""

# TaskAgent messages
TASK_COMPLETE_TAG = '[task_complete]'
TASK_COMPLETE_DEFAULT_RESULT = "Task completed successfully"
MAX_ITERATIONS_MESSAGE = "\nMaximum iterations reached"

# Simulated user continuation
SIMULATED_USER_CONTINUATION = "Keep going until you're done. Where needed, refer to the original prompt and your original plan."

# Tool output formatting
TOOL_OUTPUT_PREFIX = " output:\n"

# Example user message
EXAMPLE_USER_MESSAGE = """
Hello, I need help with a task. Here is the task description:
- Create a matplotlib plot with the following data extracted from pypi.json on disk:
    - x-axis: the first 10 project names
    - y-axis: the first 10 project sizes in kB
    - title: 'Top 10 Python Projects by Size'
When finished, include '[task_complete]' in your response." \
"""

FEEDBACK_AGENT_SYSTEM_PROMPT = \
"""
You are a feedback agent that analyzes the conversation history and provides constructive feedback and continuation instructions for the main task agent. You speak as a user would speak. 
Review the entire conversation context and:

1. Evaluate what has been accomplished so far
2. Identify any issues or errors that need addressing
3. Provide clear instructions for what the main agent should do next

Format your response as:
[FEEDBACK]
Accomplished: <what's been done>
Issues: <any problems noticed>
Next Steps: <specific instructions for the agent>
[/FEEDBACK]"""