# core/npc_scripts.py
"""
Master NPC Dialogue & Script Reference Data for Cognitive Quest 2D.
Covers All Quarters (1 to 4) & All Maps (1 to 12) + Stage Select Hub.
Corresponds directly to docs/GAME_NPC_SCRIPTS_ALL_QUARTERS.md.
"""

MAP_INSTRUCTIONS_DATA = {
    "map1.txt": {
        "title": "WELCOME TO GEOMETRY FOREST!",
        "subtitle": "Hello, {player_name}! The magical river has no crossing!",
        "theme": "forest",
        "steps": [
            {
                "title": "1. Answer 5 Geometry Questions & Build the Bridge:",
                "bullets": [
                    "Find all 5 Shape Guardians hidden in the forest.",
                    "Approach each guardian and HOLD FIST to view the question.",
                    "Each correct answer constructs 1 wooden plank across the river!"
                ]
            },
            {
                "title": "2. Cross the Bridge to the Old Man:",
                "bullets": [
                    "Once all 5 planks are laid, cross the water safely."
                ]
            },
            {
                "title": "3. Solve the Old Man's Riddle:",
                "bullets": [
                    "Speak to the Old Man and answer his secret shape riddle!"
                ]
            },
            {
                "title": "4. Enter the Goal Portal:",
                "bullets": [
                    "Step into the golden portal to complete Map 1!"
                ]
            }
        ]
    },
    "map2.txt": {
        "title": "THE SHAPE VAULT OF GEOMETRY",
        "subtitle": "Welcome back, {player_name}! You are deeper in the forest!",
        "theme": "forest",
        "steps": [
            {
                "title": "1. Find the 5 Shape Guardians:",
                "bullets": [
                    "Explore the winding trails to locate all 5 stations.",
                    "Hold a CLOSED FIST to answer their shape questions."
                ]
            },
            {
                "title": "2. Collect the 5 Shape Tokens:",
                "bullets": [
                    "Gather Square, Diamond, Heart, Circle, and Star tokens!"
                ]
            },
            {
                "title": "3. Solve the Shape Matching Puzzle at the Altar:",
                "bullets": [
                    "Meet the Old Man and match each token into its outline slot!"
                ]
            },
            {
                "title": "4. Enter the Goal Portal to finish Map 2!",
                "bullets": []
            }
        ]
    },
    "map3.txt": {
        "title": "THE ANCIENT MOSAIC OF THE FOREST",
        "subtitle": "You have reached the inner Forest, {player_name}!",
        "theme": "forest",
        "steps": [
            {
                "title": "1. Gather all 5 Jigsaw Pieces:",
                "bullets": [
                    "Find the 5 Shape Guardians across the forest ruins.",
                    "Hold a CLOSED FIST to solve their geometric challenges."
                ]
            },
            {
                "title": "2. Bring the Pieces to the Old Man:",
                "bullets": [
                    "Reach the Old Man near the Master Portal."
                ]
            },
            {
                "title": "3. Assemble the Master Jigsaw Puzzle:",
                "bullets": [
                    "Interlock the 5 pieces to reconstruct the ancient portrait!"
                ]
            },
            {
                "title": "4. Step Through the Master Portal to finish Quarter 1!",
                "bullets": []
            }
        ]
    },
    "map4.txt": {
        "title": "WELCOME TO BARANGAY KALYE!",
        "subtitle": "Mabuhay, {player_name}! Welcome to the lively Barangay Kalye!",
        "theme": "fiesta",
        "steps": [
            {
                "title": "1. Visit 5 Friendly Barrio Vendors:",
                "bullets": [
                    "Locate the Sari-Sari Store, Sorbetes Cart, Jeepney Terminal, Market Fruit Scale, and Parol Workshop.",
                    "Hold a CLOSED FIST to solve their daily math challenges."
                ]
            },
            {
                "title": "2. Master Philippine Money, Change, & Measurements:",
                "bullets": [
                    "Calculate peso change, count coins, and check weights!"
                ]
            },
            {
                "title": "3. Meet the Barrio Leader at the Plaza Gate:",
                "bullets": [
                    "Complete all 5 market trials to unlock the road ahead!"
                ]
            }
        ]
    },
    "map5.txt": {
        "title": "THE BAHAY KUBO BUILD CHALLENGE",
        "subtitle": "Maligayang pagdating, {player_name}!",
        "theme": "fiesta",
        "steps": [
            {
                "title": "1. Help 5 Barrio Craftspeople:",
                "bullets": [
                    "Solve math challenges on Fractions, Division, Shapes, Time, and Garden Perimeters.",
                    "Hold a CLOSED FIST to accept each building challenge."
                ]
            },
            {
                "title": "2. Progressively Construct the Bahay Kubo:",
                "bullets": [
                    "Each correct answer raises bamboo stilts, walls, nipa roof, and ladder!"
                ]
            },
            {
                "title": "3. Enter the Goal Portal once the Bahay Kubo is complete!",
                "bullets": []
            }
        ]
    },
    "map6.txt": {
        "title": "THE GRAND FIESTA CELEBRATION",
        "subtitle": "It's Fiesta Day, {player_name}!",
        "theme": "fiesta",
        "steps": [
            {
                "title": "1. Complete the 5 Plaza Celebration Stations:",
                "bullets": [
                    "Help the fiesta committee with band schedules, food portions, game prizes, and banner lengths!"
                ]
            },
            {
                "title": "2. Unlock the Golden Portal to the Monetary Desert (Quarter 3)!",
                "bullets": []
            }
        ]
    },
    "quarter3": {
        "title": "THE MONETARY DESERT EXPEDITION",
        "subtitle": "Welcome to the golden sands, {player_name}!",
        "theme": "desert",
        "steps": [
            {
                "title": "1. Explore the Ancient Desert Ruins:",
                "bullets": [
                    "Find the 5 Desert Sages guarding the golden currency stations.",
                    "Hold a CLOSED FIST to decode ancient trade tablets."
                ]
            },
            {
                "title": "2. Solve Multi-Step Money & Currency Problems:",
                "bullets": [
                    "Add and subtract Philippine Peso bills and coins!"
                ]
            },
            {
                "title": "3. Unlock the Pharaoh's Golden Vault to reach Quarter 4!",
                "bullets": []
            }
        ]
    },
    "quarter4": {
        "title": "THE WATER TEMPLE SANCTUARY",
        "subtitle": "Dive deep into the sunken sanctum, {player_name}!",
        "theme": "water",
        "steps": [
            {
                "title": "1. Locate the Water Temple Guardians:",
                "bullets": [
                    "Find each guardian stationed along the submerged aqueducts.",
                    "Hold a CLOSED FIST to solve advanced grade-level challenges."
                ]
            },
            {
                "title": "2. Collect the Golden Keys:",
                "bullets": [
                    "Watch each key fly into your Objectives HUD upon success!"
                ]
            },
            {
                "title": "3. Activate the Lotus Raft & Floodgate Controls:",
                "bullets": [
                    "Unlock the Master Temple Sanctum to complete Cognitive Quest!"
                ]
            }
        ]
    },
    "map10.txt": {
        "title": "THE WATER TEMPLE SANCTUARY - THE TEMPLE AQUEDUCT",
        "subtitle": "Dive into the outer sanctuary, {player_name}!",
        "theme": "water",
        "steps": [
            {
                "title": "1. Locate the 6 Water Guardians:",
                "bullets": [
                    "Explore the submerged channels to locate all 6 guardians.",
                    "Hold a CLOSED FIST to accept each mathematical test."
                ]
            },
            {
                "title": "2. Collect All 6 Golden Keys:",
                "bullets": [
                    "Each correct solution awards a glowing Golden Key."
                ]
            },
            {
                "title": "3. Unlock the Ancient Key Box:",
                "bullets": [
                    "Consult the Temple Elder to solve the Key Lock Box Puzzle!"
                ]
            },
            {
                "title": "4. Enter the Goal Portal to advance to Map 11!",
                "bullets": []
            }
        ]
    },
    "map11.txt": {
        "title": "THE SUBMERGED KEY VAULT",
        "subtitle": "The currents run deep, {player_name}!",
        "theme": "water",
        "steps": [
            {
                "title": "1. Search the Submerged Chambers:",
                "bullets": [
                    "Find all 6 guardians stationed behind the temple barricades.",
                    "Hold a CLOSED FIST to decode each water puzzle."
                ]
            },
            {
                "title": "2. Collect 6 Golden Keys:",
                "bullets": [
                    "Gather all 6 keys to unlock the inner sanctum doors."
                ]
            },
            {
                "title": "3. Unlock the Master Double Doors:",
                "bullets": [
                    "Fit each key into its lock slot to swing open the heavy doors!"
                ]
            },
            {
                "title": "4. Step Through the Golden Portal into Map 12!",
                "bullets": []
            }
        ]
    },
    "map12.txt": {
        "title": "THE LOTUS RAFT & FINAL SANCTUM",
        "subtitle": "Master the rapids of the Great Floodgate, {player_name}!",
        "theme": "water",
        "steps": [
            {
                "title": "1. Open All 6 Aqueduct Sluices:",
                "bullets": [
                    "Challenge the 6 guardians guarding the canal valves.",
                    "Correct answers fill the canal rapids with rushing water!"
                ]
            },
            {
                "title": "2. Solve the Helm Addition Equation:",
                "bullets": [
                    "Speak with Guardian Bromen and arrange the scattered runes into a balanced addition equation."
                ]
            },
            {
                "title": "3. Ride the Lotus Raft Cruise:",
                "bullets": [
                    "Hop aboard the Lotus Raft to sail across the rapids to the East Pier."
                ]
            },
            {
                "title": "4. Enter the Grand Master Portal to complete Cognitive Quest!",
                "bullets": []
            }
        ]
    }
}


STATION_SCRIPTS_DATA = {
    # ----------------------------------------------------
    # QUARTER 1: GEOMETRY FOREST
    # ----------------------------------------------------
    ("quarter1", "map1.txt", 1): {
        "name": "Circle Guardian",
        "role": "Station 1 - Geometry Forest",
        "greeting": "Greetings, little explorer! I am the Circle Guardian. I roll with joy because I have no pointy corners! Are you ready for my shape challenge? Hold a Closed Fist to begin!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "The correct answer was displayed above! Keep practicing and your mind will grow stronger. Here is your first bridge plank!",
        "correct_praise": "Amazing! That is correct! One bridge plank has appeared over the river!"
    },
    ("quarter1", "map1.txt", 2): {
        "name": "Heart Guardian",
        "role": "Station 2 - Geometry Forest",
        "greeting": "Hello, bright student! My heart beats with excitement. Let's see if you can divide shapes equally. Hold a Closed Fist to see your challenge!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good effort! Take this bridge plank for your hard work!",
        "correct_praise": "That's great! Another bridge plank just floated into place over the river!"
    },
    ("quarter1", "map1.txt", 3): {
        "name": "Square Guardian",
        "role": "Station 3 - Geometry Forest",
        "greeting": "Stand tall, student! I am the Square Guardian. All four of my sides are equal and strong. Hold a Closed Fist to test your shape building knowledge!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good try! Here is your third bridge plank!",
        "correct_praise": "Splendid! The third bridge plank is now securely placed across the stream!"
    },
    ("quarter1", "map1.txt", 4): {
        "name": "Star Guardian",
        "role": "Station 4 - Geometry Forest",
        "greeting": "Twinkle, twinkle, young adventurer! I shine bright high in the sky. When shapes glide, they follow mathematical rules. Hold a Closed Fist to begin!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "You will get it better next time! Keep going—here is your fourth bridge plank!",
        "correct_praise": "You're good at this! Only one bridge plank left before the river can be crossed!"
    },
    ("quarter1", "map1.txt", 5): {
        "name": "Diamond Guardian",
        "role": "Station 5 - Geometry Forest",
        "greeting": "Welcome to the final station, champion! I sparkle with sharp angles. Hold a Closed Fist to take on my composite figure challenge!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "You did your best! The fifth bridge plank is now laid. Cross over to meet the Old Man!",
        "correct_praise": "Brilliant! The bridge across the river is now fully built! Cross over and speak to the Old Man!"
    },

    # Map 2: Shape Vault (Stations 1-5)
    ("quarter1", "map2.txt", 1): {
        "name": "Square Guardian",
        "role": "Shape Vault Station 1",
        "greeting": "Greetings, {player_name}! The Shape Vault requires our sacred shape tokens. Prove your shape mastery! Hold a Closed Fist to reveal your question!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! Take this Shape Token so your quest can continue!",
        "correct_praise": "Spot on! Take this glowing Shape Token to the Old Man's altar!"
    },
    ("quarter1", "map2.txt", 2): {
        "name": "Diamond Guardian",
        "role": "Shape Vault Station 2",
        "greeting": "Greetings, {player_name}! The Shape Vault requires our sacred shape tokens. Prove your shape mastery! Hold a Closed Fist to reveal your question!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! Take this Shape Token so your quest can continue!",
        "correct_praise": "Spot on! Take this glowing Shape Token to the Old Man's altar!"
    },
    ("quarter1", "map2.txt", 3): {
        "name": "Heart Guardian",
        "role": "Shape Vault Station 3",
        "greeting": "Greetings, {player_name}! The Shape Vault requires our sacred shape tokens. Prove your shape mastery! Hold a Closed Fist to reveal your question!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! Take this Shape Token so your quest can continue!",
        "correct_praise": "Spot on! Take this glowing Shape Token to the Old Man's altar!"
    },
    ("quarter1", "map2.txt", 4): {
        "name": "Circle Guardian",
        "role": "Shape Vault Station 4",
        "greeting": "Greetings, {player_name}! The Shape Vault requires our sacred shape tokens. Prove your shape mastery! Hold a Closed Fist to reveal your question!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! Take this Shape Token so your quest can continue!",
        "correct_praise": "Spot on! Take this glowing Shape Token to the Old Man's altar!"
    },
    ("quarter1", "map2.txt", 5): {
        "name": "Star Guardian",
        "role": "Shape Vault Station 5",
        "greeting": "Greetings, {player_name}! The Shape Vault requires our sacred shape tokens. Prove your shape mastery! Hold a Closed Fist to reveal your question!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! Take this Shape Token so your quest can continue!",
        "correct_praise": "Spot on! Take this glowing Shape Token to the Old Man's altar!"
    },

    # Map 3: Ancient Mosaic (Stations 1-5)
    ("quarter1", "map3.txt", 1): {
        "name": "Shape Guardian",
        "role": "Ancient Mosaic Station 1",
        "greeting": "You've reached the depths of the forest! The ancient guardian painting has been scattered. Hold a Closed Fist to earn a mosaic slice!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good try! Take this jigsaw slice to help restore the ancient painting!",
        "correct_praise": "Fantastic! Here is your interlocking jigsaw piece. Bring it to the Old Man!"
    },
    ("quarter1", "map3.txt", 2): {
        "name": "Shape Guardian",
        "role": "Ancient Mosaic Station 2",
        "greeting": "You've reached the depths of the forest! The ancient guardian painting has been scattered. Hold a Closed Fist to earn a mosaic slice!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good try! Take this jigsaw slice to help restore the ancient painting!",
        "correct_praise": "Fantastic! Here is your interlocking jigsaw piece. Bring it to the Old Man!"
    },
    ("quarter1", "map3.txt", 3): {
        "name": "Shape Guardian",
        "role": "Ancient Mosaic Station 3",
        "greeting": "You've reached the depths of the forest! The ancient guardian painting has been scattered. Hold a Closed Fist to earn a mosaic slice!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good try! Take this jigsaw slice to help restore the ancient painting!",
        "correct_praise": "Fantastic! Here is your interlocking jigsaw piece. Bring it to the Old Man!"
    },
    ("quarter1", "map3.txt", 4): {
        "name": "Shape Guardian",
        "role": "Ancient Mosaic Station 4",
        "greeting": "You've reached the depths of the forest! The ancient guardian painting has been scattered. Hold a Closed Fist to earn a mosaic slice!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good try! Take this jigsaw slice to help restore the ancient painting!",
        "correct_praise": "Fantastic! Here is your interlocking jigsaw piece. Bring it to the Old Man!"
    },
    ("quarter1", "map3.txt", 5): {
        "name": "Shape Guardian",
        "role": "Ancient Mosaic Station 5",
        "greeting": "You've reached the depths of the forest! The ancient guardian painting has been scattered. Hold a Closed Fist to earn a mosaic slice!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good try! Take this jigsaw slice to help restore the ancient painting!",
        "correct_praise": "Fantastic! Here is your interlocking jigsaw piece. Bring it to the Old Man!"
    },

    # ----------------------------------------------------
    # QUARTER 2: BARANGAY KALYE / BARRIOS' FIESTA
    # ----------------------------------------------------
    # Map 4: The Festive Street Market
    ("quarter2", "map4.txt", 1): {
        "name": "Aling Nena (Sari-Sari Store)",
        "role": "Barrio Merchant - Station 1",
        "greeting": "Mabuhay, little suki! Welcome to my Sari-Sari store. Can you help me compute? Hold a Closed Fist to get your question!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort, little suki! Take your market stamp so you can keep going!",
        "correct_praise": "Salamat! Ang galing mo naman!"
    },
    ("quarter2", "map4.txt", 2): {
        "name": "Mang Pedring (Sorbetes Cart)",
        "role": "Barrio Merchant - Station 2",
        "greeting": "Ting-ting-ting! Delicious Sorbetes! Hold a Closed Fist to help me!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good try! Here is your sorbetes stamp for your hard effort!",
        "correct_praise": "Super! Here is a sweet scoop of math success!"
    },
    ("quarter2", "map4.txt", 3): {
        "name": "Kuya Jomar (Jeepney Terminal)",
        "role": "Barrio Merchant - Station 3",
        "greeting": "Barya lang po sa umaga! We are ready to roll down the highway. Hold a Closed Fist to help me calculate!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "You'll get it next trip! Here is your jeepney terminal stamp!",
        "correct_praise": "Ayos! Next stop: Math Mastery!"
    },
    ("quarter2", "map4.txt", 4): {
        "name": "Ate Maria (Market Fruit Stand)",
        "role": "Barrio Merchant - Station 4",
        "greeting": "Fresh sweet mangoes from Guimaras! Hold a Closed Fist to calculate!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good effort! Take your market fruit stamp and keep moving forward!",
        "correct_praise": "Tumpak! Perfectly balanced!"
    },
    ("quarter2", "map4.txt", 5): {
        "name": "Mang Carding (Parol Workshop)",
        "role": "Barrio Merchant - Station 5",
        "greeting": "Maligayang Fiesta! We are crafting colorful bamboo Parols for the street lamps. Hold a Closed Fist to help me!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good try! Here is your final market stamp to complete your card!",
        "correct_praise": "Mabuhay! Our budget is balanced and the street lanterns shine bright!"
    },

    # Map 5: Bahay Kubo Construction
    ("quarter2", "map5.txt", 1): {
        "name": "Craftsman (Bamboo Posts)",
        "role": "Bahay Kubo Builder - Station 1",
        "greeting": "Bayanihan in action! We are building a traditional Bahay Kubo together. Hold a Closed Fist to help us build!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! The community continues to build together. Here is your construction piece!",
        "correct_praise": "Bayanihan victory! Look at the Bahay Kubo—another section has been built into place!"
    },
    ("quarter2", "map5.txt", 2): {
        "name": "Craftsman (Sawali Walls)",
        "role": "Bahay Kubo Builder - Station 2",
        "greeting": "Bayanihan in action! We are building a traditional Bahay Kubo together. Hold a Closed Fist to help us build!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! The community continues to build together. Here is your construction piece!",
        "correct_praise": "Bayanihan victory! Look at the Bahay Kubo—another section has been built into place!"
    },
    ("quarter2", "map5.txt", 3): {
        "name": "Craftsman (Windows & Door)",
        "role": "Bahay Kubo Builder - Station 3",
        "greeting": "Bayanihan in action! We are building a traditional Bahay Kubo together. Hold a Closed Fist to help us build!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! The community continues to build together. Here is your construction piece!",
        "correct_praise": "Bayanihan victory! Look at the Bahay Kubo—another section has been built into place!"
    },
    ("quarter2", "map5.txt", 4): {
        "name": "Craftsman (Nipa Roof)",
        "role": "Bahay Kubo Builder - Station 4",
        "greeting": "Bayanihan in action! We are building a traditional Bahay Kubo together. Hold a Closed Fist to help us build!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! The community continues to build together. Here is your construction piece!",
        "correct_praise": "Bayanihan victory! Look at the Bahay Kubo—another section has been built into place!"
    },
    ("quarter2", "map5.txt", 5): {
        "name": "Craftsman (Bamboo Ladder)",
        "role": "Bahay Kubo Builder - Station 5",
        "greeting": "Bayanihan in action! We are building a traditional Bahay Kubo together. Hold a Closed Fist to help us build!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "Good effort! The community continues to build together. Here is your construction piece!",
        "correct_praise": "Bayanihan victory! Look at the Bahay Kubo—another section has been built into place!"
    },

    # Map 6: Grand Fiesta Plaza
    ("quarter2", "map6.txt", 1): {
        "name": "Committee Member",
        "role": "Fiesta Committee - Station 1",
        "greeting": "Maligayang Fiesta! The plaza games and celebrations need our help! Hold a Closed Fist to help us prepare!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good effort! Take this fiesta ribbon so the celebration continues!",
        "correct_praise": "Viva! Everything is organized to perfection! The crowd cheers!"
    },
    ("quarter2", "map6.txt", 2): {
        "name": "Committee Member",
        "role": "Fiesta Committee - Station 2",
        "greeting": "Maligayang Fiesta! The plaza games and celebrations need our help! Hold a Closed Fist to help us prepare!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good effort! Take this fiesta ribbon so the celebration continues!",
        "correct_praise": "Viva! Everything is organized to perfection! The crowd cheers!"
    },
    ("quarter2", "map6.txt", 3): {
        "name": "Committee Member",
        "role": "Fiesta Committee - Station 3",
        "greeting": "Maligayang Fiesta! The plaza games and celebrations need our help! Hold a Closed Fist to help us prepare!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good effort! Take this fiesta ribbon so the celebration continues!",
        "correct_praise": "Viva! Everything is organized to perfection! The crowd cheers!"
    },
    ("quarter2", "map6.txt", 4): {
        "name": "Committee Member",
        "role": "Fiesta Committee - Station 4",
        "greeting": "Maligayang Fiesta! The plaza games and celebrations need our help! Hold a Closed Fist to help us prepare!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good effort! Take this fiesta ribbon so the celebration continues!",
        "correct_praise": "Viva! Everything is organized to perfection! The crowd cheers!"
    },
    ("quarter2", "map6.txt", 5): {
        "name": "Committee Member",
        "role": "Fiesta Committee - Station 5",
        "greeting": "Maligayang Fiesta! The plaza games and celebrations need our help! Hold a Closed Fist to help us prepare!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "Good effort! Take this fiesta ribbon so the celebration continues!",
        "correct_praise": "Viva! Everything is organized to perfection! The crowd cheers!"
    },

    # ----------------------------------------------------
    # QUARTER 3: MONETARY DESERT & ANCIENT RUINS (Maps 7, 8, 9)
    # ----------------------------------------------------
    ("quarter3", "*", 1): {
        "name": "Desert Sage",
        "role": "Desert Sage - Station 1",
        "greeting": "Traveler of the sands! Ancient treasures belong only to those who seek knowledge. Hold a Closed Fist to consult the desert trade tablet!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "The desert winds teach patience. Take this trade seal and press forward!",
        "correct_praise": "Wise and true! The golden sands resonate with your accurate calculation. Take this desert seal!"
    },
    ("quarter3", "*", 2): {
        "name": "Desert Sage",
        "role": "Desert Sage - Station 2",
        "greeting": "Traveler of the sands! Ancient treasures belong only to those who seek knowledge. Hold a Closed Fist to consult the desert trade tablet!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "The desert winds teach patience. Take this trade seal and press forward!",
        "correct_praise": "Wise and true! The golden sands resonate with your accurate calculation. Take this desert seal!"
    },
    ("quarter3", "*", 3): {
        "name": "Desert Sage",
        "role": "Desert Sage - Station 3",
        "greeting": "Traveler of the sands! Ancient treasures belong only to those who seek knowledge. Hold a Closed Fist to consult the desert trade tablet!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "The desert winds teach patience. Take this trade seal and press forward!",
        "correct_praise": "Wise and true! The golden sands resonate with your accurate calculation. Take this desert seal!"
    },
    ("quarter3", "*", 4): {
        "name": "Desert Sage",
        "role": "Desert Sage - Station 4",
        "greeting": "Traveler of the sands! Ancient treasures belong only to those who seek knowledge. Hold a Closed Fist to consult the desert trade tablet!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "The desert winds teach patience. Take this trade seal and press forward!",
        "correct_praise": "Wise and true! The golden sands resonate with your accurate calculation. Take this desert seal!"
    },
    ("quarter3", "*", 5): {
        "name": "Desert Sage",
        "role": "Desert Sage - Station 5",
        "greeting": "Traveler of the sands! Ancient treasures belong only to those who seek knowledge. Hold a Closed Fist to consult the desert trade tablet!",
        "wrong_retry": "Hmm, not quite! Try again.",
        "out_of_tries": "The desert winds teach patience. Take this trade seal and press forward!",
        "correct_praise": "Wise and true! The golden sands resonate with your accurate calculation. Take this desert seal!"
    },

    # ----------------------------------------------------
    # QUARTER 4: UNDERWATER DUNGEON & WATER TEMPLE (Maps 10, 11, 12)
    # ----------------------------------------------------
    ("quarter4", "*", 1): {
        "name": "Water Guardian",
        "role": "Water Temple - Station 1",
        "greeting": "Greetings, seeker of the deep! The clear waters flow according to perfect mathematical harmony. Hold a Closed Fist to channel your logical power!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "The ocean rewards perseverance. Here is your Golden Key so your quest can proceed!",
        "correct_praise": "Splendid! The waters shine bright! A Golden Key flies into your Objectives HUD!"
    },
    ("quarter4", "*", 2): {
        "name": "Water Guardian",
        "role": "Water Temple - Station 2",
        "greeting": "Greetings, seeker of the deep! The clear waters flow according to perfect mathematical harmony. Hold a Closed Fist to channel your logical power!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "The ocean rewards perseverance. Here is your Golden Key so your quest can proceed!",
        "correct_praise": "Splendid! The waters shine bright! A Golden Key flies into your Objectives HUD!"
    },
    ("quarter4", "*", 3): {
        "name": "Water Guardian",
        "role": "Water Temple - Station 3",
        "greeting": "Greetings, seeker of the deep! The clear waters flow according to perfect mathematical harmony. Hold a Closed Fist to channel your logical power!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "The ocean rewards perseverance. Here is your Golden Key so your quest can proceed!",
        "correct_praise": "Splendid! The waters shine bright! A Golden Key flies into your Objectives HUD!"
    },
    ("quarter4", "*", 4): {
        "name": "Water Guardian",
        "role": "Water Temple - Station 4",
        "greeting": "Greetings, seeker of the deep! The clear waters flow according to perfect mathematical harmony. Hold a Closed Fist to channel your logical power!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "The ocean rewards perseverance. Here is your Golden Key so your quest can proceed!",
        "correct_praise": "Splendid! The waters shine bright! A Golden Key flies into your Objectives HUD!"
    },
    ("quarter4", "*", 5): {
        "name": "Water Guardian",
        "role": "Water Temple - Station 5",
        "greeting": "Greetings, seeker of the deep! The clear waters flow according to perfect mathematical harmony. Hold a Closed Fist to channel your logical power!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "The ocean rewards perseverance. Here is your Golden Key so your quest can proceed!",
        "correct_praise": "Splendid! The waters shine bright! A Golden Key flies into your Objectives HUD!"
    },
    ("quarter4", "*", 6): {
        "name": "Water Guardian",
        "role": "Water Temple - Station 6",
        "greeting": "Greetings, seeker of the deep! The clear waters flow according to perfect mathematical harmony. Hold a Closed Fist to channel your logical power!",
        "wrong_retry": "Think carefully! Try again.",
        "out_of_tries": "The ocean rewards perseverance. Here is your Golden Key so your quest can proceed!",
        "correct_praise": "Splendid! The waters shine bright! A Golden Key flies into your Objectives HUD!"
    }
}


MENTOR_SCRIPTS_DATA = {
    # Quarter 1
    ("quarter1", "map1.txt"): {
        "name": "Old Man",
        "role": "Forest Mentor",
        "incomplete": "Halt, young traveler! Beyond this point lies the portal.\nBut to pass, you must build the bridge first and answer my riddle!\nGo back and solve the shape puzzles in the forest.",
        "complete": "Ah! You have crossed the Bridge of Shapes! But before the portal opens, you must prove your wisdom. Hear my riddle:",
        "wrong_riddle": "That is incorrect, young adventurer! Think carefully and try again.",
        "correct_riddle": "Outstanding, young adventurer! You have built the bridge and solved my riddle!\nYou may now enter the portal and proceed on your quest. Safe travels!"
    },
    ("quarter1", "map2.txt"): {
        "name": "Old Man",
        "role": "Altar Guardian",
        "incomplete": "Halt, young traveler! The altar remains dormant.\nYou must seek out all 5 Shape Guardians in this chamber\nand collect their shape tokens before the vault will respond!",
        "complete": "Marvelous work, {player_name}! You have gathered all 5 shape tokens: Square, Diamond, Heart, Circle, and Star.\nNow, place each shape token into its matching sacred outline on the altar to unlock the path!",
        "solved": "Well done! Every shape rests in its rightful home. The portal is open—step forward!"
    },
    ("quarter1", "map3.txt"): {
        "name": "Old Man",
        "role": "Grand Altar Mentor",
        "incomplete": "Halt, young traveler! Beyond this point lies the master portal.\nGather all 5 jigsaw puzzle pieces first and solve my puzzle!",
        "complete": "Excellent work gathering the puzzle pieces, {player_name}!\nNow you must solve the jigsaw puzzle using what you got.\nFit the interlocking edges together to reveal the ancient guardian portrait.\nAre you ready?",
        "solved": "Outstanding, young adventurer {player_name}! You have restored the portrait with mathematical precision!\nThe Geometry Forest is peaceful once again.\nThe gates to Quarter 2: Barangay Kalye are now open!\nOnward to your next adventure!"
    },

    # Quarter 2
    ("quarter2", "map4.txt"): {
        "name": "Barrio Leader",
        "role": "Barangay Gatekeeper",
        "incomplete": "Welcome to our barangay, young student!\nBefore we open the gate to the inner barrio, please help all 5 vendors in the street market!",
        "complete": "Magaling! You have brought harmony and quick counting to our whole street market!\nThe road to the Barrio Garden and Bahay Kubo is open. Tuloy po kayo!"
    },
    ("quarter2", "map5.txt"): {
        "name": "Master Carpenter",
        "role": "Bahay Kubo Altar",
        "incomplete": "Keep going, young builder! We need all 5 building sections completed before we can celebrate!",
        "complete": "Magnificent! The Bahay Kubo stands proud and strong, built by your mathematical teamwork!\nThe road to the Grand Plaza is open!"
    },
    ("quarter2", "map6.txt"): {
        "name": "Hermano Mayor",
        "role": "Fiesta Grand Stage",
        "incomplete": "Welcome, guest of honor! Help all 5 plaza stations so the fiesta can reach its peak!",
        "complete": "Mabuhay ang Fiesta! You have brought joy, fairness, and mathematical brilliance to our whole town!\nThe golden portal to Quarter 3: Monetary Desert is now open!"
    },

    # Quarter 3
    ("quarter3", "*"): {
        "name": "Desert Vault Keeper",
        "role": "Pharaoh's Vault Altar",
        "incomplete": "Halt, traveler! The Pharaoh's treasury remains locked. Gather all 5 trade seals from the desert sages!",
        "complete": "You have braved the shifting dunes and mastered the ancient tests!\nThe sacred vault unlocks, revealing the shimmering waterway to the Water Temple!\nProceed, champion!"
    },

    # Quarter 4
    ("quarter4", "*"): {
        "name": "Temple Elder",
        "role": "Master Floodgate Altar",
        "incomplete": "Halt, brave diver! The master floodgate remains sealed.\nCollect all 5 Golden Keys from the Water Guardians to calm the currents!",
        "complete": "Incredible, {player_name}! All 5 Golden Keys are in place!\nThe aqueducts align, the lotus raft glides forward, and the grand sanctuary is unlocked!\nYou have mastered mathematics from the tallest forest trees to the deepest ocean temples!"
    }
}


def _infer_quarter_and_map(arg1, arg2=None):
    """Internal helper to deduce quarter_key and map_name from flexible arguments."""
    a1 = str(arg1).strip().lower() if arg1 else ""
    a2 = str(arg2).strip().lower() if arg2 else ""

    # Check if a1 is already quarter key
    if a1.startswith("quarter") and (a2.endswith(".txt") or a2 in ["*", ""]):
        return a1, a2 or "*"

    # Map filename to quarter
    map_to_quarter = {
        "map1.txt": "quarter1", "map2.txt": "quarter1", "map3.txt": "quarter1",
        "map4.txt": "quarter2", "map5.txt": "quarter2", "map6.txt": "quarter2",
        "map7.txt": "quarter3", "map8.txt": "quarter3", "map9.txt": "quarter3",
        "map10.txt": "quarter4", "map11.txt": "quarter4", "map12.txt": "quarter4"
    }

    if a1 in map_to_quarter:
        return map_to_quarter[a1], a1
    if a2 in map_to_quarter:
        return map_to_quarter[a2], a2
    if a1.endswith(".txt"):
        return "quarter1", a1
    if a1.startswith("quarter"):
        return a1, "*"
    return "quarter1", a1 or "*"


def get_map_instructions(arg1, arg2=None, arg3="Student"):
    """
    Returns the instructions dict for the specified map or quarter, with {player_name} formatted.
    Supports get_map_instructions(map_name, player_name) or
    get_map_instructions(quarter_key, map_name, player_name).
    """
    if arg2 is not None and not str(arg2).lower().endswith(".txt") and not str(arg2).lower().startswith("map"):
        # Called as (map_name, player_name)
        m_key = str(arg1).lower()
        p_name = str(arg2) if arg2 else "Student"
        quarter_key, _ = _infer_quarter_and_map(m_key)
    else:
        # Called as (quarter_key, map_name, player_name)
        quarter_key = str(arg1).lower() if arg1 else "quarter1"
        m_key = str(arg2).lower() if arg2 else ""
        p_name = str(arg3) if arg3 else "Student"

    info = MAP_INSTRUCTIONS_DATA.get(m_key)
    if not info:
        info = MAP_INSTRUCTIONS_DATA.get(quarter_key)
    if not info:
        info = {
            "title": "QUEST OBJECTIVES",
            "subtitle": f"Welcome, {p_name}!",
            "theme": "forest",
            "steps": [
                {
                    "title": "1. Solve Station Challenges:",
                    "bullets": ["Approach each station and hold a closed fist to answer questions."]
                },
                {
                    "title": "2. Unlock the Goal Portal:",
                    "bullets": ["Complete all 5 stations to advance."]
                }
            ]
        }
        return info

    formatted = {
        "title": info["title"],
        "subtitle": info["subtitle"].format(player_name=p_name),
        "theme": info.get("theme", "forest"),
        "steps": []
    }
    for step in info["steps"]:
        formatted["steps"].append({
            "title": step["title"],
            "bullets": list(step["bullets"])
        })
    return formatted


def get_station_script(arg1, arg2, arg3=None, arg4="Student"):
    """
    Returns the station NPC script dict with complete key aliases.
    Supports:
      get_station_script(map_name, station_index, player_name="Student")
      get_station_script(quarter_key, map_name, station_index, player_name="Student")
    """
    if isinstance(arg2, int) or (isinstance(arg2, str) and arg2.isdigit()):
        # Called as (map_name, station_index, [player_name])
        m_key = str(arg1).lower()
        station_index = int(arg2)
        p_name = str(arg3) if arg3 else "Student"
        q_key, _ = _infer_quarter_and_map(m_key)
    else:
        # Called as (quarter_key, map_name, station_index, [player_name])
        q_key = str(arg1).lower()
        m_key = str(arg2).lower()
        station_index = int(arg3) if (arg3 is not None and str(arg3).isdigit()) else 1
        p_name = str(arg4) if arg4 else "Student"

    # Specific map match
    script = STATION_SCRIPTS_DATA.get((q_key, m_key, station_index))
    if not script:
        # Wildcard map match
        script = STATION_SCRIPTS_DATA.get((q_key, "*", station_index))

    if not script:
        script = {
            "name": f"Station {station_index} Guardian",
            "role": f"Quest Station {station_index}",
            "greeting": f"Greetings, {p_name}! Hold a Closed Fist to take on my challenge!",
            "wrong_retry": "Hmm, not quite! Try again.",
            "out_of_tries": "Good effort! Take this quest item so you can continue!",
            "correct_praise": "Outstanding! That is correct!"
        }

    # Item awarded by quarter and station
    items_by_quarter = {
        "quarter1": {1: "Triangle Token", 2: "Square Token", 3: "Star Token", 4: "Circle Token", 5: "Diamond Token"},
        "quarter2": {1: "Fresh Barrio Fish", 2: "Pure Coconut Milk", 3: "Jeepney Fare Ticket", 4: "Sweet Guimaras Mangoes", 5: "Fiesta Bamboo Parol"},
        "quarter3": {1: "Solar Cargo Supplies", 2: "Oasis Sunstone", 3: "Desert Vault Keystone", 4: "Golden Altar Rune", 5: "Sun Keystone"},
        "quarter4": {1: "Golden Key of Tides", 2: "Coral Conch Key", 3: "Neptune's Water Gear", 4: "Aqueduct Sluice Rune", 5: "Chrono Lotus Key", 6: "Master Sanctum Key"}
    }
    awarded_item = items_by_quarter.get(q_key, {}).get(station_index, "Progression Item")

    greeting_str = script["greeting"].format(player_name=p_name)
    retry_str = script["wrong_retry"].format(player_name=p_name)
    reveal_str = script["out_of_tries"].format(player_name=p_name)
    praise_str = script["correct_praise"].format(player_name=p_name)

    return {
        "name": script["name"],
        "npc_name": script["name"],
        "role": script["role"],
        "npc_title": script["role"],
        "greeting": greeting_str,
        "wrong_retry": retry_str,
        "retry_line": retry_str,
        "out_of_tries": reveal_str,
        "out_of_tries_line": reveal_str,
        "correct_praise": praise_str,
        "praise_line": praise_str,
        "item_awarded": awarded_item
    }


def get_mentor_script(arg1, arg2=None, arg3="Student"):
    """
    Returns mentor dialogue data for exit / altar NPCs with complete key aliases.
    Supports:
      get_mentor_script(map_name, player_name="Student")
      get_mentor_script(quarter_key, map_name, player_name="Student")
    """
    if arg2 is not None and not str(arg2).lower().endswith(".txt") and not str(arg2).lower().startswith("map"):
        # Called as (map_name, player_name)
        m_key = str(arg1).lower()
        p_name = str(arg2) if arg2 else "Student"
        q_key, _ = _infer_quarter_and_map(m_key)
    else:
        # Called as (quarter_key, map_name, player_name)
        q_key = str(arg1).lower() if arg1 else "quarter1"
        m_key = str(arg2).lower() if arg2 else ""
        p_name = str(arg3) if arg3 else "Student"

    mentor = MENTOR_SCRIPTS_DATA.get((q_key, m_key))
    if not mentor:
        mentor = MENTOR_SCRIPTS_DATA.get((q_key, "*"))

    if not mentor:
        mentor = {
            "name": "Stage Mentor",
            "role": "Quarter Guardian",
            "incomplete": "Complete all 5 station challenges before passing through the portal!",
            "complete": f"Well done, {p_name}! You have mastered all challenges! Step into the portal!"
        }

    inc_str = mentor["incomplete"].format(player_name=p_name)
    comp_str = mentor["complete"].format(player_name=p_name)

    res = {
        "name": mentor["name"],
        "mentor_name": mentor["name"],
        "role": mentor["role"],
        "mentor_title": mentor["role"],
        "incomplete": inc_str,
        "incomplete_dialogue": inc_str,
        "complete": comp_str,
        "complete_dialogue": comp_str
    }
    if "wrong_riddle" in mentor:
        res["wrong_riddle"] = mentor["wrong_riddle"].format(player_name=p_name)
    if "correct_riddle" in mentor:
        res["correct_riddle"] = mentor["correct_riddle"].format(player_name=p_name)
    if "solved" in mentor:
        res["solved"] = mentor["solved"].format(player_name=p_name)
    return res
