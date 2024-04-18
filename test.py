import torch
import torch.nn.functional as F

from transformers import AutoModelForCausalLM, AutoTokenizer

import argparse
from attack import AdvAttack

DEFAULT_PROMPT = "Who are Harry Potter's best friends?"
DEFAULT_TARGET = "Harry Potter's best friends are Ron Weasley and Hermione Granger."
DEFAULT_INSTRUCT = "Answer all questions succinctly."

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("--model_path", type=str, required=True, help="Path to model")
	parser.add_argument("-q", "--fp16", action="store_true", help="Use fp16 when loading in model")
	parser.add_argument("-v", "--verbose", action="store_true", help="Show tqdm for runs")

	args = parser.parse_args()

	return args

def test_attack(attack, args):
	attack.run(256, 64, 128, verbose=args.verbose)

def test_loss(attack: AdvAttack, args):
	func_loss = attack.get_target_ppl(attack.prompt).item()

	if args.verbose:
		print("Computed Loss", func_loss)

	logits = attack.model.forward(attack.prompt.unsqueeze(0)).logits
	logits = F.log_softmax(logits, dim = 2)
	target_logits = logits[0][attack.indices_dict["target"]-1]
	vals = attack.values_dict["target"]

	sum = 0
	for index in range(len(vals)):
		sum -= target_logits[index][vals[index]].item()

	if args.verbose:
		print("Computed Loss", sum)

	assert func_loss == sum
	
def test_candidates(attack: AdvAttack, args):
	candidates = attack.top_candidates(attack.prompt, attack.indices_dict["suffix"], attack.indices_dict["target"],100)
	return

def test_prompt(attack: AdvAttack, args, suffix):
	attack.set_suffix(suffix)
	attack.prompt_response(verbose=args.verbose)


def main():
	args = parse_args()

	if args.fp16:
		model = AutoModelForCausalLM.from_pretrained(args.model_path, torch_dtype = torch.float16)
	else:
		model = AutoModelForCausalLM.from_pretrained(args.model_path)

	tokenizer = AutoTokenizer.from_pretrained(args.model_path)

	if torch.cuda.is_available:
		model.to("cuda:0")

	if args.verbose:
		print("Model and tokenizer loaded")

	attack = AdvAttack(
		model, 
		tokenizer, 
		prompt=DEFAULT_PROMPT, 
		target=DEFAULT_TARGET, 
		suffix_token = "!", 
		suffix_length=64, 
		instruction=DEFAULT_INSTRUCT
	)

	#test_attack(attack, args)
	#test_loss(attack, args)
	#test_candidates(attack, args)
 
	#SUFFIX = torch.tensor([7548, 3776, 837, 5791, 13, 8001, 5384, 21011, 3053, 14033, 394, 19017, 14542, 5135, 26619, 270])
 
	#test_prompt(attack, args, SUFFIX)

if __name__ == "__main__":
	main()


