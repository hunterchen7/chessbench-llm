from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Literal, Optional
import torch

app = FastAPI()

# You can override this via env
MODEL_ID = "microsoft/phi-2"

print(f"Loading model: {MODEL_ID}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
)
model.eval()

# OpenAI-compatible request schema
class Message(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stop: Optional[List[str]] = None

@app.post("/api/v1/chat/completions")
async def chat(request: ChatRequest):
    prompt = ""
    for msg in request.messages:
        prompt += f"{msg.role.capitalize()}: {msg.content.strip()}\n"
    prompt += "Assistant:"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=request.max_tokens or 512,
        temperature=request.temperature or 0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )

    reply = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    return {
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
    }
