Puzzles:

use `puzzlebench.py` to run some benchmarks, i have a postgres db set up elsewhere where the results get pushed

starting Elo for matches.json was 1500, i'm lowering to 800.

i want to play around more with the prompt, to see if i can get more performance out of it and stop the models from making super obvious mistakes, like hanging pieces in 1, etc

i've noticed that a bunch of times it'll go for a check which hangs the piece at the same time, it's a little strange (even in the strongest models, Gemini 2.5 Pro Preview, etc)

another thing is i think giving it SAN notation makes it stronger than UCI notation, since the `+` and `#` notation makes it want to play those moves more, not sure if it also likes captures too (`x`)

i was also getting some werid issues with qwq-32b, deepseek r1, o3 mini high and o4 mini high so they've been excluded

i'm not made of money so i'm not running O3, gemini 2.5 pro preview hurts enough

- `uvicorn llm_server:app --host 0.0.0.0 --port 8000` to start the server
- `python chessbench.py` to make the server play against itself

this is a game that Qwen2.5-1.5B-instruct "played" against itself.

played in quotes because there is some jank processing going on to extract moves

=== Turn 1 White ===

Move played: Nh3
```
r n b q k b n r
p p p p p p p p
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . N
P P P P P P P P
R N B Q K B . R
```

=== Turn 1 Black ===

Move played: Nh6
```
r n b q k b . r
p p p p p p p p
. . . . . . . n
. . . . . . . .
. . . . . . . .
. . . . . . . N
P P P P P P P P
R N B Q K B . R
```

=== Turn 2 White ===

Move played: Ng5
```
r n b q k b . r
p p p p p p p p
. . . . . . . n
. . . . . . N .
. . . . . . . .
. . . . . . . .
P P P P P P P P
R N B Q K B . R
```

=== Turn 2 Black ===

Move played: e5
```
r n b q k b . r
p p p p . p p p
. . . . . . . n
. . . . p . N .
. . . . . . . .
. . . . . . . .
P P P P P P P P
R N B Q K B . R
```

=== Turn 3 White ===

Move played: Nf3
```
r n b q k b . r
p p p p . p p p
. . . . . . . n
. . . . p . . .
. . . . . . . .
. . . . . N . .
P P P P P P P P
R N B Q K B . R
```

=== Turn 3 Black ===

Move played: Be7
```
r n b q k . . r
p p p p b p p p
. . . . . . . n
. . . . p . . .
. . . . . . . .
. . . . . N . .
P P P P P P P P
R N B Q K B . R
```

=== Turn 4 White ===

Move played: Ng5
```
r n b q k . . r
p p p p b p p p
. . . . . . . n
. . . . p . N .
. . . . . . . .
. . . . . . . .
P P P P P P P P
R N B Q K B . R
```

=== Turn 4 Black ===

Move played: Rf8
```
r n b q k r . .
p p p p b p p p
. . . . . . . n
. . . . p . N .
. . . . . . . .
. . . . . . . .
P P P P P P P P
R N B Q K B . R
```

=== Turn 5 White ===

Move played: Nf3
```
r n b q k r . .
p p p p b p p p
. . . . . . . n
. . . . p . . .
. . . . . . . .
. . . . . N . .
P P P P P P P P
R N B Q K B . R
```

=== Turn 5 Black ===

Failed to extract a legal move. Game aborted.

=== Game Over ===
Result: *

Final FEN: rnbqkr2/ppppbppp/7n/4p3/8/5N2/PPPPPPPP/RNBQKB1R b KQq - 5 5

Moves played:
01. White: Nh3
02. Black: Nh6
03. White: Ng5
04. Black: e5
05. White: Nf3
06. Black: Be7
07. White: Ng5
08. Black: Rf8
09. White: Nf3
