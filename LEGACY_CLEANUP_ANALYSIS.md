# Legacy and Outdated Items Analysis

Based on a comprehensive review of the project, here's a detailed list of legacy compatibility items and outdated components that could be cleaned up:

## **1. Duplicate Directory Structure (Major) - UPDATED**
- **`/workspace/VIA_tech_demo/`** - Complete duplicate of main codebase
  - **CLARIFICATION**: This is actually a streamlined copy for Hugging Face Spaces deployment
  - Contains identical `src/`, `config/`, `data/`, `scripts/` structure
  - **Impact**: ~50% of codebase duplication
  - **Status**: Requires special handling - see HF Spaces recommendations below

## **2. Legacy Configuration Files**
- **`config/config.json`** - Old JSON format configuration (mentioned in CLAUDE.md as "legacy format for compatibility")
- **`VIA_tech_demo/config/config.json`** - Duplicate of legacy config
- **`pyproject.toml.streamlit`** - Streamlit-specific project file (outdated)
- **`requirements-gradio.txt`** - Separate requirements file for Gradio (redundant with pyproject.toml)
- **`VIA_tech_demo/requirements.txt`** - Legacy requirements format

## **3. Database Files (Testing/Development Artifacts)**
- **Multiple test databases**: `test.db`, `test_alias.db`, `test_fixed.db`, `interactive_test.db`, `test_automation.db`, `demo_system.db`
- **Backup files**: `hybrid_system.db.backup` and entire `/data/backups/migration_backups/` directory
- **Development databases**: `/data/dev/`, `/data/test/`, `/data/prod/` (empty directories)

## **4. Legacy Code Patterns in Source**
- **`src/services/simple_scoring_engine.py`** - "Simplified" version suggesting there's a full version
- **Legacy routing methods** in `src/nodes/human_routing_agent.py`:
  - `_legacy_routing()` method
  - `_convert_to_legacy_format()` method
  - Legacy field mapping support
- **Legacy method markers** in `src/nodes/chatbot_agent.py`:
  - Methods marked as "(legacy method)"

## **5. Cache and Compiled Files**
- **4,111 `.pyc` files** across multiple `__pycache__` directories
- **Build artifacts** that should be in `.gitignore`

## **6. Documentation Redundancy**
- **Multiple README files**: Main README.md, docs/README.md, VIA_tech_demo/README.md
- **Setup guides**: SETUP.md, README-gradio.md, VIA_tech_demo/README_DATABASE_SETUP.md
- **Git help file**: `git_help.md` (appears to be personal notes)

## **7. Model Files (Potentially Unused)**
- **`/models/` directory** with large model files:
  - `codellama-7b.gguf`, `llama-13b.gguf`, `llama-7b.gguf`, `mistral-7b.gguf`
  - These may be for local LLM testing but appear unused in current codebase

## **8. Docker Configuration Duplication**
- **Multiple Docker setups**: `Dockerfile`, `Dockerfile.gpu`, `docker-compose.gpu.yml`
- Suggests evolution from CPU-only to GPU support

## **9. Notebook Outputs and Logs**
- **`/notebooks/agent_testers/outputs/`** - Contains timestamped test outputs from July 2025
- **Multiple log files**: `/logs/app.log`, `/logs/debug.log`, `/notebooks/logs/`

## **10. Script Collection (Mixed Utility)**
- **Demo/test scripts**: `demo.py`, `answer_agent_demo.py`, `experimentation_demo.py`
- **Setup scripts**: `setup.py`, `setup_local_llm.py`, `gpu_detect.py`
- Some may be valuable, others appear to be one-off experiments

## **Cleanup Recommendations by Priority:**

### **High Priority (Safe to Remove)**
1. ~~Delete entire `/VIA_tech_demo/` directory (50% size reduction)~~ **UPDATED**: See HF Spaces recommendations below
2. Remove all `__pycache__/` directories and `.pyc` files
3. Clean up test databases and backup files
4. Remove `pyproject.toml.streamlit` and `requirements-gradio.txt`

### **Medium Priority (Review Before Removal)**
1. Legacy routing methods in human_routing_agent.py
2. `config/config.json` legacy format files
3. Unused model files in `/models/` directory
4. Old documentation files and git_help.md

### **Low Priority (Keep for Now)**
1. Demo scripts (may be useful for development)
2. Docker configurations (different deployment options)
3. Notebook outputs (may contain valuable test data)

## **Hugging Face Spaces Deployment Recommendations**

Since `VIA_tech_demo` is a streamlined copy for Hugging Face Spaces deployment, here are the best approaches for handling it in a devcontainer environment:

### **Option 1: Git Subtree (Recommended)**
Convert `VIA_tech_demo` to a git subtree to maintain it as a streamlined copy while keeping it in sync:

```bash
# Remove current VIA_tech_demo directory
rm -rf VIA_tech_demo

# Add as subtree (assuming you have a separate HF Spaces repo)
git subtree add --prefix=VIA_tech_demo https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE main --squash

# To push updates later:
git subtree push --prefix=VIA_tech_demo origin main
```

**Benefits:**
- Maintains separation for HF Spaces
- Easy to push updates with single command
- No duplication in main repo history

### **Option 2: Build Script + Deployment Directory**
Create a build process that generates the HF Spaces version:

```bash
# Remove VIA_tech_demo
rm -rf VIA_tech_demo

# Create build script for HF Spaces deployment
mkdir -p deploy/huggingface
# Add build.sh script that copies only necessary files with streamlined structure
```

### **Option 3: Git Worktree (If Same Repo)**
If HF Spaces is a branch of the same repo:

```bash
# Remove directory
rm -rf VIA_tech_demo

# Add as worktree
git worktree add VIA_tech_demo huggingface-spaces
```

### **Option 4: Separate Repository Entirely**
Move HF Spaces to its own repo and sync via CI/CD:

```bash
# In devcontainer, clone HF Spaces repo separately
cd /workspace
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE hf-spaces
```

### **Recommended Implementation**
For devcontainer usage, **Option 2** with a build script is most practical:

1. Remove `VIA_tech_demo` from main repo
2. Create `deploy/huggingface/` directory with:
   - `build.sh` - Copies necessary files
   - `app.py` - HF Spaces entry point
   - `requirements.txt` - Minimal dependencies
3. Add to `.gitignore`: `VIA_tech_demo/` (if keeping locally)
4. Use build script to generate deployment package when needed

## **Summary**
**Total estimated cleanup impact**: ~30-40% reduction in repository size (adjusted for HF Spaces consideration), with most gains from removing cache files and test databases.

**Files analyzed**: Over 4,000 files across the entire project structure
**Key findings**: Significant duplication and legacy compatibility code, with VIA_tech_demo requiring special deployment consideration
**Recommended approach**: Start with high-priority cache/database cleanup, implement HF Spaces build system, then review medium-priority items case by case