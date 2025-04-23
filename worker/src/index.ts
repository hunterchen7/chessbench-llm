import { neon } from '@neondatabase/serverless';

export interface Env {
	CHESSBENCH_DB_URL: string;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const dbUrl = env.CHESSBENCH_DB_URL;
		const sql = neon(dbUrl);

		const url = new URL(request.url);

		if (url.pathname === '/api/hello') {
			return Response.json({ message: 'Hello from Worker!' });
		}

		if (url.pathname === '/api/time') {
			return Response.json({ now: new Date().toISOString() });
		}

		if (url.pathname === '/api/chessbench/players') {
			try {
				const players = await sql`SELECT * FROM players SORT BY rating DESC`;
				return Response.json(players);
			} catch (err: any) {
				return new Response(`Database error: ${err.message}`, { status: 500 });
			}
		}

		const playerMatchesPrefix = '/api/chessbench/matches';
		if (url.pathname.startsWith(playerMatchesPrefix)) {
			try {
				const playerId = url.searchParams.get('name');
				if (!playerId) {
					return new Response('Player ID not found', { status: 400 });
				}

				const matches = await sql`
					SELECT * FROM matches WHERE player = ${playerId}
				`;
				return Response.json(matches);
			} catch (err: any) {
				return new Response(`Database error: ${err.message}`, { status: 500 });
			}
		}

		if (url.pathname.startsWith('/api/chessbench/puzzle-by-id')) {
			try {
				const puzzleId = url.pathname.split('/').pop();
				if (!puzzleId) {
					return new Response('Puzzle ID not found', { status: 400 });
				}

				const puzzle = await sql`
					SELECT * FROM puzzles WHERE id = ${puzzleId}
				`;
				if (puzzle.length === 0) {
					return new Response('Puzzle not found', { status: 404 });
				}
				return Response.json(puzzle[0]);
			} catch (err: any) {
				return new Response(`Database error: ${err.message}`, { status: 500 });
			}
		}

		if (url.pathname.startsWith('/api/chessbench/random-puzzle-in-range')) {
			try {
				const range = url.pathname.split('/').pop();
				if (!range) {
					return new Response('Range not found', { status: 400 });
				}

				const min = Number(url.searchParams.get('min')) || 0;
				const max = Number(url.searchParams.get('max')) || 4000;

				const puzzles = await sql`
					SELECT * FROM puzzles
					WHERE rating BETWEEN ${min} AND ${max}
					ORDER BY random()
					LIMIT 1
				`;
				return Response.json(puzzles);
			} catch (err: any) {
				return new Response(`Database error: ${err.message}`, { status: 500 });
			}
		}

		return new Response('Not Found', { status: 404 });
	},
};
