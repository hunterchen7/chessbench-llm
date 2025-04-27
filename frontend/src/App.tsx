import { Route, BrowserRouter, Routes } from 'react-router-dom';
import './App.css';
import Navbar from './components/Navbar';
import Puzzles from './Puzzles';
import Matches from './Matches';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { useEffect, useState } from 'react';

const App = () => {
  const [game, setGame] = useState(new Chess());

  const makeMove = (move: string) => {
    const newGame = game.move(move);
    if (newGame) {
      setGame(new Chess(game.fen()));
    }
  };
  const onDrop = (sourceSquare: string, targetSquare: string) => {
    const move = game.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q', // always promote to a queen for simplicity
    });
    if (move === null || game.turn() === 'w') return false; // illegal move
    setGame(new Chess(game.fen()));
    return true;
  };

  return (
    <BrowserRouter>
      <main className="min-h-screen">
        <Navbar />
        <div className="flex flex-col items-center justify-center my-4 w-1/3 mx-auto">
          <div className="text-lg">
            Play a game against <span className='font-mono bg-gray-800 px-1 rounded'>meta-llama/llama-4-scout:free</span>
          </div>
          <Chessboard position={game.fen()} onPieceDrop={onDrop} />
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
