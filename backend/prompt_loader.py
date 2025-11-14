"""
Prompt management utilities
Load and manage system prompts from external files
"""

import os
from pathlib import Path

def load_system_prompt(prompt_name: str = "system_prompt") -> str:
    """
    Load system prompt from file
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        
    Returns:
        Prompt content as string
    """
    prompt_dir = Path(__file__).parent / "prompts"
    prompt_file = prompt_dir / f"{prompt_name}.txt"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def get_system_content(similar_conversations: str = "") -> str:
    """
    Get system prompt content with variables filled in
    
    Args:
        similar_conversations: Context from similar past conversations
        
    Returns:
        Formatted system prompt
    """
    template = load_system_prompt("system_prompt")
    return template.format(similar_conversations=similar_conversations)
