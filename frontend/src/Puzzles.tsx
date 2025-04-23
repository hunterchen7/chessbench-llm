import { useState } from "react";
import Modal from "./components/Modal";

const Puzzles = () => {
  const [methodology, setMethodology] = useState(false);

  return (
    <div className="flex flex-col items-center justify-center">
      <h1 className="text-2xl font-bold my-4">Puzzles Leaderboard</h1>
      <div className="text-lg mb-4 underline hover:cursor-pointer hover:text-gray-300" onClick={() => setMethodology(true)}>
        view methodology
      </div>
      {
        methodology && (
          <Modal isOpen={methodology} onClose={() => setMethodology(false)}>
            <div className="text-md text-left bg-gray-600 p-4 rounded-lg mx-auto">
              <h2 className="text-lg font-bold mb-2">Methodology</h2>
              <p>
                Each model starts with an Elo rating of 800, with a K factor of 256 which linearly decays over 12 rounds to 16.
              </p>
              <br />
              <p>
                Outcome is computed as 1 if all moves are correct, 0.5 if more than half of the moves are correct, and 0 if less than half of the moves are correct.
              </p>
              <br />
              <p>
                Each model is prompted with the following prompt:
                <div className="bg-gray-700 p-2 rounded-lg mt-2 text-left">
                  You are playing a chess puzzle as (side). Find the best move in this position:
                  <ul className="list-disc list-inside text-left ml-3 pl-3">
                    <li>position of white pieces</li>
                    <li>position of black pieces</li>
                    <li>list of legal moves in <a
                      className="underline text-blue-400 hover:text-blue-600"
                      href="https://en.wikipedia.org/wiki/Algebraic_notation_(chess)"
                      target="_blank"
                      rel="noopener noreferrer"
                    >SAN notation</a>
                    </li>
                  </ul>
                </div>
              </p>
              <p className="mt-4">
                There is definitely room for improvement on the prompt, but this is a reasonable start. The returned response is parsed by <span className="font-mono">meta-llama/llama-4-scout</span> to extract the best move, with a manually written heuristic as a fallback.
              </p>
              <p className="mt-4 text-left">
                The methodology is definitely flawed, other things to consider are:
                <ul className="list-disc list-inside text-left ml-3 pl-3">
                  <li>Models don&apos;t solve the same puzzles (there is a puzzle bank of ~1.4M puzzles, all puzzles with 1000+ solves on Lichess), so performance isn&apos;t tested on the same puzzles, and some of the same rating would be easier for LLMs to solve vs. others</li>
                  <li>The notation given in SAN likely causes some amount of bias, since checks, captures and most importantly checkmates are all captured in the notation</li>
                  <li>There is no consideration for puzzle rating deviation, and Elo is a fairly flawed rating system compared to Glicko and the likes, but it was used for simplicity sake.</li>
                </ul>
              </p>
            </div>
          </Modal>
        )
      }
    </div>
  );
}

export default Puzzles;