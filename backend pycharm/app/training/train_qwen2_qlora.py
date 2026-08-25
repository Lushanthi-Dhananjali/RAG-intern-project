import torch
from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Configuration & Hyperparameters
MAX_SEQ_LENGTH = 2048
MODEL_NAME = "unsloth/Qwen2-7B-Instruct-bnb-4bit"  # Pre-quantized 4-bit base model
DATASET_PATH = "./data/raft_training_dataset.jsonl"
OUTPUT_DIR = "./qwen2_7b_civic_lora"

print("🚀 Loading Qwen2-7B-Instruct with 4-bit quantization via Unsloth...")

# 2. Load Model & Tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,  # Auto-detects float16 or bfloat16 based on GPU
    load_in_4bit=True,  # Enforces 4-bit QLoRA
)

# 3. Attach LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # LoRA Rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,  # Optimized at 0 for Unsloth
    bias="none",
    use_gradient_checkpointing="unsloth",  # Saves substantial VRAM
    random_state=3407,
)


# 4. Format Dataset for Fine-Tuning
def format_prompts(examples):
    instructions = examples["instruction"]
    inputs = examples["input"]
    outputs = examples["output"]
    texts = []

    for inst, inp, out in zip(instructions, inputs, outputs):
        # Format matching Qwen2 Chat ML Template
        formatted_text = f"<|im_start|>system\n{inst}<|im_end|>\n<|im_start|>user\n{inp}<|im_end|>\n<|im_start|>assistant\n{out}<|im_end|>"
        texts.append(formatted_text)

    return {"text": texts}


print(f"📊 Loading dataset from: '{DATASET_PATH}'...")
dataset = load_dataset("json", data_files={"train": DATASET_PATH})
dataset = dataset.map(format_prompts, batched=True)

# 5. Initialize SFTTrainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    packing=False,  # Set to True for short sequences to speed up training
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,  # Adjust based on dataset size (e.g., 100-300 steps)
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir=OUTPUT_DIR,
    ),
)

# 6. Execute Fine-Tuning
print("🔥 Starting QLoRA Training...")
trainer_stats = trainer.train()

# 7. Save LoRA Adapters & GGUF for Ollama Deployment
print(f"💾 Saving trained LoRA adapter to '{OUTPUT_DIR}'...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# Optional: Export to GGUF format to run locally via Ollama
# model.save_pretrained_gguf("./qwen2_civic_model", tokenizer, quantization_method="q4_k_m")

print("✅ Fine-Tuning Complete!")