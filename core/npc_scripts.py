# core/npc_scripts.py
"""
Master NPC Dialogue & Script Reference Data for Cognitive Quest 2D.
Covers All Quarters (1 to 4) & All Maps (1 to 12) + Stage Select Hub.
Corresponds directly to docs/GAME_NPC_SCRIPTS_ALL_QUARTERS.md.
"""

MAP_INSTRUCTIONS_DATA = {
    # ====================================================
    # QUARTER 1: GEOMETRY FOREST & SHAPES (Maps 1, 2, 3)
    # ====================================================
    "quarter1": {
        "title": "QUARTER 1: GEOMETRY FOREST",
        "subtitle": "Welcome to the magical Forest of Shapes, {player_name}!",
        "theme": "forest",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Identify and name 2D geometric shapes (Circle, Triangle, Square, Rectangle, Star, Diamond, and Heart).",
            "Describe shape characteristics including the number of sides, straight lines, curved edges, and corners (vertices).",
            "Solve geometry riddles and visual-spatial jigsaw puzzles using shape properties."
        ],
        "steps": [
            {
                "title": "1. Find the 5 Shape Guardians:",
                "bullets": [
                    "Explore the forest trails and approach each guardian station.",
                    "Hold a CLOSED FIST (or Click) to answer geometry questions."
                ]
            },
            {
                "title": "2. Collect Shape Tokens & Solve Altar Puzzles:",
                "bullets": [
                    "Each correct answer earns building planks, tokens, or jigsaw pieces!"
                ]
            },
            {
                "title": "3. Enter the Goal Portal to advance to the next map!",
                "bullets": []
            }
        ]
    },
    "map1.txt": {
        "title": "QUARTER 1: GEOMETRY FOREST - RIVER CROSSING",
        "subtitle": "Hello, {player_name}! The magical river has no crossing!",
        "theme": "forest",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Name 2D shapes and count their sides, straight lines, and corners/vertices.",
            "Differentiate shapes with straight sides (triangles, squares) from curved shapes (circles, hearts).",
            "Solve the Forest Mentor's shape riddle using logical deduction."
        ],
        "steps": [
            {
                "title": "1. Answer 5 Geometry Questions & Build the Bridge:",
                "bullets": [
                    "Find all 5 Shape Guardians hidden in the forest.",
                    "Approach each guardian and HOLD A CLOSED FIST (or Click) to view the question.",
                    "Each correct answer constructs 1 wooden plank across the river!"
                ]
            },
            {
                "title": "2. Cross the Bridge to the Old Man:",
                "bullets": [
                    "Once all 5 planks are laid, cross the water safely to meet the Forest Mentor."
                ]
            },
            {
                "title": "3. Solve the Old Man's Shape Riddle:",
                "bullets": [
                    "Speak to the Old Man and select the shape that solves his riddle!"
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
        "title": "QUARTER 1: THE SHAPE VAULT OF GEOMETRY",
        "subtitle": "Welcome back, {player_name}! You are deeper in the forest!",
        "theme": "forest",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Identify specific geometric properties of Triangles, Squares, Diamonds, Stars, and Circles.",
            "Apply visual matching by placing geometric tokens into their matching altar silhouette slots.",
            "Recognize 2D shape characteristics in different orientations and sizes."
        ],
        "steps": [
            {
                "title": "1. Find the 5 Shape Guardians:",
                "bullets": [
                    "Explore the winding trails to locate all 5 stations.",
                    "Hold a CLOSED FIST (or Click) to answer their shape questions."
                ]
            },
            {
                "title": "2. Collect the 5 Sacred Shape Tokens:",
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
        "title": "QUARTER 1: THE ANCIENT MOSAIC OF THE FOREST",
        "subtitle": "You have reached the inner Forest ruins, {player_name}!",
        "theme": "forest",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Demonstrate comprehensive mastery of 2D shape attributes and visual geometry.",
            "Assemble interlocking jigsaw pieces using edge matching, pattern recognition, and spatial perception.",
            "Synthesize Quarter 1 geometry skills to unlock the path to Quarter 2: Barangay Kalye."
        ],
        "steps": [
            {
                "title": "1. Gather all 5 Jigsaw Pieces:",
                "bullets": [
                    "Find the 5 Shape Guardians across the forest ruins.",
                    "Hold a CLOSED FIST (or Click) to solve their geometric challenges."
                ]
            },
            {
                "title": "2. Bring the Pieces to the Old Man:",
                "bullets": [
                    "Reach the Old Man near the Master Portal with your collected pieces."
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

    # ====================================================
    # QUARTER 2: BARANGAY KALYE & FILIPINO MARKET (Maps 4, 5, 6)
    # ====================================================
    "quarter2": {
        "title": "QUARTER 2: BARANGAY KALYE & FIESTA",
        "subtitle": "Mabuhay, {player_name}! Welcome to lively Barangay Kalye!",
        "theme": "fiesta",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Recognize and count Philippine Peso currency coins (₱1, ₱5, ₱10, ₱20) and paper bills (₱20 to ₱1000).",
            "Calculate total costs and correct change in everyday market transactions.",
            "Apply units of measurement for length, weight/mass (g, kg), liquid capacity, and clock time.",
            "Understand basic fractions (1/2, 1/4) and geometric perimeter through Bayanihan cooperative building."
        ],
        "steps": [
            {
                "title": "1. Visit 5 Friendly Barrio Vendors:",
                "bullets": [
                    "Explore the street market and accept math challenges from neighborhood stations.",
                    "Hold a CLOSED FIST (or Click) to solve daily market and measurement problems."
                ]
            },
            {
                "title": "2. Build & Celebrate with Bayanihan Spirit:",
                "bullets": [
                    "Help construct the Bahay Kubo, arrange fiesta schedules, or measure market items!"
                ]
            },
            {
                "title": "3. Enter the Goal Portal to advance!",
                "bullets": []
            }
        ]
    },
    "map4.txt": {
        "title": "QUARTER 2: BARANGAY KALYE - STREET MARKET",
        "subtitle": "Mabuhay, {player_name}! Welcome to the lively Street Market!",
        "theme": "fiesta",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Identify denominations of Philippine Peso coins and banknotes.",
            "Solve addition and subtraction word problems involving buying, selling, and giving exact change.",
            "Read measurement scales for grocery weights and calculate jeepney passenger fares."
        ],
        "steps": [
            {
                "title": "1. Visit 5 Friendly Barrio Vendors:",
                "bullets": [
                    "Locate the Sari-Sari Store, Sorbetes Cart, Jeepney Terminal, Fruit Scale, and Parol Workshop.",
                    "Hold a CLOSED FIST (or Click) to calculate exact change, fares, and weights."
                ]
            },
            {
                "title": "2. Master Philippine Money, Change, & Measurements:",
                "bullets": [
                    "Calculate peso change, count coin totals, and check food weights!"
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
        "title": "QUARTER 2: THE BAHAY KUBO BUILD CHALLENGE",
        "subtitle": "Maligayang pagdating, {player_name}! Let's build with Bayanihan!",
        "theme": "fiesta",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Recognize and represent unit fractions (1/2, 1/3, 1/4) in construction parts and materials.",
            "Apply measurement concepts of perimeter, length (cm, m), and clock time to architectural planning.",
            "Demonstrate community cooperation (Bayanihan) through structured mathematical problem solving."
        ],
        "steps": [
            {
                "title": "1. Help 5 Barrio Craftspeople:",
                "bullets": [
                    "Solve math challenges on Fractions, Division, Shapes, Time, and Garden Perimeters.",
                    "Hold a CLOSED FIST (or Click) to accept each building challenge."
                ]
            },
            {
                "title": "2. Progressively Construct the Bahay Kubo:",
                "bullets": [
                    "Each correct answer raises bamboo stilts, woven walls, nipa roof, and ladder!"
                ]
            },
            {
                "title": "3. Enter the Goal Portal once the Bahay Kubo is complete!",
                "bullets": []
            }
        ]
    },
    "map6.txt": {
        "title": "QUARTER 2: THE GRAND FIESTA CELEBRATION",
        "subtitle": "It's Fiesta Day, {player_name}! The whole town is celebrating!",
        "theme": "fiesta",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Solve multi-step measurement, time scheduling, and money distribution problems.",
            "Calculate equal sharing of fiesta food portions, band performance schedules, and game prizes.",
            "Complete Quarter 2 mastery to unlock the golden sands of Quarter 3: Monetary Desert."
        ],
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

    # ====================================================
    # QUARTER 3: MONETARY DESERT & OASIS MIRAGE (Maps 7, 8, 9)
    # ====================================================
    "quarter3": {
        "title": "QUARTER 3: THE MONETARY DESERT EXPEDITION",
        "subtitle": "Welcome to the golden sands, {player_name}!",
        "theme": "desert",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Add and subtract 2-digit and 3-digit numbers with and without regrouping/borrowing.",
            "Read, analyze, and solve multi-step mathematical word problems involving quantities and currency.",
            "Identify number patterns, arithmetic sequences, skip-counting, and place value (hundreds, tens, ones).",
            "Estimate sums and differences to make accurate trade decisions and manage caravan supplies."
        ],
        "steps": [
            {
                "title": "1. Explore the Ancient Desert Ruins:",
                "bullets": [
                    "Find the 5 Desert Sages guarding the golden currency stations.",
                    "Hold a CLOSED FIST (or Click) to decode ancient trade tablets."
                ]
            },
            {
                "title": "2. Solve Multi-Step Money & Currency Problems:",
                "bullets": [
                    "Add and subtract Philippine Peso bills, count gold, and balance trade equations!"
                ]
            },
            {
                "title": "3. Unlock the Pharaoh's Golden Vault to reach Quarter 4!",
                "bullets": []
            }
        ]
    },
    "map7.txt": {
        "title": "QUARTER 3: MONETARY DESERT - CARAVAN TRAIL",
        "subtitle": "Mount your desert steed, {player_name}! The expedition begins!",
        "theme": "desert",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Perform 2-digit addition and subtraction involving market trade items and solar supplies.",
            "Interpret place value concepts (hundreds, tens, ones) on ancient number stone tablets.",
            "Apply skip-counting and pattern recognition to calculate caravan distances and water rations."
        ],
        "steps": [
            {
                "title": "1. Locate 5 Desert Sages:",
                "bullets": [
                    "Ride along the sandstone trail to find all 5 trade stations.",
                    "Hold a CLOSED FIST (or Click) to calculate cargo quantities and gold coins."
                ]
            },
            {
                "title": "2. Lead the Royal Caravan:",
                "bullets": [
                    "Gather all 5 Solar Cargo packs to energize the Sun Portal."
                ]
            },
            {
                "title": "3. Step Through the Sun Portal into Map 8!",
                "bullets": []
            }
        ]
    },
    "map8.txt": {
        "title": "QUARTER 3: MONETARY DESERT - PHARAOH'S VAULT",
        "subtitle": "Enter the ancient subterranean treasury, {player_name}!",
        "theme": "desert",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Solve 3-digit addition and subtraction problems requiring regrouping in tens and hundreds.",
            "Determine missing numbers in balanced arithmetic equations and number sentences.",
            "Apply logical deduction to unlock ancient numerical combination locks."
        ],
        "steps": [
            {
                "title": "1. Search the Pyramid Chambers:",
                "bullets": [
                    "Find the 5 Vault Guardians stationed among ancient treasure chests.",
                    "Hold a CLOSED FIST (or Click) to solve multi-digit equations."
                ]
            },
            {
                "title": "2. Collect 5 Desert Vault Keystones:",
                "bullets": [
                    "Place keystones into the central pharaoh's dais to break the vault seal!"
                ]
            },
            {
                "title": "3. Enter the Vault Portal to advance to Map 9!",
                "bullets": []
            }
        ]
    },
    "map9.txt": {
        "title": "QUARTER 3: MONETARY DESERT - OASIS MIRAGE",
        "subtitle": "The sacred waters shimmer beneath the desert sun, {player_name}!",
        "theme": "desert",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Master multi-step arithmetic word problems combining addition, subtraction, and currency exchange.",
            "Compare numerical expressions and evaluate trade balance inequalities.",
            "Complete Quarter 3 mastery to unlock the underwater passage to Quarter 4: Water Temple."
        ],
        "steps": [
            {
                "title": "1. Reach the 5 Oasis Sages:",
                "bullets": [
                    "Explore palm groves and ancient monoliths to answer final desert questions.",
                    "Hold a CLOSED FIST (or Click) to calculate exact trade values."
                ]
            },
            {
                "title": "2. Awaken the Pharaoh's Water Altar:",
                "bullets": [
                    "Watch the golden sands part to reveal the subterranean canal!"
                ]
            },
            {
                "title": "3. Step Through the Master Portal to dive into Quarter 4!",
                "bullets": []
            }
        ]
    },

    # ====================================================
    # QUARTER 4: WATER TEMPLE & CLOCKTOWER (Maps 10, 11, 12)
    # ====================================================
    "quarter4": {
        "title": "QUARTER 4: THE WATER TEMPLE SANCTUARY",
        "subtitle": "Dive deep into the sunken sanctum, {player_name}!",
        "theme": "water",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Read and write time in hours and minutes on analog and digital clocks, and compute elapsed time intervals.",
            "Formulate balanced arithmetic equations and solve multiplication/division (equal sharing) readiness problems.",
            "Apply spatial orientation, symmetry, and sequencing to operate canal floodgates and sluice valves.",
            "Synthesize comprehensive Grade 2 mathematical knowledge to achieve Grand Champion Mastery!"
        ],
        "steps": [
            {
                "title": "1. Locate the Water Temple Guardians:",
                "bullets": [
                    "Find each guardian stationed along the submerged aqueducts.",
                    "Hold a CLOSED FIST (or Click) to solve advanced grade-level challenges."
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
                    "Unlock the Master Temple Sanctum to complete Cognitive Maze!"
                ]
            }
        ]
    },
    "map10.txt": {
        "title": "QUARTER 4: WATER TEMPLE - THE TEMPLE AQUEDUCT",
        "subtitle": "Dive into the outer sanctuary, {player_name}!",
        "theme": "water",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Tell time to the nearest 5 minutes on clock faces and solve elapsed time word problems.",
            "Solve equal sharing and repeated addition (introductory multiplication) problems.",
            "Collect and sequence 6 Golden Keys to unlock the Ancient Lock Box."
        ],
        "steps": [
            {
                "title": "1. Locate the 6 Water Guardians:",
                "bullets": [
                    "Explore the submerged channels to locate all 6 guardians.",
                    "Hold a CLOSED FIST (or Click) to accept each mathematical test."
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
        "title": "QUARTER 4: THE SUBMERGED KEY VAULT",
        "subtitle": "The currents run deep, {player_name}!",
        "theme": "water",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Solve multi-step time, measurement, and mixed-operation arithmetic challenges.",
            "Understand division as equal grouping/partitioning in aquatic treasure distribution.",
            "Apply logical key matching to unlock the heavy double doors of the inner temple."
        ],
        "steps": [
            {
                "title": "1. Search the Submerged Chambers:",
                "bullets": [
                    "Find all 6 guardians stationed behind the temple barricades.",
                    "Hold a CLOSED FIST (or Click) to decode each water puzzle."
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
        "title": "QUARTER 4: THE LOTUS RAFT & FINAL SANCTUM",
        "subtitle": "Master the rapids of the Great Floodgate, {player_name}!",
        "theme": "water",
        "objectives_title": "🎯 LEARNING OBJECTIVES:",
        "objectives_subtitle": "After this activity, you should be able to:",
        "objectives": [
            "Demonstrate comprehensive mastery across all Grade 2 Math domains: Geometry, Measurement, Money, Arithmetic, and Time.",
            "Construct balanced arithmetic addition and multiplication equations using rune numbers.",
            "Navigate the interactive Lotus Raft across rushing water canals and celebrate Grand Champion Victory!"
        ],
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
                "title": "4. Enter the Grand Master Portal to complete Cognitive Maze!",
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
        "name": "Knight Guardian",
        "role": "Grand Fiesta Portal Guardian",
        "incomplete": "Halt, student! The Grand Fiesta Portal is sealed.\nFirst, resolve all 5 math challenges in the street market, then face my Philippine Currency Matching Trial!",
        "challenge": "Halt, courageous student {player_name}! You have resolved all 5 barrio market challenges.\nNow, to unlock the Grand Fiesta Portal, you must prove your knowledge in the Philippine Currency Matching Trial!\nMatch each Philippine bill and coin to its correct denomination!",
        "complete": "Outstanding valor and sharp intellect, {player_name}! You have successfully identified all Philippine currency!\nThe Grand Fiesta Portal is now permanently open. Step through to complete Quarter 2!"
    },
    ("quarter2", "map5.txt"): {
        "name": "Knight Guardian",
        "role": "Grand Fiesta Portal Guardian",
        "incomplete": "Halt, builder! The Grand Fiesta Portal is sealed.\nFirst, construct all 5 sections of the Bahay Kubo, then face my Philippine Currency Matching Trial!",
        "challenge": "Magnificent work constructing the Bahay Kubo, {player_name}!\nBefore you step through the Grand Fiesta Portal, you must pass my Philippine Currency Matching Trial!\nDemonstrate your mastery of Philippine Peso banknotes and coins!",
        "complete": "Superb mastery, {player_name}! You have mastered both geometry building and Philippine currency!\nThe Grand Fiesta Portal is unlocked. Proceed, champion!"
    },
    ("quarter2", "map6.txt"): {
        "name": "Knight Guardian",
        "role": "Grand Fiesta Portal Guardian",
        "incomplete": "Halt, traveler! The Grand Fiesta Portal is sealed.\nClear all 5 festival plaza stations before taking the Currency Trial!",
        "challenge": "Welcome to the Grand Portal, {player_name}! You have cleared all 5 festival stations.\nFace my final Philippine Currency Matching Trial to prove your fiscal wisdom!",
        "complete": "Mabuhay! Truly exceptional work, {player_name}!\nYou have mastered all Philippine Peso bills and coins with flying colors!\nThe Grand Fiesta Portal to Quarter 3 is now open!"
    },
    ("quarter2", "*"): {
        "name": "Knight Guardian",
        "role": "Grand Fiesta Portal Guardian",
        "incomplete": "Halt! Complete all 5 barrio stall challenges before taking the Currency Trial!",
        "challenge": "Halt, brave student {player_name}!\nTo unlock this portal, match each Philippine Peso bill and coin to its correct denomination!",
        "complete": "Magnificent! You have conquered the Philippine Currency Matching Trial!\nThe Grand Fiesta Portal is open!"
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


def get_map_instructions(arg1, arg2=None, arg3=None):
    """
    Returns the instructions dict for the specified map or quarter, with {player_name} formatted.
    Supports:
      get_map_instructions(map_or_quarter, player_name="Student")
      get_map_instructions(quarter_key, map_name, player_name="Student")
    """
    if arg3 is not None:
        # Explicit 3 args: (quarter_key, map_name, player_name)
        quarter_key = str(arg1).lower() if arg1 else "quarter1"
        m_key = str(arg2).lower() if arg2 else ""
        p_name = str(arg3) if arg3 else "Student"
    elif arg2 is not None:
        a2_str = str(arg2).lower().strip()
        if a2_str.endswith(".txt") or a2_str.startswith("map") or a2_str in ["*", ""]:
            # Called as (quarter_key, map_name)
            quarter_key = str(arg1).lower() if arg1 else "quarter1"
            m_key = a2_str
            p_name = "Student"
        else:
            # Called as (map_or_quarter, player_name)
            first_key = str(arg1).lower().strip() if arg1 else "quarter1"
            p_name = str(arg2) if arg2 else "Student"
            if first_key.startswith("quarter"):
                quarter_key = first_key
                m_key = ""
            else:
                quarter_key, m_key = _infer_quarter_and_map(first_key)
    else:
        # 1 arg
        first_key = str(arg1).lower().strip() if arg1 else "quarter1"
        p_name = "Student"
        if first_key.startswith("quarter"):
            quarter_key = first_key
            m_key = ""
        else:
            quarter_key, m_key = _infer_quarter_and_map(first_key)

    info = MAP_INSTRUCTIONS_DATA.get(m_key)
    if not info:
        info = MAP_INSTRUCTIONS_DATA.get(quarter_key)
    if not info:
        info = {
            "title": "QUEST OBJECTIVES",
            "subtitle": f"Welcome, {p_name}!",
            "theme": "forest",
            "objectives_title": "🎯 LEARNING OBJECTIVES:",
            "objectives_subtitle": "After this activity, you should be able to:",
            "objectives": [
                "Understand and apply mathematical reasoning to solve grade-level challenges.",
                "Complete station tasks and interact with guardians to advance your quest."
            ],
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
        "objectives_title": info.get("objectives_title", "🎯 LEARNING OBJECTIVES:"),
        "objectives_subtitle": info.get("objectives_subtitle", "After this activity, you should be able to:"),
        "objectives": list(info.get("objectives", [])),
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
