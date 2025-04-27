import { Chess, SQUARES, Move, PieceSymbol } from 'chess.js';

type PositionSummary = {
	fen: string;
	white_pieces: string;
	black_pieces: string;
	legal_moves: string[];
};

function summarizePosition(fen: string, san: boolean = true): PositionSummary {
	const board = new Chess(fen);

	const whiteGroups: Record<PieceSymbol, string[]> = {
		p: [],
		n: [],
		b: [],
		r: [],
		q: [],
		k: [],
	};
	const blackGroups: Record<PieceSymbol, string[]> = {
		p: [],
		n: [],
		b: [],
		r: [],
		q: [],
		k: [],
	};

	const pieceMap = board.board();
	for (let rank = 0; rank < 8; rank++) {
		for (let file = 0; file < 8; file++) {
			const piece = pieceMap[rank][file];
			if (piece) {
				const square = SQUARES[rank * 8 + file];
				const squareName = square.toLowerCase(); // chess.js uses "a1" etc.

				if (piece.color === 'w') {
					whiteGroups[piece.type].push(squareName);
				} else {
					blackGroups[piece.type].push(squareName);
				}
			}
		}
	}

	function formatGroup(groups: Record<PieceSymbol, string[]>): string {
		const names: Record<PieceSymbol, string> = {
			k: 'king',
			q: 'queen',
			r: 'rook',
			b: 'bishop',
			n: 'knight',
			p: 'pawn',
		};
		return Object.entries(groups)
			.filter(([_, squares]) => squares.length > 0)
			.sort()
			.map(([ptype, squares]) => `- ${names[ptype as PieceSymbol]}: ${squares.sort().join(', ')}`)
			.join('\n ');
	}

	const legalMoves = san
		? board.moves({ verbose: false })
		: board.moves({ verbose: true }).map((move) => (move as Move).san || move.toString());

	return {
		fen,
		white_pieces: formatGroup(whiteGroups),
		black_pieces: formatGroup(blackGroups),
		legal_moves: legalMoves,
	};
}

export function createPrompt(fen: string, san: boolean = true): string {
	const positionSummary = summarizePosition(fen, san);
	const side = new Chess(fen).turn() === 'w' ? 'white' : 'black';

	return `
You are tasked with playing the ${side} pieces in the following chess position.

The pieces on the board are arranged as follows:
white pieces: ${positionSummary.white_pieces}
black pieces: ${positionSummary.black_pieces}

Your turn (${side} to move)

Legal moves: ${positionSummary.legal_moves.join(', ')}

Your Objective: Select the single best move from the provided list.
Analysis Process:
1. Identify Candidate Moves: Briefly scan the list for active moves: checks, moves threatening mate, moves placing pieces on key squares. Also note moves that place your piece where it can be immediately captured.
2. Mandatory Tactical Calculation (Highest Priority):
 - For every candidate move identified in Step 1, especially checks or moves placing a piece en prise (where it can be captured):
 - Calculate the opponent's primary responses. What are the forced replies? What happens if the opponent captures the piece you just moved?
 - Evaluate the position after the opponent's likely reply.
 - If your move places a piece en prise: Does the opponent capturing it lead to your checkmate shortly after? Does it lead to you winning more material than you lost? Does it gain a decisive, unavoidable advantage? If yes, this is a potential sacrifice.
 - If your move places a piece en prise and the opponent capturing it simply results in you losing material with no significant compensation, this is a blunder. Eliminate this move from consideration.
 - If your move is a check: Are all opponent responses safe for you? Does any response capture your checking piece? If yes, evaluate the consequences as described above (is it a sacrifice leading to mate, or a blunder?).
3. Eliminate Blunders: Discard any move confirmed as a blunder in Step 2 (uncompensated loss of material or leading to a worse position).
4. Compare Sound Candidates:
 - Evaluate the remaining moves (safe moves and sound sacrifices).
 - Prioritize forcing lines that lead to checkmate quickly (like a sound sacrifice leading to mate, or a check sequence leading to mate).
 - If no immediate mate is found, choose the move that provides the greatest advantage safely.
5. Final Selection:
 - Choose exactly one move from the legal moves list that survived the tactical calculation and comparison.
`;
}

export async function sendPrompt(
	prompt: string,
	model: string,
	key: string,
	serverUrl: string = 'https://openrouter.ai/api/v1/chat/completions',
): Promise<string | null> {
	try {
		const response = await fetch(serverUrl, {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${key}`,
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				model,
				messages: [{ role: 'user', content: prompt }],
			}),
		});

		const data = await response.json();

		console.log(`Response: ${JSON.stringify(data)}`);

		return data?.choices?.[0].message.content.trim();
	} catch (error: any) {
		console.error(`Error: ${error}`);
		console.error(`Request failed: ${error.response?.status}`);
		console.error(error.response?.data);
		return null;
	}
}

async function parseMove(fen: string, response: string): Promise<string | null> {
	const board = new Chess(fen);
	const legalMoves = board.moves({ verbose: true });

	for (const move of legalMoves) {
		const san = board.move(move).san;
		board.undo();
		if (response.includes(san)) {
			return san;
		}
	}
	return null;
}

async function extractMoveScout(responseText: string, key: string): Promise<string> {
	const prompt = `
You are an assistant that extracts the final chess move selected from a grandmaster-style explanation.

The move must be in SAN (Standard Algebraic Notation), such as: e4, d4, Nf3, Nc6, O-O, Qxe5, etc.

Only return the move that the player finally decided to play. Ignore other candidate moves that were discussed but rejected. If multiple moves are mentioned, return the one that is clearly stated as the final or best choice.

Respond with **only** the SAN move, and nothing else.

Text:
"""
${responseText}
"""

Final Move:`;

	const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${key}`,
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({
			model: 'meta-llama/llama-4-scout:free',
			messages: [{ role: 'user', content: prompt }],
		}),
	});

	if (response.ok) {
		const data = await response.json();
		const content = data?.choices?.[0]?.message?.content;
		if (typeof content === 'string') {
			return content.trim();
		} else {
			throw new Error(`Invalid response format: ${JSON.stringify(data)}`);
		}
	} else {
		const errorText = await response.text();
		throw new Error(`Extraction failed: ${response.status}\n${errorText}`);
	}
}

function extractSanHeuristically(response: string, fen: string): string | null {
	const board = new Chess(fen);
	const legalSans = board.moves();

	const candidateRegex = /\b([KNBRQ]?[a-h]?[1-8]?x?[a-h][1-8]|O-O(?:-O)?)\b/g;
	const candidates = Array.from(response.matchAll(candidateRegex)).map((m) => m[1]);

	for (const move of candidates) {
		if (legalSans.includes(move)) {
			const before = response.slice(0, response.indexOf(move)).toLowerCase();
			if (/(final answer|i choose|best move|i played|my move|i play|i will play|i select|my chosen)/.test(before.slice(-100))) {
				return move;
			}
		}
	}

	for (const move of candidates) {
		if (legalSans.includes(move)) {
			return move;
		}
	}

	return null;
}

export async function extractMove(response: string, fen: string, key: string): Promise<string | null> {
	try {
		const extracted = await extractMoveScout(response, key);
		const parsed = await parseMove(fen, extracted);
		if (parsed) return parsed;
	} catch (e) {
		console.error(`Scout extraction failed: ${e}`);
	}
	return extractSanHeuristically(response, fen);
}
