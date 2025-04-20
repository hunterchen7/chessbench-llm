from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "Qwen/Qwen2.5-0.5B-instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",           # Automatically selects GPU if available
)

# Example inference
prompt = """
SYSTEM:
You are a world-class chess grandmaster. Given a position, select the best move from the list of legal moves.

Piece positions:
White:
  K e1, Q d1, R a1 h1, B c1 f1, N b1 g1, P a2 b2 c2 d2 e2 f3 g2 h2

Black:
  K e8, Q d8, R a8 h8, B c8 f8, N b8 g8, P a7 b7 c5 d7 e7 f7 g7 h7

Choosing a move not in the legal move list will result in a forfeit.

Side to move: White

Legal moves:
["g2g3", "g2g4", "f3g1", "f3h4", "f3g5", "f3e5", "f3d4", "f3h2", "e2e3", "e2e4", "d2d3", "d2d4", "c2c3", "c2c4", "b2b3", "b2b4", "a2a3", "a2a4", "h2h3", "h2h4", "g1h3", "g1f3", "b1a3", "b1c3"]

Select exactly one legal move from the list above.

"""
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
input_ids = inputs["input_ids"]
output_ids = model.generate(**inputs, max_new_tokens=256)[0]

# Slice only the new tokens (model's response)
response_ids = output_ids[input_ids.shape[1]:]
response = tokenizer.decode(response_ids, skip_special_tokens=True)

print(response.strip())
