# 📜 Cognitive Quest 2D — Master NPC Dialogue & Script Reference
### All Quarters (1 to 4) & All Maps (1 to 12) + Stage Select Hub

> **Educational Core**: Elementary Mathematics (Grades 1–2: Geometry, Measurement, Philippine Currency, Fractions, Arithmetic & Logic)  
> **Dynamic Database Design**: All dialogues are generalized so that teachers can dynamically update question sets in the database without breaking the narrative immersion.  
> **Interactive Gesture System**:  
> 1. **Proximity Trigger**: Player walks close to an NPC $\rightarrow$ Dialogue box smoothly opens.  
> 2. **Fist Closed Gesture (or Click/Spacebar)**: Player holds a closed fist for 0.9s $\rightarrow$ Pops up the **Dynamic Question from the Database**.  
> 3. **Answer Selection (Hover + Fist Closed)**:  
>    - **Wrong (Attempt 1)**: Encouraging retry prompt without specific hints *(“Hmm, not quite! Try again.”)* $\rightarrow$ 1 try remaining.  
>    - **Out of Tries**: Encouraging line + reveals correct answer + grants stage item so quest continues.  
>    - **Correct**: Praise dialogue + Quest reward granted + Progress updates on HUD.  
> 4. **Mentor / Altar Minigame**: Once all 5 station items are collected, talk to the Stage Mentor to solve the stage puzzle and unlock the Goal Portal.

---

# 🌟 Act 0: The Awakening (Stage Select Hub / Global Intro)

*Setting: The Stage Select Hub. The Student is walking past the glowing quarter portals when the Old Man (Mentor Wizard) appears.*

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

# 🌲 QUARTER 1: GEOMETRY FOREST

---

## 🗺️ Map 1: "The Forest River & The Bridge of Shapes"

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

### 💬 Stations 1–5: Shape Guardians

#### 🟢 Station 1: Circle Guardian
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

#### ❤️ Station 2: Heart Guardian
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

#### 🟦 Station 3: Square Guardian
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

#### ⭐ Station 4: Star Guardian
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

#### 🔶 Station 5: Diamond Guardian
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

## 🗺️ Map 2: "The Shape Vault & The Matching Altar"

### 📋 Map 2 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                    THE SHAPE VAULT OF GEOMETRY                       ║
╠══════════════════════════════════════════════════════════════════════╣
║ Welcome back, [Player Name]! You are deeper in the forest!          ║
║                                                                      ║
║ 1. Find the 5 Shape Guardians:                                       ║
║    • Explore the winding trails to locate all 5 stations.            ║
║    • Hold a CLOSED FIST to answer their shape questions.             ║
║                                                                      ║
║ 2. Collect the 5 Shape Tokens:                                       ║
║    • Gather Square, Diamond, Heart, Circle, and Star tokens!         ║
║                                                                      ║
║ 3. Solve the Shape Matching Puzzle at the Altar:                     ║
║    • Meet the Old Man and match each token into its outline slot!    ║
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
You must seek out all 5 Shape Guardians in this chamber
and collect their shape tokens before the vault will respond!”

[If Tokens == 5]:
Old Man:
“Marvelous work, [Player Name]! You have gathered all 5 shape tokens: Square, Diamond, Heart, Circle, and Star.
Now, place each shape token into its matching sacred outline on the altar to unlock the path!”

[Minigame: Shape Matching Board]:
→ Drag and drop Square, Diamond, Heart, Circle, and Star into matching slots.

[On Puzzle Solved]:
Old Man:
“Well done! Every shape rests in its rightful home. The portal is open—step forward!”
```

---

## 🗺️ Map 3: "The Ancient Mosaic & The Jigsaw Trial"

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

# 🏘️ QUARTER 2: BARANGAY KALYE / BARRIOS' FIESTA

---

## 🗺️ Map 4: "The Festive Street Market"

### 📋 Map 4 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                      WELCOME TO BARANGAY KALYE!                      ║
╠══════════════════════════════════════════════════════════════════════╣
║ Mabuhay, [Player Name]! Welcome to the lively Barangay Kalye!        ║
║                                                                      ║
║ 1. Visit 5 Friendly Barrio Vendors:                                  ║
║    • Locate the Sari-Sari Store, Sorbetes Cart, Jeepney Terminal,    ║
║      Market Fruit Scale, and Parol Workshop.                         ║
║    • Hold a CLOSED FIST to solve their daily math challenges.        ║
║                                                                      ║
║ 2. Master Philippine Money, Change, & Measurements:                  ║
║    • Calculate peso change, count coins, and check weights!          ║
║                                                                      ║
║ 3. Meet the Barrio Leader at the Plaza Gate:                         ║
║    • Complete all 5 market trials to unlock the road ahead!          ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 💬 Stations 1–5: Barrio Merchants

#### 🏪 Station 1: Aling Nena (Sari-Sari Store)
```
[Proximity Trigger]:
Aling Nena:
“Mabuhay, little suki! Welcome to my Sari-Sari store. Can you help me compute? Hold a Closed Fist to get your question!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Aling Nena:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Aling Nena:
“Good effort, little suki! Take your market stamp so you can keep going!”

[Feedback - Correct]:
Aling Nena:
“Salamat! Ang galing mo naman!”
```

#### 🍦 Station 2: Mang Pedring (Sorbetes Cart)
```
[Proximity Trigger]:
Mang Pedring:
“Ting-ting-ting! Delicious Sorbetes! Hold a Closed Fist to help me!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Mang Pedring:
“Think carefully! Try again.”

[Feedback - Out of Tries]:
Mang Pedring:
“Good try! Here is your sorbetes stamp for your hard effort!”

[Feedback - Correct]:
Mang Pedring:
“Super! Here is a sweet scoop of math success!”
```

#### 🚐 Station 3: Kuya Jomar (Jeepney Terminal)
```
[Proximity Trigger]:
Kuya Jomar:
“Barya lang po sa umaga! We are ready to roll down the highway. Hold a Closed Fist to help me calculate!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Kuya Jomar:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Kuya Jomar:
“You'll get it next trip! Here is your jeepney terminal stamp!”

[Feedback - Correct]:
Kuya Jomar:
“Ayos! Next stop: Math Mastery!”
```

#### 🥭 Station 4: Ate Maria (Market Fruit Stand)
```
[Proximity Trigger]:
Ate Maria:
“Fresh sweet mangoes from Guimaras! Hold a Closed Fist to calculate!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Ate Maria:
“Think carefully! Try again.”

[Feedback - Out of Tries]:
Ate Maria:
“Good effort! Take your market fruit stamp and keep moving forward!”

[Feedback - Correct]:
Ate Maria:
“Tumpak! Perfectly balanced!”
```

#### 🏮 Station 5: Mang Carding (Parol Workshop)
```
[Proximity Trigger]:
Mang Carding:
“Maligayang Fiesta! We are crafting colorful bamboo Parols for the street lamps. Hold a Closed Fist to help me!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Mang Carding:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Mang Carding:
“Good try! Here is your final market stamp to complete your card!”

[Feedback - Correct]:
Mang Carding:
“Mabuhay! Our budget is balanced and the street lanterns shine bright!”
```

### 🎖️ Barrio Leader (Barangay Gate)
```
[If Stations < 5]:
Barrio Leader:
“Welcome to our barangay, young student!
Before we open the gate to the inner barrio, please help all 5 vendors in the street market!”

[If Stations == 5]:
Barrio Leader:
“Magaling! You have brought harmony and quick counting to our whole street market!
The road to the Barrio Garden and Bahay Kubo is open. Tuloy po kayo!”
```

---

## 🗺️ Map 5: "The Bahay Kubo Construction"

### 📋 Map 5 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                     THE BAHAY KUBO BUILD CHALLENGE                   ║
╠══════════════════════════════════════════════════════════════════════╣
║ Maligayang pagdating, [Player Name]!                                 ║
║                                                                      ║
║ 1. Help 5 Barrio Craftspeople:                                       ║
║    • Solve math challenges on Fractions, Division, Shapes, Time,     ║
║      and Garden Perimeters.                                          ║
║    • Hold a CLOSED FIST to accept each building challenge.           ║
║                                                                      ║
║ 2. Progressively Construct the Bahay Kubo:                           ║
║    • Each correct answer raises bamboo stilts, walls, nipa roof,     ║
║      and ladder!                                                     ║
║                                                                      ║
║ 3. Enter the Goal Portal once the Bahay Kubo is complete!            ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 💬 Stations 1–5: Bahay Kubo Progressive Build
```
[Proximity Trigger]:
Craftsman:
“Bayanihan in action! We are building a traditional Bahay Kubo together. Hold a Closed Fist to help us build!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Craftsman:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Craftsman:
“Good effort! The community continues to build together. Here is your construction piece!”

[Feedback - Correct]:
Craftsman:
“Bayanihan victory! Look at the Bahay Kubo—another section has been built into place!”
*(Camera pans to show bamboo stilts / woven sawali walls / nipa thatched roof assembling!)*
```

### 🔨 Master Carpenter NPC (Completed Bahay Kubo Altar)
```
[If Build Incomplete]:
Master Carpenter:
“Keep going, young builder! We need all 5 building sections completed before we can celebrate!”

[If Build Complete]:
Master Carpenter:
“Magnificent! The Bahay Kubo stands proud and strong, built by your mathematical teamwork!
The road to the Grand Plaza is open!”
```

---

## 🗺️ Map 6: "The Grand Fiesta Plaza"

### 📋 Map 6 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                     THE GRAND FIESTA CELEBRATION                     ║
╠══════════════════════════════════════════════════════════════════════╣
║ It's Fiesta Day, [Player Name]!                                      ║
║                                                                      ║
║ 1. Complete the 5 Plaza Celebration Stations:                         ║
║    • Help the fiesta committee with band schedules, food portions,   ║
║      game prizes, and banner lengths!                                ║
║                                                                      ║
║ 2. Unlock the Golden Portal to the Monetary Desert (Quarter 3)!      ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 💬 Stations 1–5: Fiesta Committee
```
[Proximity Trigger]:
Committee Member:
“Maligayang Fiesta! The plaza games and celebrations need our help! Hold a Closed Fist to help us prepare!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Committee Member:
“Think carefully! Try again.”

[Feedback - Out of Tries]:
Committee Member:
“Good effort! Take this fiesta ribbon so the celebration continues!”

[Feedback - Correct]:
Committee Member:
“Viva! Everything is organized to perfection! The crowd cheers!”
```

### 👑 Hermano Mayor (Fiesta Grand Stage)
```
[If Stations < 5]:
Hermano Mayor:
“Welcome, guest of honor! Help all 5 plaza stations so the fiesta can reach its peak!”

[If Stations == 5]:
Hermano Mayor:
“Mabuhay ang Fiesta! You have brought joy, fairness, and mathematical brilliance to our whole town!
The golden portal to Quarter 3: Monetary Desert is now open!”
```

---

# 🏜️ QUARTER 3: MONETARY DESERT & ANCIENT RUINS

---

## 🗺️ Maps 7, 8, & 9: "The Desert Treasury & Pharaoh's Vault"

### 📋 Quarter 3 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                     THE MONETARY DESERT EXPEDITION                   ║
╠══════════════════════════════════════════════════════════════════════╣
║ Welcome to the golden sands, [Player Name]!                          ║
║                                                                      ║
║ 1. Explore the Ancient Desert Ruins:                                 ║
║    • Find the 5 Desert Sages guarding the golden currency stations.  ║
║    • Hold a CLOSED FIST to decode ancient trade tablets.             ║
║                                                                      ║
║ 2. Solve Multi-Step Money & Currency Problems:                       ║
║    • Add and subtract Philippine Peso bills and coins!               ║
║                                                                      ║
║ 3. Unlock the Pharaoh's Golden Vault to reach Quarter 4!             ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 💬 Stations 1–5: Desert Sages
```
[Proximity Trigger]:
Desert Sage:
“Traveler of the sands! Ancient treasures belong only to those who seek knowledge. Hold a Closed Fist to consult the desert trade tablet!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Desert Sage:
“Hmm, not quite! Try again.”

[Feedback - Out of Tries]:
Desert Sage:
“The desert winds teach patience. Take this trade seal and press forward!”

[Feedback - Correct]:
Desert Sage:
“Wise and true! The golden sands resonate with your accurate calculation. Take this desert seal!”
```

### 🏺 Desert Vault Keeper (Final Altar)
```
[If Seals < 5]:
Desert Vault Keeper:
“Halt, traveler! The Pharaoh's treasury remains locked. Gather all 5 trade seals from the desert sages!”

[If Seals == 5]:
Desert Vault Keeper:
“You have braved the shifting dunes and mastered the ancient tests!
The sacred vault unlocks, revealing the shimmering waterway to the Water Temple!
Proceed, champion!”
```

---

# 🌊 QUARTER 4: UNDERWATER DUNGEON & WATER TEMPLE

---

## 🗺️ Maps 10, 11, & 12: "The Temple Aqueduct, Lotus Raft, & Final Sanctum"

### 📋 Quarter 4 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                     THE WATER TEMPLE SANCTUARY                       ║
╠══════════════════════════════════════════════════════════════════════╣
║ Dive deep into the sunken sanctum, [Player Name]!                    ║
║                                                                      ║
║ 1. Locate the 5 Water Temple Guardians:                              ║
║    • Find each guardian stationed along the submerged aqueducts.     ║
║    • Hold a CLOSED FIST to solve advanced grade-level challenges.    ║
║                                                                      ║
║ 2. Collect 5 Golden Keys:                                            ║
║    • Watch each key fly into your Objectives HUD upon success!       ║
║                                                                      ║
║ 3. Activate the Lotus Raft & Floodgate Controls:                     ║
║    • Unlock the Master Temple Sanctum to complete Cognitive Quest!   ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 💬 Stations 1–5: Water Temple Guardians
```
[Proximity Trigger]:
Water Guardian:
“Greetings, seeker of the deep! The clear waters flow according to perfect mathematical harmony. Hold a Closed Fist to channel your logical power!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Water Guardian:
“Think carefully! Try again.”

[Feedback - Out of Tries]:
Water Guardian:
“The ocean rewards perseverance. Here is your Golden Key so your quest can proceed!”

[Feedback - Correct]:
Water Guardian:
“Splendid! The waters shine bright! A Golden Key flies into your Objectives HUD!”
*(Golden Key award animation flies smoothly down to the Objectives HUD!)*
```

### 🔱 Temple Elder (Master Floodgate Altar)
```
[If Keys < 5]:
Temple Elder:
“Halt, brave diver! The master floodgate remains sealed.
Collect all 5 Golden Keys from the Water Guardians to calm the currents!”

[If Keys == 5]:
Temple Elder:
“Incredible, [Player Name]! All 5 Golden Keys are in place!
The aqueducts align, the lotus raft glides forward, and the grand sanctuary is unlocked!
You have mastered mathematics from the tallest forest trees to the deepest ocean temples!”
```

---

# 🎓 GRAND VICTORY REPORT CARD SPEECH
*(Delivered by Old Man / Grand Mentor upon beating all 4 Quarters)*

```
Old Man:
“Hail, Master Mathematician [Player Name]!
Look how far you have journeyed:
• You built bridges and solved geometric riddles in the Geometry Forest!
• You united communities through fair trade and Bayanihan in Barangay Kalye!
• You unlocked ancient treasures in the Monetary Desert!
• And you brought harmony to the depths of the Water Temple!

You have discovered the greatest truth of all:
Math is the ultimate magic, and with logic, courage, and perseverance,
there is no problem in this world you cannot solve!

Congratulations on completing Cognitive Quest!”
```

---
*Created for Cognitive Quest 2D — Comprehensive Master NPC Dialogue & System Script.*
