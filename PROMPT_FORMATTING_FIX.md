# Prompt Formatting Fix for Local Llama Models

## Issue Summary

The chatbot agent was returning instruction fragments instead of proper responses when using local Llama models. Responses included fragments like:
- `"\n- Maintain a warm and friendly tone throughout."`
- `"\n- Use warm, professional language."`
- `"\n- Escalate appropriately if necessary"`

## Root Cause

The issue was in `/workspace/src/integrations/llm_providers.py` in the `generate_response` method. Local Llama models require specific prompt formatting but were receiving generic message-based prompts that they couldn't properly interpret.

### Original Problem:
```python
messages = []
if system_prompt:
    messages.append(SystemMessage(content=system_prompt))
messages.append(HumanMessage(content=prompt))
response = self.client.invoke(messages)
```

This approach works for cloud models (OpenAI, Anthropic) but not for local models that expect specific instruction formats.

## Solution Implemented

### 1. Added Model-Specific Prompt Formatting Method
Created `_format_prompt_for_local_model()` method that formats prompts according to each model type:

- **Llama models**: `[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_message} [/INST]`
- **Mistral models**: `[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_message} [/INST]` (official format with system prompt markers)
- **Fallback**: Simple concatenation for unknown types

**Note**: Both Llama and Mistral now use the same system prompt format with `<<SYS>>` markers, which is compatible across model versions and follows official specifications.

### 2. Updated Response Generation Logic
Modified `generate_response()` to detect local models and apply appropriate formatting:

```python
is_local_model = self.provider_type in ["llama", "local", "mistral"]

if is_local_model:
    formatted_prompt = self._format_prompt_for_local_model(prompt, system_prompt)
    response = self.client.invoke(formatted_prompt)
else:
    # Use message-based approach for cloud models
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))
    response = self.client.invoke(messages)
```

### 3. Added Comprehensive Logging
Added debug logging to track prompt formatting for troubleshooting:
- Model type detection
- Prompt length before and after formatting
- Format applied

## Results

### Before Fix:
```json
{
  "chatbot_response": "\n- Maintain a warm and friendly tone throughout.",
  "confidence": 0.85
}
```

### After Fix:
```json
{
  "chatbot_response": "I understand your frustration about the premium increase. Let me help explain what factors might have contributed to this change. Premium adjustments can occur due to various factors including...",
  "confidence": 0.9
}
```

## Testing Results

✅ **No more instruction fragments**: All test queries now return proper conversational responses
✅ **Improved response quality**: Responses are coherent, helpful, and contextually appropriate  
✅ **Maintained cloud model compatibility**: OpenAI and Anthropic models continue working unchanged
✅ **Eliminated warnings**: Removed duplicate `<s>` token warnings by letting models handle BOS tokens

## Files Modified

1. `/workspace/src/integrations/llm_providers.py`
   - Added `_format_prompt_for_local_model()` method
   - Updated `generate_response()` method with conditional formatting
   - Enhanced logging for debugging

## Model Configuration

The fix automatically detects model types from the configuration:

```yaml
# config/shared/models.yaml
models:
  llama-7b:
    type: llama  # Triggers Llama-specific formatting
  mistral-7b:
    type: mistral  # Triggers Mistral-specific formatting
```

## Future Considerations

1. **New Model Types**: Add formatting rules for new local model types as needed
2. **Performance**: Monitor if prompt formatting adds significant overhead
3. **Testing**: Ensure all model types are covered in integration tests

This fix resolves the core issue where local Llama models were echoing prompt instructions instead of following them to generate helpful customer service responses.