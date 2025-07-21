# AI Agent Testing Suite

This directory contains a comprehensive testing suite for the Human-in-the-Loop (HITL) AI System agents. The suite provides user-friendly Jupyter notebooks for testing chatbot responses, quality assessment, and frustration detection.

## 🚀 Quick Start

1. **Generate Test Questions**: Start with `question_generator.ipynb`
2. **Test Chatbot Responses**: Run `chatbot_tester.ipynb` 
3. **Analyze Quality**: Process results through `quality_agent_tester.ipynb`
4. **Detect Frustration**: Analyze customer sentiment with `frustration_agent_tester.ipynb`

## 📋 Workflow Overview

```
┌─────────────────────┐
│ question_generator  │ ──→ generates test questions
│     .ipynb          │     for different scenarios
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  chatbot_tester     │ ──→ processes questions through
│     .ipynb          │     chatbot agent
└─────────────────────┘
           │
           ▼ conversation_results.json
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────────┐ ┌─────────────────────┐
│quality_agent│ │ frustration_agent   │
│ _tester     │ │    _tester          │
│  .ipynb     │ │     .ipynb          │ 
└─────────────┘ └─────────────────────┘
    │               │
    ▼               ▼
quality_results   frustration_results
   .json             .json

                ALTERNATIVE WORKFLOW:

┌─────────────────────┐
│  live_chat_tester   │ ──→ real-time human interaction
│     .ipynb          │     with instant AI scoring
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│   Interactive UI    │ ──→ chat + live quality/frustration
│   with Real-time    │     assessments displayed
│   AI Assessment     │     beneath each turn
└─────────────────────┘
           │
           ▼
    live_chat_results
        .json
```

## 📓 Notebook Descriptions

### 1. 📝 question_generator.ipynb
**Purpose**: Generate diverse test questions for agent testing

**Features**:
- AI-powered question generation using configurable LLM
- Multiple customer personas (frustrated, polite, technical, non-technical)
- Complexity levels (simple, medium, complex)
- Industry-specific scenarios
- Export questions in JSON format for other testers

**Outputs**:
- `questions_[timestamp].json` - Generated test questions
- `question_generation_config_[timestamp].json` - Configuration used

---

### 2. 🤖 chatbot_tester.ipynb  
**Purpose**: Test chatbot agent responses with realistic customer interactions

**Features**:
- Load and edit chatbot agent configuration (prompts, models, behavior)
- Process test questions through the chatbot agent
- Simulate multi-turn conversations with AI customer simulation
- Analyze conversation outcomes and customer satisfaction
- Export detailed conversation results

**Inputs**:
- Test questions (from question_generator.ipynb or custom JSON)
- Configurable chatbot settings

**Outputs**:
- `chatbot_results_[timestamp].json` - Complete conversation data
- `chatbot_config_[timestamp].json` - Configuration used
- `chatbot_summary_[timestamp].csv` - Analysis-ready summary

---

### 3. ⭐ quality_agent_tester.ipynb
**Purpose**: Evaluate the quality of chatbot responses and suggest improvements

**Features**:
- Load and edit quality assessment configuration
- Process chatbot conversations to generate quality scores (1-10)
- Categorize responses (adequate/needs_adjustment/human_intervention)
- Generate improved versions of low-quality responses
- Analyze quality patterns by customer type and complexity

**Inputs**:
- Conversation results (from chatbot_tester.ipynb)
- Configurable quality thresholds and assessment criteria

**Outputs**:
- `quality_assessment_results_[timestamp].json` - Detailed quality analysis
- `quality_agent_config_[timestamp].json` - Configuration used  
- `quality_summary_[timestamp].csv` - Quality metrics summary
- `quality_report_[timestamp].txt` - Executive summary

---

### 4. 😤 frustration_agent_tester.ipynb
**Purpose**: Detect customer frustration levels and recommend human intervention

**Features**:
- Load and edit frustration detection configuration
- Analyze customer queries for frustration indicators
- Track escalation patterns across conversation history
- Generate intervention recommendations
- Assess employee wellbeing impact

**Inputs**:
- Conversation results (from chatbot_tester.ipynb)
- Configurable frustration thresholds and detection rules

**Outputs**:
- `frustration_analysis_results_[timestamp].json` - Complete frustration analysis
- `frustration_agent_config_[timestamp].json` - Configuration used
- `frustration_summary_[timestamp].csv` - Analysis summary
- `frustration_report_[timestamp].txt` - Management report with employee wellbeing recommendations

---

### 5. 💬 live_chat_tester.ipynb
**Purpose**: Interactive live chat testing with real-time AI agent scoring

**Features**:
- Interactive chat window for real human-chatbot conversations
- Real-time quality scoring after each chatbot response
- Real-time frustration detection after each user message
- Live display of agent assessments and scores beneath each interaction
- Conversation trends and analysis dashboard
- Export complete conversation with all scoring data

**Use Cases**:
- **Stakeholder Demos**: Show live AI quality control and frustration detection
- **System Validation**: Test with real human interactions vs. simulated customers
- **Configuration Tuning**: See immediate impact of agent settings changes
- **Training Data**: Generate high-quality human-validated conversation examples

**Outputs**:
- `live_chat_results_[timestamp].json` - Complete conversation with real-time assessments
- `live_chat_summary_[timestamp].csv` - Turn-by-turn analysis data
- `live_chat_report_[timestamp].txt` - Session insights and recommendations

## 🔧 Configuration Management

Each tester notebook includes:

### **Agent-Specific Configuration**
- **Agent Settings** (`config.yaml`): Behavior parameters, thresholds, escalation rules
- **Prompts** (`prompts.yaml`): System prompts, assessment criteria, response templates
- **Models** (`models.yaml`): AI model preferences for different tasks

### **Configuration Features**
- **Live Editing**: Modify YAML configurations directly in notebooks
- **Comment Preservation**: Original formatting and comments maintained
- **Validation**: YAML syntax and model alias validation
- **Temporary Files**: Changes saved to temp files, originals untouched
- **Export**: Save configurations used for reproducible testing

## 📊 Data Flow and Analysis

### Input Data Formats
```json
// Test Questions (question_generator → chatbot_tester)
[
  {
    "id": 1,
    "question": "How do I reset my password?",
    "customer_type": "technical",
    "complexity": "simple"
  }
]

// Conversation Results (chatbot_tester → quality/frustration testers)
[
  {
    "id": 1,
    "customer_type": "technical", 
    "complexity": "simple",
    "conversation_history": [
      {
        "turn_number": 1,
        "customer_query": "How do I reset my password?",
        "chatbot_response": "I can help you reset your password...",
        "customer_satisfaction": 0.85
      }
    ],
    "final_outcome": "satisfied"
  }
]
```

### Enhanced Output Data
Quality and frustration testers add rich analytical data:
- Quality scores, confidence levels, improvement suggestions
- Frustration levels, escalation trends, intervention recommendations
- Pattern analysis across customer types and complexity levels

## 📈 Analysis Capabilities

### Quality Analysis
- **Quality Scoring**: 1-10 scale with detailed reasoning
- **Decision Categories**: Adequate, needs adjustment, human intervention
- **Pattern Recognition**: Quality trends by customer segment
- **Response Improvement**: AI-generated better responses

### Frustration Analysis  
- **Frustration Levels**: Low, moderate, high, critical
- **Pattern Tracking**: Escalation trends over conversation history
- **Intervention Logic**: When to route to human agents
- **Employee Protection**: Workload balancing recommendations

### Cross-Analysis
- **Customer Segmentation**: Performance by customer type and complexity
- **Model Comparison**: Test different AI models and configurations
- **Threshold Optimization**: Fine-tune quality and frustration thresholds
- **Workflow Optimization**: Identify bottlenecks and improvement opportunities

## 🛠️ Usage Instructions

### Prerequisites
- Python environment with required packages (see `pyproject.toml`)
- Jupyter Lab/Notebook server
- API keys for LLM providers (OpenAI, Anthropic, etc.)
- System running from `/workspace` directory

### Environment Setup
```bash
# Install dependencies
uv sync --dev

# Set API keys
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Start Jupyter
jupyter lab notebooks/agent_testers/
```

### Testing Workflow

1. **Start Fresh Testing Cycle**:
   ```
   question_generator.ipynb → Generate test scenarios
   ```

2. **Test Chatbot Performance**:
   ```
   chatbot_tester.ipynb → Upload questions → Run conversations → Export results
   ```

3. **Analyze Quality** (parallel with step 4):
   ```
   quality_agent_tester.ipynb → Upload chatbot results → Analyze quality → Export analysis
   ```

4. **Analyze Frustration** (parallel with step 3):
   ```
   frustration_agent_tester.ipynb → Upload chatbot results → Detect frustration → Export analysis
   ```

### Configuration Testing
- **A/B Testing**: Run same questions through different configurations
- **Threshold Tuning**: Adjust quality/frustration thresholds and measure impact
- **Model Comparison**: Test different LLM models for each agent
- **Prompt Engineering**: Iterate on system prompts and response templates

## 📁 File Organization

```
notebooks/agent_testers/
├── README.md                      # This file
├── question_generator.ipynb       # Generate test questions
├── chatbot_tester.ipynb          # Test chatbot responses
├── quality_agent_tester.ipynb    # Analyze response quality
├── frustration_agent_tester.ipynb # Detect customer frustration
├── live_chat_tester.ipynb        # Interactive live chat with real-time scoring
│
├── question_exports/              # Generated questions
│   ├── questions_20240115_143022.json
│   └── question_generation_config_20240115_143022.json
│
├── chatbot_results/              # Chatbot test results
│   ├── chatbot_results_20240115_150000.json
│   ├── chatbot_config_20240115_150000.json
│   └── chatbot_summary_20240115_150000.csv
│
├── quality_assessment_exports/   # Quality analysis results
│   ├── quality_assessment_results_20240115_152000.json
│   ├── quality_agent_config_20240115_152000.json
│   ├── quality_summary_20240115_152000.csv
│   └── quality_report_20240115_152000.txt
│
├── frustration_analysis_exports/ # Frustration analysis results
│   ├── frustration_analysis_results_20240115_153000.json
│   ├── frustration_agent_config_20240115_153000.json
│   ├── frustration_summary_20240115_153000.csv
│   └── frustration_report_20240115_153000.txt
│
└── live_chat_exports/            # Live chat session results
    ├── live_chat_results_20240115_154000.json
    ├── live_chat_summary_20240115_154000.csv
    └── live_chat_report_20240115_154000.txt
```

## 🎯 Testing Scenarios

### Basic Quality Assurance
1. Generate standard customer service questions
2. Test with default chatbot configuration
3. Analyze quality scores and identify low-performing areas
4. Adjust configuration and retest

### Frustration Detection Validation
1. Generate questions with varying frustration levels
2. Test frustration detection accuracy
3. Validate intervention thresholds
4. Assess employee protection recommendations

### Configuration Optimization
1. Test multiple prompt variations
2. Compare different AI models
3. Optimize quality/frustration thresholds
4. Measure impact on customer satisfaction

### Live Chat Validation
1. Test with real human interactions using `live_chat_tester.ipynb`
2. Validate AI scoring accuracy against human judgment
3. Demo system capabilities to stakeholders
4. Generate high-quality training conversations

### Stress Testing
1. Generate high-volume question sets
2. Test edge cases and complex scenarios
3. Validate error handling and fallback behaviors
4. Assess system performance under load

## 🚨 Troubleshooting

### Common Issues
- **Import Errors**: Ensure running from `/workspace` directory
- **API Key Issues**: Set environment variables before starting Jupyter
- **Configuration Errors**: Use YAML validation in notebooks
- **Memory Issues**: Process smaller question batches for large datasets

### Debug Tips
- Check notebook cell outputs for detailed error messages
- Validate JSON file formats before uploading
- Use temporary configuration files for safe experimentation
- Export results frequently to avoid data loss

## 📚 Additional Resources

### Configuration Examples
- See `config/agents/*/` for default agent configurations
- Review `config/shared/models.yaml` for available AI models
- Check `config/environments/` for environment-specific settings

### Integration with Main System
- Results can be used to optimize production HITL workflow
- Configuration insights inform agent deployment parameters
- Quality and frustration patterns guide human agent training

### Documentation
- Agent implementation details in `src/nodes/`
- Configuration system documentation in `config/README.md`
- Core system architecture in main `README.md`

---

## 🔄 Continuous Improvement

This testing suite supports continuous improvement of the HITL AI system:

1. **Regular Testing Cycles**: Run weekly quality assessments
2. **Performance Monitoring**: Track quality and frustration trends over time
3. **Configuration Evolution**: Iterate on prompts and thresholds based on results
4. **Data-Driven Optimization**: Use exported analytics for system tuning

The testing suite provides comprehensive insights into agent performance, enabling data-driven optimization of the human-in-the-loop AI system for maximum customer satisfaction and employee wellbeing.