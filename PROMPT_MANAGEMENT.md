# 📝 Prompt Management System

## Overview

System prompts are now managed in external files for easier editing and version control.

## File Structure

```
backend/
├── prompts/
│   └── system_prompt.txt      # Main system prompt
├── prompt_loader.py            # Prompt loading utilities
└── main.py                     # Uses prompts from files
```

## How It Works

### 1. **System Prompt File**
Location: `backend/prompts/system_prompt.txt`

This file contains the complete system prompt that defines:
- AI personality and tone
- Response formatting guidelines
- Example responses
- Conversation templates

### 2. **Prompt Loader**
Location: `backend/prompt_loader.py`

Provides utility functions:
```python
load_system_prompt(prompt_name="system_prompt")
# Loads prompt from file

get_system_content(similar_conversations="")
# Returns formatted prompt with variables filled in
```

### 3. **Main Application**
Location: `backend/main.py`

Loads prompt at startup:
```python
from prompt_loader import load_system_prompt

system_content = load_system_prompt("system_prompt")
```

## Benefits

### ✅ Easy Editing
- Edit `system_prompt.txt` directly
- No need to modify Python code
- Changes take effect on server reload

### ✅ Version Control
- Track prompt changes in Git
- Easy to diff changes
- Rollback to previous versions

### ✅ Multiple Prompts
- Create different prompts for different purposes
- Example: `casual_prompt.txt`, `formal_prompt.txt`, `english_prompt.txt`
- Switch between them easily

### ✅ Collaboration
- Team members can edit prompts without coding
- Clear separation of concerns
- Easier code reviews

## How to Edit the Prompt

### Method 1: Direct File Edit
1. Open `backend/prompts/system_prompt.txt`
2. Make your changes
3. Save the file
4. Restart the backend server

### Method 2: Hot Reload (Future Enhancement)
Add file watcher to reload prompts without restart:
```python
# In prompt_loader.py
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PromptReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.txt'):
            reload_prompts()
```

## Creating New Prompts

### Step 1: Create New Prompt File
```bash
# Create a new prompt file
echo "Your prompt content here" > backend/prompts/my_custom_prompt.txt
```

### Step 2: Load in Code
```python
custom_prompt = load_system_prompt("my_custom_prompt")
```

### Step 3: Use in Application
```python
# Use different prompts for different scenarios
if user_preference == "casual":
    prompt = load_system_prompt("casual_prompt")
elif user_preference == "formal":
    prompt = load_system_prompt("formal_prompt")
```

## Template Variables

The prompt supports template variables using Python's `.format()`:

```python
# In system_prompt.txt
"You have access to similar past conversations:
{similar_conversations}"

# In code
prompt = system_content.format(
    similar_conversations="Previous context here..."
)
```

### Available Variables:
- `{similar_conversations}` - Context from past similar conversations

### Adding New Variables:
1. Add placeholder in `system_prompt.txt`:
   ```
   User's preferred cuisine: {preferred_cuisine}
   ```

2. Update `get_system_content()` in `prompt_loader.py`:
   ```python
   def get_system_content(similar_conversations="", preferred_cuisine=""):
       template = load_system_prompt("system_prompt")
       return template.format(
           similar_conversations=similar_conversations,
           preferred_cuisine=preferred_cuisine
       )
   ```

## Best Practices

### 🎯 DO:
- ✅ Keep prompts in version control
- ✅ Use descriptive filenames
- ✅ Document prompt changes in Git commits
- ✅ Test prompts after major changes
- ✅ Keep backups of working prompts

### ❌ DON'T:
- ❌ Put sensitive data in prompts
- ❌ Make prompts too long (affects token usage)
- ❌ Forget to restart server after changes
- ❌ Edit prompts directly in production

## Testing Prompts

### Test Script
Create `test_prompt.py`:
```python
from prompt_loader import load_system_prompt

# Load and print prompt
prompt = load_system_prompt("system_prompt")
print("=" * 70)
print("SYSTEM PROMPT:")
print("=" * 70)
print(prompt)
print("=" * 70)
print(f"Length: {len(prompt)} characters")
print(f"Lines: {len(prompt.splitlines())} lines")
```

Run test:
```bash
cd backend
python test_prompt.py
```

## Advanced Usage

### Multilingual Prompts
```
prompts/
├── system_prompt_vi.txt    # Vietnamese
├── system_prompt_en.txt    # English
└── system_prompt_zh.txt    # Chinese
```

```python
# In code
language = user.get_language()  # 'vi', 'en', 'zh'
prompt = load_system_prompt(f"system_prompt_{language}")
```

### Role-Based Prompts
```
prompts/
├── system_prompt_casual.txt      # Friendly tone
├── system_prompt_professional.txt # Professional tone
└── system_prompt_expert.txt      # Expert reviewer
```

### Context-Aware Prompts
```python
def get_prompt_for_context(meal_time, user_type):
    """Get appropriate prompt based on context"""
    if meal_time == "breakfast":
        return load_system_prompt("breakfast_expert")
    elif user_type == "vegetarian":
        return load_system_prompt("vegetarian_guide")
    else:
        return load_system_prompt("system_prompt")
```

## Troubleshooting

### Prompt Not Loading
**Error:** `FileNotFoundError: Prompt file not found`

**Solution:**
1. Check file exists: `ls backend/prompts/`
2. Check filename matches: `system_prompt.txt` (no typo)
3. Check file path in code

### Formatting Issues
**Error:** `KeyError: 'similar_conversations'`

**Solution:**
1. Ensure all `{variables}` in prompt are provided
2. Use `{{` and `}}` for literal braces

### Encoding Issues
**Error:** `UnicodeDecodeError`

**Solution:**
Ensure file is saved as UTF-8:
```python
# In prompt_loader.py
with open(prompt_file, 'r', encoding='utf-8') as f:
    return f.read()
```

## Migration Guide

### From Hardcoded to File-Based

**Before:**
```python
system_content = (
    "You are a food expert...\n"
    "Answer in Vietnamese..."
)
```

**After:**
1. Create `prompts/system_prompt.txt` with content
2. Change code to:
   ```python
   from prompt_loader import load_system_prompt
   system_content = load_system_prompt("system_prompt")
   ```

## Future Enhancements

### Planned Features:
- [ ] Hot reload without server restart
- [ ] Prompt versioning with timestamps
- [ ] A/B testing different prompts
- [ ] Prompt analytics and metrics
- [ ] Web UI for prompt editing
- [ ] Prompt validation and linting

---

## Quick Reference

### Load Prompt:
```python
from prompt_loader import load_system_prompt
prompt = load_system_prompt("system_prompt")
```

### Edit Prompt:
```bash
# Edit file
nano backend/prompts/system_prompt.txt

# Restart server
# Changes will take effect
```

### Create New Prompt:
```bash
cp backend/prompts/system_prompt.txt backend/prompts/my_prompt.txt
# Edit my_prompt.txt
# Use: load_system_prompt("my_prompt")
```

---

**Now managing prompts is as easy as editing a text file!** 🎉
