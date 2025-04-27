import { sendPrompt, createPrompt } from './chess-utils.js';

const FEN = 'r1bqkb1r/pppp1ppp/2n2n2/4p1N1/2B1P3/8/PPPP1PPP/RNBQK2R b KQkq - 5 4';

const prompt = createPrompt(FEN);

sendPrompt(prompt, 'meta-llama/llama-4-scout:free')
	.then((response) => {
		console.log('Response:', response);
	})
	.catch((error) => {
		console.error('Error:', error);
	});
