# 📜 Quarter 1: Geometry Forest — Generalized NPC Dialogue & Script Reference

> **Theme**: 2D Shapes, Spatial Reasoning, Composite Figures, and Logic  
> **Target Audience**: Early Grade School / Child-Friendly, Encouraging, Educational  
> **Dynamic DB Flow**:
> 1. **Proximity Trigger**: Player walks near an NPC $\rightarrow$ Dialogue box opens automatically.
> 2. **Fist Closed Gesture (or Click/Spacebar)**: Player holds a Closed Fist $\rightarrow$ Pops up the **Dynamic Question from Database**.
> 3. **Answer Selection (Hover + Fist Closed)**:
>    - **Wrong (Attempt 1)**: Encouraging retry prompt without specific hints *(“Hmm, not quite! Try again.”)* $\rightarrow$ 1 retry.
>    - **Out of Tries**: Educational explanation + reveals correct concept + grants stage piece.
>    - **Correct**: Praise dialogue + Awards quest item (bridge plank, shape token, jigsaw piece) + Updates HUD.
> 4. **Mentor / Altar Minigame**: Solve the Old Man's riddle or puzzle to open the Goal Portal.

---

## 🌟 Act 0: The Awakening (Stage Select Hub / Prologue)

*Setting: The Stage Select clearing. The Student is walking through the hub when an elderly mentor in wizard robes calls out.*

```
Old Man:
“Stop right there!”

Student:
“Huh? Why?”

Old Man:
“I see in you such greatness! Someday you will do these lands great good. But only when trained. For now, it is only potential.”

Student:
“What shall I do?”

Old Man:
“Come! Come! Join me in my realm. Enter this portal and let's train your mind. You shall learn the ways of math! You see, it is like magic, but it runs on logic instead of spells!”

Student:
“That's amazing! I want to learn!”

Old Man:
“I like your enthusiasm! Follow me into the portal!”
```

---

## 🌲 Act 1: Map 1 — "The Forest River & The Bridge of Shapes"

### 📋 Map 1 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                    WELCOME TO GEOMETRY FOREST!                       ║
╠══════════════════════════════════════════════════════════════════════╣
║ Hello, [Player Name]! The magical river has no crossing!            ║
║                                                                      ║
║ 1. Answer 5 Geometry Questions & Build the Bridge:                   ║
║    • Find all 5 Shape Guardians hidden in the forest.                ║
║    • Approach each guardian and HOLD FIST to view the question.      ║
║    • Each correct answer constructs 1 wooden plank across the river! ║
║                                                                      ║
║ 2. Cross the Bridge to the Old Man:                                  ║
║    • Once all 5 planks are laid, cross the water safely.             ║
║                                                                      ║
║ 3. Solve the Old Man's Riddle:                                       ║
║    • Speak to the Old Man and answer his secret shape riddle!        ║
║                                                                      ║
║ 4. Enter the Goal Portal:                                            ║
║    • Step into the golden portal to complete Map 1!                  ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

### 🟢 Station 1: Circle Guardian
```
[Proximity Trigger]:
Circle Guardian:
“Greetings, little explorer! I am the Circle Guardian. I roll with joy because I have no pointy corners! Are you ready for my shape challenge? Hold a Closed Fist to begin!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Circle Guardian:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Circle Guardian:
“The correct answer was displayed above! Keep practicing and your mind will grow stronger. Here is your first bridge plank!”

[Feedback - Correct]:
Circle Guardian:
“Amazing! That is correct! One bridge plank has appeared over the river!”
```

---

### ❤️ Station 2: Heart Guardian
```
[Proximity Trigger]:
Heart Guardian:
“Hello, bright student! My heart beats with excitement. Let's see if you can divide shapes equally. Hold a Closed Fist to see your challenge!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Heart Guardian:
“Think carefully! Try again.”

[Feedback - Out of Tries]:
Heart Guardian:
“Good effort! Take this bridge plank for your hard work!”

[Feedback - Correct]:
Heart Guardian:
“That's great! Another bridge plank just floated into place over the river!”
```

---

### 🟦 Station 3: Square Guardian
```
[Proximity Trigger]:
Square Guardian:
“Stand tall, student! I am the Square Guardian. All four of my sides are equal and strong. Hold a Closed Fist to test your shape building knowledge!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Square Guardian:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Square Guardian:
“Good try! Here is your third bridge plank!”

[Feedback - Correct]:
Square Guardian:
“Splendid! The third bridge plank is now securely placed across the stream!”
```

---

### ⭐ Station 4: Star Guardian
```
[Proximity Trigger]:
Star Guardian:
“Twinkle, twinkle, young adventurer! I shine bright high in the sky. When shapes glide, they follow mathematical rules. Hold a Closed Fist to begin!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Star Guardian:
“Think carefully! Try again.”

[Feedback - Out of Tries]:
Star Guardian:
“You will get it better next time! Keep going—here is your fourth bridge plank!”

[Feedback - Correct]:
Star Guardian:
“You're good at this! Only one bridge plank left before the river can be crossed!”
```

---

### 🔶 Station 5: Diamond Guardian
```
[Proximity Trigger]:
Diamond Guardian:
“Welcome to the final station, champion! I sparkle with sharp angles. Hold a Closed Fist to take on my composite figure challenge!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Diamond Guardian:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Diamond Guardian:
“You did your best! The fifth bridge plank is now laid. Cross over to meet the Old Man!”

[Feedback - Correct]:
Diamond Guardian:
“Brilliant! The bridge across the river is now fully built! Cross over and speak to the Old Man!”
```

---

### 🧙‍♂️ Old Man NPC (Map 1 Exit Clearing)
```
[If Approached Before Bridge is Built]:
Old Man:
“Halt, young traveler! Beyond this point lies the portal.
But to pass, you must build the bridge first and answer my riddle!
Go back and solve the shape puzzles in the forest.”

[If Bridge is Complete]:
Old Man:
“Ah! You have crossed the Bridge of Shapes! But before the portal opens, you must prove your wisdom. Hear my riddle:
*(This will be randomized from 10 shape riddles in the database)*
→ Choices: [A]  [B]  [C]  [D]

[If Wrong Riddle Choice]:
Old Man:
“That is incorrect, young adventurer! Think carefully and try again.”

[If Correct Riddle Choice]:
Old Man:
“Outstanding, young adventurer! You have built the bridge and solved my riddle!
You may now enter the portal and proceed on your quest. Safe travels!”
```

---

## 🌺 Act 2: Map 2 — "The Shape Vault & The Matching Altar"

### 📋 Map 2 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                    THE SHAPE VAULT OF GEOMETRY                       ║
╠══════════════════════════════════════════════════════════════════════╣
║ Welcome back, [Player Name]! You are deeper in the forest!          ║
║                                                                      ║
║ 1. Find the 5 Shape Guardians:                                       ║
║    • Explore the winding trails to find Circle, Heart, Square,       ║
║      Star, and Diamond.                                              ║
║    • Hold a CLOSED FIST to answer their shape questions.             ║
║                                                                      ║
║ 2. Collect the 5 Shape Tokens:                                       ║
║    • Gather Square, Diamond, Heart, Circle, and Star tokens!         ║
║                                                                      ║
║ 3. Solve the Shape Matching Puzzle at the Altar:                     ║
║    • Meet the Old Man at the sacred altar.                           ║
║    • Drag and match each shape token into its glowing outline slot!  ║
║                                                                      ║
║ 4. Enter the Goal Portal to finish Map 2!                            ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 💬 Stations 1–5: Shape Tokens Collection
```
[Proximity Trigger]:
Guardian:
“Greetings, [Player Name]! The Shape Vault requires our sacred shape tokens. Prove your shape mastery! Hold a Closed Fist to reveal your question!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Guardian:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Guardian:
“Good effort! Take this Shape Token so your quest can continue!”

[Feedback - Correct]:
Guardian:
“Spot on! Take this glowing Shape Token to the Old Man's altar!”
```

### 🧙‍♂️ Old Man NPC (Map 2 Altar)
```
[If Tokens < 5]:
Old Man:
“Halt, young traveler! The altar remains dormant.
You must seek out all 5 Shape Guardians in this forest chamber
and collect their 5 shape tokens before the vault will respond!”

[If Tokens == 5]:
Old Man:
“Marvelous work, [Player Name]! You have gathered all 5 shape tokens: Square, Diamond, Heart, Circle, and Star.
Now, place each shape token into its matching sacred slot on the altar to unlock the path!”

[Minigame: Shape Matching Board]:
→ Drag and drop Square, Diamond, Heart, Circle, and Star into matching slots.

[On Puzzle Solved]:
Old Man:
“Well done! Every shape rests perfectly in its rightful home.
The ancient vault has recognized your spatial mastery.
The portal is open—step forward to your final forest trial!”
```

---

## 🧩 Act 3: Map 3 — "The Ancient Mosaic & The Jigsaw Trial"

### 📋 Map 3 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                   THE ANCIENT MOSAIC OF THE FOREST                   ║
╠══════════════════════════════════════════════════════════════════════╣
║ You have reached the inner Forest, [Player Name]!                   ║
║                                                                      ║
║ 1. Gather all 5 Jigsaw Pieces:                                       ║
║    • Find the 5 Shape Guardians across the forest ruins.             ║
║    • Hold a CLOSED FIST to solve their geometric challenges.         ║
║                                                                      ║
║ 2. Bring the Pieces to the Old Man:                                  ║
║    • Reach the Old Man near the Master Portal.                       ║
║                                                                      ║
║ 3. Assemble the Master Jigsaw Puzzle:                                ║
║    • Interlock the 5 pieces to reconstruct the ancient portrait!     ║
║                                                                      ║
║ 4. Step Through the Master Portal to finish Quarter 1!               ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 💬 Stations 1–5: Jigsaw Pieces Collection
```
[Proximity Trigger]:
Guardian:
“You've reached the depths of the forest! The ancient guardian painting has been scattered. Hold a Closed Fist to earn a mosaic slice!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Guardian:
“Think carefully! Try again.”

[Feedback - Out of Tries]:
Guardian:
“Good try! Take this jigsaw slice to help restore the ancient painting!”

[Feedback - Correct]:
Guardian:
“Fantastic! Here is your interlocking jigsaw piece. Bring it to the Old Man!”
```

### 🧙‍♂️ Old Man NPC (Map 3 Final Altar & Grand Finale)
```
[If Jigsaw Pieces < 5]:
Old Man:
“Halt, young traveler! Beyond this point lies the master portal.
Gather all 5 jigsaw puzzle pieces first and solve my puzzle!”

[If Jigsaw Pieces == 5]:
Old Man:
“Excellent work gathering the puzzle pieces, [Player Name]!
Now you must solve the jigsaw puzzle using what you got.
Fit the interlocking edges together to reveal the ancient guardian portrait.
Are you ready?”

[Minigame: 5-Piece Jigsaw Assembly]:
→ Drag and assemble the interlocking vertical jigsaw slices into the frame.

[On Puzzle Solved]:
Old Man:
“Outstanding, young adventurer [Player Name]! You have restored the portrait with mathematical precision!
The Geometry Forest is peaceful once again.
The gates to Quarter 2: Barangay Kalye are now open!
Onward to your next adventure!”
```

---
*Created for Cognitive Quest 2D / Grade 1 Elementary Mathematics Curriculum.*
