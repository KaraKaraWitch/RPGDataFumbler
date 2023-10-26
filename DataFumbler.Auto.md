# DataFumbler.Auto.py

## OobaBooga

Think of it as like a "Weaker" or on par version of OpenAI's ChatGPT / GPT 3.5.

### Benefits:

- You **Own** the model. so you can switch to another model if you don't like it.
- "Uncensored". Since you own the model, you can select which model you like the best.

### Downsides

- You need a recentish GPU. (8GB VRAM GPU can fit a 7B model quantized)
- The setup and getting everything "Right" can get finiky.
- Patience

### Setup

1. Refer to the [installation](https://github.com/oobabooga/text-generation-webui#installation) instructions here for setup.
2. modify the provided .toml file that tells how you want to translate the file. Comments are included to help guide you.
3. Run the command.

### Model Recommendations

This list is inconclusive. Do consider your options and do recommend some on the issues/discussion threads.

Most models are found on [HuggingFace](https://huggingface.co). Here are some recommendations

- [`airoboros-mistral2.2-7b.Q4_K_M.gguf`](https://huggingface.co/TheBloke/airoboros-mistral2.2-7B-GGUF/blob/main/airoboros-mistral2.2-7b.Q4_K_M.gguf) [This model fits on a 8GB with a context size similar to OpenAI. Yields reasonable results]
- 

## OpenAI

Ah yes, OpenAI. The model that everyone is so enamured about.

This library does provide OpenAI as a way to translate games. But the author does not use it so is unable to test what feels the best.

The code is self written but the processing is taken from