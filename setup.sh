#!/bin/bash

echo "🚀 AutoTrade AI Bot Setup Script Initiated..."

# 1. System Update & Install Python Tools
echo "🔧 Updating system and installing Python environment..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv build-essential

# 2. Create Python Virtual Environment
echo "🐍 Creating and activating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install pandas

# 3. Install Required Python Packages (excluding MetaTrader5 for Codex/Linux)
echo "📦 Installing required Python libraries (MetaTrader5 skipped)..."
if [ ! -f requirements.txt ]; then
  echo "❌ Error: requirements.txt not found!"
  exit 1
fi

grep -v 'MetaTrader5' requirements.txt > temp_requirements.txt
pip install --upgrade pip setuptools wheel
pip install -r temp_requirements.txt
rm temp_requirements.txt

# 4. Create Default Config File (if not present)
echo "🔐 Checking for config/config.json..."
mkdir -p config
if [ ! -f config/config.json ]; then
  echo "🛡️ Creating default config/config.json..."
  cat <<EOF > config/config.json
{
  "api_key": "REPLACE_ME",
  "api_secret": "REPLACE_ME"
}
EOF
else
  echo "✅ Found existing config/config.json"
fi

# 5. Final Notices for Developer
echo ""
echo "⚠️ NOTICE: MetaTrader5 package is excluded due to Linux/Codex environment."
echo "💡 You can still develop, test, and backtest all non-MT5 logic."
echo "💻 For live MT5 trading, run this bot on a Windows machine with MetaTrader5 installed and configured."
echo ""
echo "✅ Setup complete!"
echo "👉 To activate your virtual environment:"
echo "   source venv/bin/activate"
echo "👉 To run backtests or simulate live strategy:"
echo "   python main.py"
