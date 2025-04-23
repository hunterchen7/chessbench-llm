import { Route, BrowserRouter, Routes } from 'react-router-dom';
import './App.css';
import Navbar from './components/Navbar';
import Puzzles from './Puzzles';
import Matches from './Matches';

const App = () => {
  return (
    <BrowserRouter>
      <main className="min-h-screen">
        <Navbar />
        <Routes>
          <Route path="/puzzles" element={<Puzzles />} />
          <Route path="/matches" element={<Matches />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
};

export default App;
