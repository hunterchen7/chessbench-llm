const Navbar = () => (
  <nav className="bg-gray-800 text-white px-5 py-5 flex justify-between items-center select-none">
    <div className="text-xl font-semibold">Chessbench</div>
    <ul className="flex space-x-4">
      <li><a href="/" className="hover:underline">Home</a></li>
      <li><a href="/puzzles" className="hover:underline">Puzzles</a></li>
      <li><a href="/matches" className="hover:underline">Matches</a></li>
      <li><a href="https://github.com/hunterchen7/chessbench-llm" className="hover:underline" target="_blank" rel="noreferrer">GitHub</a></li>
    </ul>
  </nav>
);

export default Navbar;