import { neon } from '@neondatabase/serverless';

export interface Env {
	CHESSBENCH_DB_URL: string;
	OPENROUTER_API_KEY: string;
}

import { Chess, Square, SQUARES, Move, PieceSymbol } from 'chess.js';
import axios from 'axios';

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

function createPrompt(fen: string, san: boolean = true): string {
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

function createPuzzlePrompt(fen: string, san: boolean = true): string {
	const positionSummary = summarizePosition(fen, san);
	const side = new Chess(fen).turn() === 'w' ? 'white' : 'black';

	return `
You are playing a chess puzzle as ${side}. Find the best move in this position: ${JSON.stringify(positionSummary)}
`;
}

async function sendPrompt(
	prompt: string,
	model: string,
	serverUrl: string = 'https://openrouter.ai/api/v1/chat/completions',
): Promise<string | null> {
	try {
		const response = await axios.post(
			serverUrl,
			{
				model,
				messages: [{ role: 'user', content: prompt }],
			},
			{
				headers: {
					Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
				},
			},
		);

		return response.data.choices[0].message.content.trim();
	} catch (error: any) {
		console.error(`Request failed: ${error.response?.status}`);
		console.error(error.response?.data);
		return null;
	}
}

const corsHeaders = {
	'Access-Control-Allow-Origin': '*', // or specific origin like "http://localhost:3000"
	'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
	'Access-Control-Allow-Headers': 'Content-Type',
};

function withCors(response: Response): Response {
	const newResponse = new Response(response.body, response);
	Object.entries(corsHeaders).forEach(([key, value]) => {
		newResponse.headers.set(key, value);
	});
	return newResponse;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const dbUrl = env.CHESSBENCH_DB_URL;
		const sql = neon(dbUrl);

		const url = new URL(request.url);

		if (url.pathname === '/api/hello') {
			return withCors(Response.json({ message: 'Hello from Worker!' }));
		}

		if (url.pathname === '/api/time') {
			return withCors(Response.json({ now: new Date().toISOString() }));
		}

		if (url.pathname === '/api/chessbench/players') {
			try {
				const players = await sql`
				  SELECT
					players.name,
					players.rating,
					COUNT(matches.*) AS puzzles_played
					FROM players
					LEFT JOIN matches ON matches.player = players.name
					GROUP BY players.name, players.rating
					ORDER BY players.rating DESC
				`;
				return withCors(Response.json(players));
			} catch (err: any) {
				return withCors(new Response(`Database error: ${err.message}`, { status: 500 }));
			}
		}

		const playerMatchesPrefix = '/api/chessbench/puzzles';
		if (url.pathname.startsWith(playerMatchesPrefix)) {
			try {
				const playerId = url.searchParams.get('name');
				if (!playerId) {
					return withCors(new Response('Player ID not found', { status: 400 }));
				}

				const matches = await sql`
					SELECT
						matches.*,
						puzzles.rating AS puzzle_rating,
						puzzles.url_slug
					FROM matches
					JOIN puzzles ON matches.puzzle = puzzles.id
					WHERE matches.player = ${playerId}
				`;
				return withCors(Response.json(matches));
			} catch (err: any) {
				return withCors(new Response(`Database error: ${err.message}`, { status: 500 }));
			}
		}

		const playerCountMatchesPrefix = '/api/chessbench/puzzles-count';
		if (url.pathname.startsWith(playerCountMatchesPrefix)) {
			try {
				const playerId = url.searchParams.get('name');
				if (!playerId) {
					return withCors(new Response('Player ID not found', { status: 400 }));
				}
				const matches = await sql`
					SELECT COUNT(*) FROM matches WHERE player = ${playerId}
				`;

				return withCors(Response.json(matches[0]));
			} catch (err: any) {
				return withCors(new Response(`Database error: ${err.message}`, { status: 500 }));
			}
		}

		if (url.pathname.startsWith('/api/chessbench/puzzle-by-id')) {
			try {
				const puzzleId = url.pathname.split('/').pop();
				if (!puzzleId) {
					return withCors(new Response('Puzzle ID not found', { status: 400 }));
				}

				const puzzle = await sql`
					SELECT * FROM puzzles WHERE id = ${puzzleId}
				`;
				if (puzzle.length === 0) {
					return withCors(new Response('Puzzle not found', { status: 404 }));
				}
				return withCors(Response.json(puzzle[0]));
			} catch (err: any) {
				return withCors(new Response(`Database error: ${err.message}`, { status: 500 }));
			}
		}

		if (url.pathname.startsWith('/api/chessbench/random-puzzle-in-range')) {
			try {
				const range = url.pathname.split('/').pop();
				if (!range) {
					return withCors(new Response('Range not found', { status: 400 }));
				}

				const min = Number(url.searchParams.get('min')) || 0;
				const max = Number(url.searchParams.get('max')) || 4000;

				const puzzles = await sql`
					SELECT * FROM puzzles
					WHERE rating BETWEEN ${min} AND ${max}
					ORDER BY random()
					LIMIT 1
				`;
				return withCors(Response.json(puzzles));
			} catch (err: any) {
				return withCors(new Response(`Database error: ${err.message}`, { status: 500 }));
			}
		}

		if (url.pathname.startsWith('/api/chessbench/rating-history')) {
			try {
				const playerId = url.searchParams.get('name');

				const whereClause = playerId ? sql`WHERE matches.player = ${playerId}` : sql``;

				const matches = await sql`
					SELECT
						matches.*
					FROM matches
					${whereClause}
					ORDER BY matches.time ASC
				`;

				const DEFAULT_RATING = 800;

				const playerMatches: Record<string, { name: string; ratings: number[] }> = {};

				for (let match of matches) {
					const name = match.player;
					if (!playerMatches[name]) {
						playerMatches[name] = { name, ratings: [] };
					}
					const prevRating = playerMatches[name].ratings.at(-1) ?? DEFAULT_RATING;
					const newRating = prevRating + parseInt(match.rating_change);
					playerMatches[name].ratings.push(newRating);
				}

				const result = Object.values(playerMatches);
				return withCors(Response.json(result));
			} catch (err: any) {
				return withCors(new Response(`Database error: ${err.message}`, { status: 500 }));
			}
		}

		return withCors(new Response('Not Found', { status: 404 }));
	},
};
