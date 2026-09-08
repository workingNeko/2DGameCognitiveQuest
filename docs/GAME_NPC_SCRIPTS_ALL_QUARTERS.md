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

## 🗺️ Map 10: "The Submerged Aqueduct & Fountain Halls"

### 📋 Map 10 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                   THE SUBMERGED AQUEDUCT CHALLENGE                   ║
╠══════════════════════════════════════════════════════════════════════╣
║ Welcome to the Water Temple, [Player Name]!                          ║
║                                                                      ║
║ 1. Meet the 6 Elemental Water Guardians:                             ║
║    • Explore the flooded stone corridors and fountain basins.        ║
║    • Approach each guardian and HOLD FIST to view their challenge.   ║
║                                                                      ║
║ 2. Collect 6 Golden Keys:                                            ║
║    • Each correct answer awards 1 gleaming Golden Key that flies     ║
║      directly into your Objectives HUD!                              ║
║                                                                      ║
║ 3. Unlock the Aqueduct Gateway:                                      ║
║    • Once all 6 Golden Keys are collected, the water gates lower     ║
║      and the passage to the Sunken Vault opens!                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 🗺️ Map 11: "The Sunken Vault & The Ancient Key Lock"

### 📋 Map 11 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                     THE ANCIENT KEY LOCK VAULT                       ║
╠══════════════════════════════════════════════════════════════════════╣
║ Deep within the flooded sanctuary, [Player Name]!                    ║
║                                                                      ║
║ 1. Gather all 6 Golden Keys from the 6 Water Guardians.             ║
║ 2. Approach Guardian Bromen at the Ancient Lock Block.               ║
║ 3. Drag & turn each Golden Key into its corresponding keyhole.       ║
║ 4. Watch the heavy dungeon double doors swing open and enter!        ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 🗺️ Map 12: "The Grand Canal Rapids & The Lotus Raft"

### 📋 Map 12 Instructions Popup
```text
╔══════════════════════════════════════════════════════════════════════╗
║                  THE LOTUS RAFT & RAPIDS CRUISE                      ║
╠══════════════════════════════════════════════════════════════════════╣
║ The final challenge of Cognitive Quest awaits, [Player Name]!        ║
║                                                                      ║
║ 1. Open the 6 Canal Water Sluices:                                   ║
║    • Solve math challenges with the 6 Temple Guardians to fill       ║
║      the dry canal basin with rushing crystal water!                 ║
║                                                                      ║
║ 2. Restore the Helm Equation with Guardian Bromen:                   ║
║    • Arrange scattered stone runes into a balanced addition equation ║
║      [ Number ] + [ Number ] = [ Sum ] to unlock the rudder!         ║
║                                                                      ║
║ 3. Sail the Lotus Raft Across the Rapids:                            ║
║    • Board the Lotus Raft to cruise across the turbulent rapids!     ║
║                                                                      ║
║ 4. Enter the Grand Exit Portal to complete Cognitive Quest!          ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

### 💬 Stations 1–6: The 6 Elemental Water Guardians

#### 🌊 Station 1: Aqua Sprite Marina (Guardian of the Azure Fountain)
```
[Proximity Trigger]:
Aqua Sprite Marina:
“Splash! Welcome, diver! I am Marina, guardian of the crystalline azure fountain. The water currents dance to the rhythm of numbers! Hold a Closed Fist to test your math flow!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Aqua Sprite Marina:
“Hmm, that is not quite correct. You have 1 try remaining! Think carefully.”

[Feedback - Out of Tries]:
Aqua Sprite Marina:
“Out of tries! The correct answer was displayed above. Keep going—the water fountain still opened for you!”

[Feedback - Correct]:
Aqua Sprite Marina:
“Splendid! Your mathematical intellect is top-tier! The fountain shines bright!”
*(Golden Key / Sluice Emblem flies smoothly down to the Objectives HUD!)*
```

#### 🪸 Station 2: Coral Sage Sheldon (Elder of the Geyser Basin)
```
[Proximity Trigger]:
Coral Sage Sheldon:
“Greetings, patient student. I am Sheldon, keeper of the deep coral reefs. True understanding grows steadily, branch by branch. Hold a Closed Fist to consult the coral tablets!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Coral Sage Sheldon:
“Hmm, that is not quite correct. You have 1 try remaining! Think carefully.”

[Feedback - Out of Tries]:
Coral Sage Sheldon:
“Out of tries! The correct answer was displayed above. Coral wisdom rewards persistence—take this key and continue onward!”

[Feedback - Correct]:
Coral Sage Sheldon:
“Excellent! That's correct, onto the next challenge! The geyser basin pulses with energy!”
*(Golden Key / Sluice Emblem flies smoothly down to the Objectives HUD!)*
```

#### 🛡️ Station 3: Tide Knight Finneas (Champion of the Torrent Gate)
```
[Proximity Trigger]:
Tide Knight Finneas:
“Halt, young warrior! I am Finneas, champion of the torrent gate. Sharp logic is stronger than any trident! Are your counting skills ready? Hold a Closed Fist to begin the trial!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Tide Knight Finneas:
“Hmm, that is not quite correct. You have 1 try remaining! Think carefully.”

[Feedback - Out of Tries]:
Tide Knight Finneas:
“Out of tries! The correct answer was displayed above. Stand tall—a brave student learns from every trial! Take the gate key!”

[Feedback - Correct]:
Tide Knight Finneas:
“Superb! Your logic is unbreakable, adventurer! The torrent gate opens wide!”
*(Golden Key / Sluice Emblem flies smoothly down to the Objectives HUD!)*
```

#### 🦎 Station 4: Axolotl Scholar Lani (Keeper of the Pearl Falls)
```
[Proximity Trigger]:
Axolotl Scholar Lani:
“Bloop! Hello there! I am Lani, scholar of the pearl waterfalls. I love discovering patterns in the ripples! Hold a Closed Fist to see what math mystery we can solve together!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Axolotl Scholar Lani:
“Hmm, that is not quite correct. You have 1 try remaining! Think carefully.”

[Feedback - Out of Tries]:
Axolotl Scholar Lani:
“Out of tries! The correct answer was displayed above. Don't worry, friend—the pearl waterfall still reveals its treasure!”

[Feedback - Correct]:
Axolotl Scholar Lani:
“Splendid! Your mathematical intellect is top-tier! The pearl falls shimmer with golden light!”
*(Golden Key / Sluice Emblem flies smoothly down to the Objectives HUD!)*
```

#### 🐉 Station 5: River Drake Coral (Sentinel of the Grand Aqueduct)
```
[Proximity Trigger]:
River Drake Coral:
“Rumble! I am Coral the River Drake, sentinel of the grand aqueduct. Only sharp minds can navigate my aquatic channels. Hold a Closed Fist to show me your mathematical power!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
River Drake Coral:
“Hmm, that is not quite correct. You have 1 try remaining! Think carefully.”

[Feedback - Out of Tries]:
River Drake Coral:
“Out of tries! The correct answer was displayed above. Your courage is recognized! Take this aqueduct key and swim forward!”

[Feedback - Correct]:
River Drake Coral:
“Excellent! That's correct, onto the next challenge! The grand aqueduct flows without hindrance!”
*(Golden Key / Sluice Emblem flies smoothly down to the Objectives HUD!)*
```

#### 🌀 Station 6: Whirlpool Elder Glaucus (Master of Oceanic Currents)
```
[Proximity Trigger]:
Whirlpool Elder Glaucus:
“Welcome to the heart of the sanctum, master student. I am Glaucus, master of oceanic currents. You have reached the pinnacle of Quarter 4! Hold a Closed Fist for your final elemental test!”

[Gesture: Fist Closed]:
→ Pop up Dynamic Question from Database

[Feedback - Wrong / Retry]:
Whirlpool Elder Glaucus:
“Hmm, that is not quite correct. You have 1 try remaining! Think carefully.”

[Feedback - Out of Tries]:
Whirlpool Elder Glaucus:
“Out of tries! The correct answer was displayed above. The ocean embraces your whole journey! Take the final Golden Key!”

[Feedback - Correct]:
Whirlpool Elder Glaucus:
“Superb! Your logic is unbreakable, adventurer! All 6 oceanic currents are in perfect balance!”
*(Golden Key / Sluice Emblem flies smoothly down to the Objectives HUD!)*
```

---

### 🗝️ Guardian Bromen Dialogues (Map 10 & 11: Ancient Lock Block)

```
[If Keys < 6]:
Guardian Bromen:
“Halt, student! The double doors and portal are sealed.
You must first collect all 6 Golden Keys from the guardians in this chamber. (Current: [X]/6 Keys)”
[Button]: “I will go search for them”

[If Keys == 6]:
Guardian Bromen:
“Excellent! You have collected all 6 Golden Keys.
To unlock the double doors, you must now insert and turn the keys into the 6 slots on the Ancient Lock Block.”
[Button]: “Unlock the Ancient Box”

[After Solving Key Puzzle]:
Guardian Bromen:
“Outstanding work, student! The Ancient Lock Block has been solved.
The heavy double doors have swung open!
Proceed through the doorway and step into the portal to finish.”
[Button]: “Pass Through Doors”
```

---

### ⛵ Guardian Bromen & Lotus Raft Dialogues (Map 12: Rapids Cruise)

```
[If Sluices < 6]:
Guardian Bromen (Lotus Raft Guardian):
“Halt, young voyager! The Lotus Raft is safely moored.
The canal is not yet full enough to carry us across.
Open all 6 Aqueduct Sluices in the temple chambers! ([X]/6 Sluices Opened)”
[Button]: “I will go open the sluices!”

[If Sluices == 6]:
Guardian Bromen (Lotus Raft Guardian):
“Marvelous! All 6 Aqueduct Sluices are open and the canal is full!
Before we sail, the ancient rudder equation was scattered by the rapids!
Arrange the scattered runes into a correct addition equation to unlock the helm!”
[Button]: “Solve Addition Puzzle”

[After Solving Addition Altar]:
Guardian Bromen (Lotus Raft Guardian):
“Splendid addition, young voyager! The helm's rune equation is restored!
The Lotus Raft is untethered and floating on the rapids!
Walk onto the pier and hop aboard the raft to sail to the portal!”
[Button]: “Step Aboard the Raft”
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
