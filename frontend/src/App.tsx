import { Route, BrowserRouter, Routes } from 'react-router-dom';
import './App.css';
import Navbar from './components/Navbar';
import Puzzles from './Puzzles';
import Matches from './Matches';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { useEffect, useState } from 'react';
import { fetchWithPrefix as fetch } from './utils/fetch';

const App = () => {
  const [game, setGame] = useState(new Chess());
  const [isAIThinking, setIsAIThinking] = useState(false);

  const onDrop = (sourceSquare: string, targetSquare: string) => {
    const move = game.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q', // always promote to a queen for simplicity
    });
    if (move === null || game.turn() === 'w') return false; // illegal move
    setGame(new Chess(game.fen()));
    setIsAIThinking(true);

    // prompt the AI to make a move
    fetch('ai-move?fen=' + game.fen())
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        response.json().then((res) => {
          if (res.move) {
            game.move(res.move);
            setGame(new Chess(game.fen()));
          }
        });
        setIsAIThinking(false);
      }).catch((error) => {
        console.error('Error fetching AI move:', error);
        setIsAIThinking(false);
      });
    return true;
  };

  return (
    <BrowserRouter>
      <main className="min-h-screen">
        <Navbar />
        <div className="flex flex-col items-center justify-center my-4 mx-auto">
          <div className='flex'>
            <div className='flex flex-col w-[80vh]'>
              <div className="text-lg text-center">
                Play a game against <span className='font-mono bg-gray-800 px-1 rounded'>meta-llama/llama-4-scout:free</span></div>
              <Chessboard position={game.fen()} onPieceDrop={onDrop} />
            </div>
            <div>
              {isAIThinking ? (
                <div className="text-lg text-center">
                  AI is thinking...
                </div>
              ) : (
                <div className="text-lg text-center">
                  AI is waiting for your move.
                </div>
              )}
            </div>
          </div>

        </div>
        <Routes>
          <Route path="/puzzles" element={<Puzzles />} />
          <Route path="/matches" element={<Matches />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
};

export default App;
