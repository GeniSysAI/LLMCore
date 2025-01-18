# Ensure pip is upgraded
Write-Output "Upgrading pip..."
python.exe -m pip install --upgrade pip

# Install required packages
Write-Output "Installing required packages..."
pip install openvino-genai
pip install --extra-index-url https://download.pytorch.org/whl/cpu `
    "git+https://github.com/huggingface/optimum-intel.git" `
    "git+https://github.com/openvinotoolkit/nncf.git" `
    "onnx<=1.16.1"

# Export the Meta Llama 3.2 3B Instruct model
Write-Output "Exporting the Meta Llama 3.2 3B Instruct model..."
optimum-cli export openvino --model meta-llama/Llama-3.2-3B-Instruct `
    --task text-generation-with-past `
    --weight-format int4 `
    --group-size 64 `
    --ratio 1.0 `
    llama-3.2-3b-instruct-INT4

Write-Output "Installation and export complete."


