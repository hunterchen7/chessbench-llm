import { useEffect, useState } from "react";
import { fetchWithPrefix } from "../utils/fetch";

interface Ply {
  ply: number;
  move: string;
  response: string;
}

const URL_PREFIX = "https://lichess.org/";

interface Puzzle {
  id: number;
  player: string;
  url_slug: string;
  puzzle: string;
  rating_change: number;
  time: string;
  notes: Ply[];
  puzzle_rating: number;
}

const toLocaleString = (date: string) => {
  const d = new Date(date);
  return d.toLocaleString("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

const PlayerPuzzles = ({ player }: { player: string }) => {
  const [puzzles, setPuzzles] = useState<Puzzle[]>([]);

  useEffect(() => {
    fetchWithPrefix(`/api/chessbench/puzzles?name=${player}`).then((res) => {
      if (res.ok) {
        res.json().then((data: Puzzle[]) => {
          data.reverse();
          setPuzzles(data);
        });
      } else {
        console.error("Failed to fetch puzzles");
      }
    });
  }, [player]);

  return (
    <div className="overflow-x-auto w-full max-h-[70vh] overflow-y-auto">
      <table className="min-w-full bg-gray-800 text-white border border-gray-700">
        <thead>
          <tr>
            <th className="px-4 py-2 border-r border-gray-700">Puzzle ID</th>
            <th className="px-4 py-2 border-r border-gray-700">Rating Change</th>
            <th className="px-4 py-2">Time Played</th>
          </tr>
        </thead>
        <tbody>
          {
            puzzles.map((puzzle) => (
              <tr key={puzzle.id} className="hover:bg-gray-700 border border-gray-700">
                <td className="px-4 py-2 border-r border-gray-700">
                  <a href={`${URL_PREFIX}${puzzle.url_slug}`} target="_blank" rel="noopener noreferrer" className="cursor-pointer hover:text-gray-400 underline transition-all w-fit">
                    {puzzle.puzzle}
                  </a>
                </td>
                <td className="px-4 py-2 text-center border-r border-gray-700">{puzzle.rating_change}</td>
                <td className="px-4 py-2 text-center">{toLocaleString(puzzle.time)}</td>
              </tr>
            ))
          }
        </tbody>
      </table>
    </div>
  );


}

export default PlayerPuzzles;