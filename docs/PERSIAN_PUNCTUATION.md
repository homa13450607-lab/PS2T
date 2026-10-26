# Persian punctuation restoration (offline)

PS2T can add Persian punctuation to the full transcript using a local token-classification model. The model is optional; if it is missing or cannot be loaded, transcription continues and the full transcript remains in its current form.

## Model

Model card: https://huggingface.co/MohammadJRanjbar/parsbert-persian-punctuation

The model repository currently requires a Hugging Face login and acceptance of its access conditions (including sharing contact information). Review those terms yourself before proceeding. The model weights are about 649 MB.

## Setup on Windows

1. Open the model card above, sign in to Hugging Face, and accept the repository's access conditions if you agree.
2. Download the model files into this local folder in the PS2T project:

   models/persian-punctuation/

   At minimum, the folder must contain config.json, tokenizer_config.json, tokenizer.json, and model.safetensors. Keep any other model/tokenizer files provided by the repository too.
3. Install the Python dependency in the project's existing virtual environment:

   venv\Scripts\python.exe -m pip install "transformers>=4.40.0,<5.0.0"

   This command needs package access. For a fully offline computer, download compatible wheels on a connected computer and transfer/install them locally.
4. In config/settings.yaml, ensure the following settings are present:

   punctuation:
     enabled: true
     model_path: "models/persian-punctuation"

5. Stop PS2T with Ctrl+C and restart it:

   venv\Scripts\python.exe main.py

The model is loaded locally and is not downloaded at runtime. It runs on CPU by default to avoid competing with faster-whisper for GPU memory. It inserts punctuation into the full transcript; the timestamped segment table and SRT retain the original segment text/timing for traceability.

## Validation

First test a short audio sample and compare the full transcript against the audio. The model restores punctuation only; it does not correct missed or misrecognized words. If the model is unavailable, check the application log for a warning and verify the local model folder contents.
