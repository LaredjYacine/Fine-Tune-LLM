# Fine-Tune-LLM
This repository is me learning how to Fine Tune LLMs 
# Qwen2.5-1.5B PEFT LoRA Fine-Tuner

This project sets up and executes a Parameter-Efficient Fine-Tuning (PEFT) pipeline using **LoRA** (Low-Rank Adaptation) on the **Qwen/Qwen2.5-1.5B-Instruct** causal language model. It utilizes a subset of the Databricks Dolly 15k dataset formatted for instruction tuning via Hugging Face's `transformers`, `peft`, `datasets`, and `trl` libraries.

---

## Installation

You can install all required dependencies instantly using **uv**:

```bash
uv pip install transformers peft huggingface_hub torch torchao datasets trl
```
<p align="center">
  <img width="500" alt="Screenshot_1" src="https://github.com/user-attachments/assets/eb2d2ada-b468-4636-9da0-c0030a8b8054" />
</p>
