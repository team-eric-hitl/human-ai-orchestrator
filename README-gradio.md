# HITL System - Gradio Demo

This is the Gradio version of the HITL (Human-in-the-Loop) AI System demo, converted from Streamlit with optimized processing logic and improved performance.

## 🚀 Key Features

### Optimized Processing Logic
- **Early Escalation Detection**: Critical frustration triggers immediate human routing (skips chatbot/quality analysis)
- **Efficient Workflow**: Context → Frustration → Early Check → (Chatbot → Quality → Final Check) OR (Direct Escalation)
- **Performance Gain**: Saves 2 LLM calls when immediate escalation is needed

### Real-time Interface
- **6-Panel Layout**: Chat, Logs, Frustration Analysis, Quality Analysis, Human Roster, Agent Profile, Escalation Context
- **Live Updates**: All panels update simultaneously during processing
- **Professional UI**: Clean Gradio interface with custom styling
- **Mobile Responsive**: Works well on different screen sizes

### AI Agents
- **Context Manager**: Gathers relevant conversation context
- **Frustration Agent**: Analyzes customer frustration levels (Claude Sonnet)
- **Chatbot Agent**: Generates customer service responses (Claude Haiku - fast)
- **Quality Agent**: Reviews and improves responses (Claude Sonnet)
- **Human Routing Agent**: Intelligent agent assignment (Claude Haiku)

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- API Keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (optional), `LANGCHAIN_API_KEY` (optional)

### Installation
```bash
# Install dependencies
pip install -r requirements-gradio.txt

# OR if using the existing project structure:
uv add gradio
```

### Environment Setup
Create a `.env` file with your API keys:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional
LANGCHAIN_API_KEY=your_langchain_api_key_here  # Optional for tracing
LANGCHAIN_TRACING_V2=true  # Optional for tracing
```

## 🚀 Running the App

### Local Development
```bash
# Run the Gradio app
python gradio_demo.py

# Or run tests first
python test_gradio_basic.py
```

The app will be available at: `http://localhost:7860`

### Production Deployment

#### Option 1: Hugging Face Spaces (Recommended for demos)
1. Create a new Space on [Hugging Face](https://huggingface.co/spaces)
2. Upload the following files:
   - `gradio_demo.py`
   - `requirements-gradio.txt` (rename to `requirements.txt`)
   - `src/` directory (entire codebase)
   - `config/` directory
   - `data/` directory
3. Add your API keys in the Space settings (Environment Variables)
4. The space will auto-deploy with HTTPS and sharing capabilities

#### Option 2: Railway/Render
```bash
# Create railway.toml or render.yaml
# Add environment variables via platform dashboards
# Deploy using platform-specific commands
```

#### Option 3: Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements-gradio.txt

EXPOSE 7860
CMD ["python", "gradio_demo.py"]
```

## 🎯 Usage Examples

### Basic Customer Inquiry
```
User: "Hello, I need help with my account"
→ System processes through: Context → Frustration → Chatbot → Quality
→ Returns helpful response with analysis
```

### High Frustration Scenario
```
User: "This is ridiculous! I've been trying to fix this for hours!"
→ System detects critical frustration
→ Immediately escalates to human agent (skips chatbot/quality)
→ Shows assigned agent profile and escalation context
```

### Quality Improvement
```
User: "I need help with a complex billing issue"
→ Chatbot generates initial response
→ Quality agent detects improvement needed
→ Returns enhanced response or escalates if necessary
```

## 🔧 Technical Architecture

### Processing Flow (Optimized)
1. **Context Gathering**: Collect relevant conversation history and data
2. **Frustration Analysis**: Analyze customer sentiment and frustration level
3. **Early Escalation Check**: If critical/high frustration → direct human routing
4. **Chatbot Response**: Generate AI response (only if no early escalation)
5. **Quality Analysis**: Review and potentially improve response
6. **Final Escalation Check**: Additional escalation triggers based on quality

### Performance Optimizations
- **Fast Mode Default**: Uses Claude Haiku for chatbot responses
- **Async Processing**: Proper async handling for database operations
- **Smart Caching**: Context caching for repeated queries
- **Resource Management**: Efficient memory and connection handling

### Configuration
- **Agent-Centric Config**: Each agent has its own configuration namespace
- **Model Selection**: Easy switching between different LLM models
- **Environment Overrides**: Dev/test/prod configuration separation

## 📊 Monitoring & Analytics

### Built-in Logging
- Real-time system logs with timestamps
- Agent processing steps and decisions
- LLM call tracking and performance metrics
- Error handling and recovery tracking

### LangSmith Integration (Optional)
```env
LANGCHAIN_API_KEY=your_key
LANGCHAIN_TRACING_V2=true
```

## 🔒 Security & Best Practices

### API Key Management
- Use environment variables for all API keys
- Never commit secrets to version control
- Use platform-specific secret management for deployment

### Resource Limits
- Connection pooling for database operations
- Request queuing to prevent overload
- Timeout handling for LLM calls

## 🎨 Customization

### UI Styling
Modify the CSS in `create_interface()` function:
```python
css = """
.analysis-panel {
    height: 300px;
    background-color: #f8f9fa;
    /* Add your custom styles */
}
"""
```

### Adding New Agents
1. Create new agent class in `src/nodes/`
2. Add configuration in `config/agents/`
3. Initialize in `initialize_system()`
4. Add to processing workflow in `process_user_input()`

## 🐛 Troubleshooting

### Common Issues
1. **System initialization failed**: Check API keys and configuration files
2. **No human agents found**: Verify database setup and agent data
3. **LLM call timeouts**: Check network connectivity and API limits
4. **Interface not loading**: Ensure all dependencies are installed

### Debug Mode
```python
# Enable debug logging
logging_config["level"] = "DEBUG"
```

## 🆚 Streamlit vs Gradio Comparison

| Feature | Streamlit | Gradio |
|---------|-----------|--------|
| Performance | Good | Better (async support) |
| Deployment | Custom | HuggingFace Spaces, easier |
| Mobile Support | Limited | Better responsive design |
| API Generation | Manual | Automatic REST API |
| Real-time Updates | Session-based | Event-driven |
| Styling | Custom CSS | Theme-based + CSS |
| Learning Curve | Medium | Lower |

## 📈 Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Multi-language support for international customers
- [ ] Advanced analytics dashboard
- [ ] Voice input/output capabilities
- [ ] Integration with external CRM systems
- [ ] A/B testing framework for response optimization

## 📝 License

This project is part of the HITL AI System. See the main project documentation for licensing details.