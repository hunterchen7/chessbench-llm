import { neon } from '@neondatabase/serverless';

export interface Env {
	CHESSBENCH_DB_URL: string;
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
					SELECT * FROM matches WHERE player = ${playerId}
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

		return withCors(new Response('Not Found', { status: 404 }));
	},
};
