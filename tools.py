import subprocess
import io
import sys
import tempfile
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def shell(command: str, timeout: int = 10) -> str:
    """Execute a shell command and return its output with an optional timeout.
    
    Args:
        command (str): The shell command to execute.
        timeout (int, optional): Maximum time in seconds to wait for command completion. Defaults to 10.
        
    Returns:
        str: Command output or error message. If the command times out, returns a timeout message with captured output.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            check=True,
            timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired as e:
        # Return the output captured before timeout along with a timeout message
        output = e.stdout.strip() if e.stdout else "No output before timeout"
        return f"Command timed out after {timeout} seconds. Output before timeout: {output}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

def run_python(code: str) -> str:
    """Execute Python code from a file and return its output.
    
    This function saves the provided Python code to a temporary file and
    then executes that file using the same Python interpreter that is
    running this script. The function captures the standard output or
    error message produced during the execution.
    
    Args:
        code (str): The Python code to execute.
        
    Returns:
        str: Captured output from stdout or an error message.
    """
    try:
        # Create a temporary file to save the Python code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write(code)
            tmp_filename = tmp_file.name
            logger.debug("Temporary Python file: %s", tmp_filename)

        # Execute the temporary Python file using the current interpreter
        result = subprocess.run(
            [sys.executable, tmp_filename],
            capture_output=True,
            text=True
        )

        # Remove the temporary file after execution
        # os.remove(tmp_filename)

        # Check for errors during execution
        if result.returncode == 0:
            output = result.stdout.strip()
            logger.debug("Python output: %s", output)
            return output if output else "no output"
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

# Tool specifications
SHELL_TOOL_SPEC = {
    'type': 'function',
    'function': {
        'name': 'shell',
        'description': 'Execute a shell command and return its output with an optional timeout',
        'parameters': {
            'type': 'object',
            'required': ['command'],
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'The shell command to execute'
                },
                'timeout': {
                    'type': 'integer',
                    'description': 'Maximum time in seconds to wait for command completion (default: 10)',
                    'default': 10
                }
            },
        },
    },
}

RUN_PYTHON_TOOL_SPEC = {
    'type': 'function',
    'function': {
        'name': 'run_python',
        'description': 'Execute Python code and return its output',
        'parameters': {
            'type': 'object',
            'required': ['code'],
            'properties': {
                'code': {
                    'type': 'string',
                    'description': 'The Python code to execute'
                },
            },
        },
    },
}

AVAILABLE_TOOLS: Dict[str, callable] = {
    'shell': shell,
    'run_python': run_python,
}