#!/bin/bash
# HRET Installation Script for BenchhubPlus

set -e

echo "🚀 Installing HRET (Haerae Evaluation Toolkit) for BenchhubPlus..."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HRET_PATH="$PROJECT_ROOT/../haerae-evaluation-toolkit"

# Check if HRET directory exists
if [ ! -d "$HRET_PATH" ]; then
    echo "❌ HRET directory not found at: $HRET_PATH"
    echo "Please ensure haerae-evaluation-toolkit is cloned in the parent directory"
    exit 1
fi

echo "📁 Found HRET at: $HRET_PATH"

# Install HRET in development mode
echo "📦 Installing HRET in development mode..."
cd "$HRET_PATH"

# Install HRET requirements first
if [ -f "requirements.txt" ]; then
    echo "📋 Installing HRET requirements..."
    pip install -r requirements.txt
fi

# Install HRET in editable mode
echo "🔧 Installing HRET in editable mode..."
pip install -e .

# Verify installation
echo "✅ Verifying HRET installation..."
python -c "
try:
    import llm_eval
    from llm_eval.evaluator import Evaluator
    from llm_eval.hret import evaluation_context
    print('✅ HRET successfully installed and importable')
except ImportError as e:
    print(f'❌ HRET import failed: {e}')
    exit(1)
"

echo "🎉 HRET installation completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Update your BenchhubPlus code to use HRET"
echo "2. Test the integration with: python -m pytest tests/"
echo "3. Run BenchhubPlus with HRET support"