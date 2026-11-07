"""Human-authored stories. No downloaded scripts and no LLM service."""
from dataclasses import dataclass
import hashlib
import json
import re


@dataclass(frozen=True)
class Topic:
    key: str
    theme: str
    title: str
    goal: str
    beats: tuple[str, ...]
    visuals: tuple[str, ...]
    tags: tuple[str, ...]
    source: str = ""

    @property
    def fingerprint(self):
        text = " ".join(self.beats).lower()
        return hashlib.sha256(re.sub(r"\W+", " ", text).encode()).hexdigest()


def topic(key, theme, title, goal, text, visuals, tags, source=""):
    beats = tuple(text.split("|"))
    assert len(beats) == len(visuals.split()), key
    return Topic(key, theme, title, goal, beats, tuple(visuals.split()), tuple(tags.split(",")), source)


TOPICS = [
    topic("bridge", "adventure", "Pip's Little Bridge", "Solve a small problem together.",
          "Pip the bunny finds a tiny stream on the forest path.|His friend Tilly Turtle wants to reach the flowers across it.|Pip finds a broad fallen leaf beside the shallow water.|Together they place their leaf across the tiny stream like a bridge.|Tilly crosses safely, and both friends enjoy the flowers together.",
          "pond flowers leaf leaf flowers", "friendship,problem solving,animal story"),
    topic("lost-star", "adventure", "The Star That Was a Flower", "Look closely before deciding.",
          "Tilly spots something yellow shining softly beside the garden path.|Could a little star have fallen down into their garden?|Pip looks closely and sees five bright yellow flower petals.|It is a flower, growing safely underneath the warm sun.|They leave it growing so everyone can enjoy its lovely shape.",
          "flower star flower sun flower", "flowers,observation,animal story"),
    topic("rain-shelter", "adventure", "A Cozy Place for Two", "Find a gentle solution with a friend.",
          "Soft raindrops surprise Pip and Tilly during their gentle garden walk.|Pip spots a broad leaf resting beside a little tree.|He holds it up, but Tilly is still getting wet.|They move closer together until the leaf covers both their heads.|The rain stops, and two cozy friends continue their lovely walk.",
          "rain leaf rain leaf sun", "friendship,rain,animal story"),
    topic("seed-journey", "adventure", "Where Will the Little Seed Grow?", "Care for a seed.",
          "Pip finds a tiny seed lying on the garden path.|Tilly helps him find some soft soil near the sunny flowers.|They tuck the seed into soil and add a little water.|They visit again over many days, watching patiently for a sprout.|At last, a tiny green shoot welcomes both their happy faces.",
          "seed soil water sun sprout", "seeds,patience,gardening"),
    topic("moon-walk", "adventure", "Tilly's Quiet Moonlit Walk", "Notice familiar things in a new setting.",
          "In our pretend story, Tilly takes a gentle evening walk.|The same garden looks different under the softly shining moon.|Pip points out their tree, their flowers, and their little pond.|Tilly recognizes each familiar place, even in the cool blue light.|They return home together, ready for a calm and cozy rest.",
          "moon tree flowers pond moon", "bedtime,observation,animal story"),
    topic("count-three", "counting", "Three Carrots for the Picnic", "Count three objects, one at a time.",
          "Pip is packing carrots for a little picnic with Tilly.|Here is one carrot, waiting in the bright picnic basket.|Add another carrot, and now there are two carrots altogether.|One more joins them: one, two, three bright orange carrots.|We counted each carrot once, and our picnic is ready now.",
          "carrot:0 carrot:1 carrot:2 carrot:3 carrot:3", "counting,numbers,picnic"),
    topic("count-five", "counting", "Five Stars in Tilly's Picture", "Count five stars.",
          "Tilly is drawing a night sky, one little star at a time.|First come two stars, shining together in her pretend sky.|She adds two more, and now four stars fill the picture.|One final star makes five: one, two, three, four, five.|Five lovely stars make Tilly's picture feel bright and complete.",
          "star:0 star:2 star:4 star:5 star:5", "counting,stars,numbers"),
    topic("count-down", "counting", "The Five-Flower Countdown", "Count backward from five to one.",
          "Five paper flowers are ready for Pip's pretend garden game.|Tilly covers one with a leaf, leaving four flowers showing.|She covers another flower, and three flowers are still showing.|She covers one more, leaving just two paper flowers still showing.|Cover one more: one remains. Then uncover all five flowers again.",
          "flower:5 flower:4 flower:3 flower:2 reveal-flowers", "counting,countdown,numbers"),
    topic("add-one", "counting", "One More Makes Four", "Add one to a group of three.",
          "Pip places three smooth pebbles beside Tilly's little garden drawing.|Let's count them carefully together: one, two, three little pebbles.|Tilly brings one more pebble and places it beside the others.|Now count the whole group: one, two, three, four pebbles.|Adding one to three makes four. Their pebble path is ready!",
          "pebble:3 pebble:3 pebble:1 pebble:4 pebble:4", "addition,counting,numbers"),
    topic("pairs", "counting", "A Pair for Each Friend", "Understand a pair as two objects.",
          "Pip and Tilly are making paper stars for their pictures.|Pip chooses two stars, and Tilly chooses two stars too.|A group of two matching things can be called a pair.|One pair for Pip, and one pair for his friend Tilly.|Count all their stars together: one, two, three, four shining stars.",
          "star:4 star:2 star:2 star:4 star:4", "pairs,counting,numbers"),
    topic("circles", "shapes", "The Circle Has No Corners", "Recognize circles.",
          "Pip is searching for a shape with no corners today.|A circle curves all the way around, with no straight sides.|Tilly draws one big circle and one tiny circle beside it.|Their sizes are different, but both shapes are still circles.|Follow the round edge with your eyes, all the way home.",
          "circle:1 circle:1 circle:2 circle:2 circle:1", "circles,shapes,geometry"),
    topic("triangles", "shapes", "Three Sides Make a Triangle", "Identify a triangle by its three sides.",
          "Tilly has a shape puzzle for Pip in the garden.|This shape has one straight side, then two, then three.|It also has three corners, where those straight sides meet.|A shape with three straight sides is called a triangle.|Big or small, our triangles always have three straight sides.",
          "triangle:1 triangle:1 triangle:1 triangle:2 triangle:3", "triangles,shapes,geometry"),
    topic("color-sort", "shapes", "Pip Sorts Red and Blue", "Group objects by color.",
          "Pip finds red and blue paper circles on the picnic mat.|He places the red circles together on one side of the mat.|Tilly places the blue circles together on the other side.|They have sorted the circles into groups using their colors.|Every circle has a place, and their colorful mat looks tidy.",
          "mixed circles-red circles-blue sorted sorted", "colors,sorting,shapes"),
    topic("squares", "shapes", "Four Equal Sides for a Square", "Recognize squares.",
          "Tilly draws a square for Pip's little paper house window.|It has four straight sides, and all four are equally long.|Its four corners look like the corner of a book.|Pip draws a smaller square, keeping those same special features.|Both are squares: four equal sides and four tidy right-angle corners.",
          "square:1 square:1 square:1 square:2 square:2", "squares,shapes,geometry"),
    topic("mix-green", "shapes", "Yellow and Blue Paint Make Green", "Observe a common paint color mixture.",
          "Pip has yellow paint and blue paint for his garden picture.|Tilly puts a little of each color onto the mixing tray.|They slowly stir the two paints together with their pretend brush.|With these paints, yellow and blue mix into a lovely green.|Now they can paint green leaves around their bright paper flowers.",
          "paint-yellow paint-blue paint-mix leaf flowers", "colors,paint,color mixing"),
    topic("butterfly", "facts", "A Butterfly's Six Little Legs", "Learn that butterflies are insects with six legs.",
          "A butterfly rests near Pip and Tilly's colorful garden flowers.|Butterflies are insects, and insects have six legs on their bodies.|Our drawing spreads the legs out so we can count them.|One, two, three on one side, and three on the other.|That makes six legs! Pip watches gently without touching the butterfly.",
          "butterfly butterfly butterfly butterfly flowers", "butterflies,insects,animal facts", "https://www.si.edu/spotlight/buginfo/butterfly"),
    topic("turtle-shell", "facts", "Tilly's Shell Is Part of Her", "Understand that a turtle shell is part of its body.",
          "Tilly Turtle carries her shell everywhere she goes in our story.|A real turtle's shell is part of its body, including bones.|A turtle cannot take its shell off like a little jacket.|Its shell grows along with it as the turtle gets bigger.|Pip understands: Tilly's shell belongs to Tilly, every single day.",
          "turtle turtle turtle turtle turtle", "turtles,shells,animal facts", "https://nationalzoo.si.edu/animals/eastern-box-turtle"),
    topic("bird-feathers", "facts", "Feathers Make a Bird Special", "Recognize feathers as a bird feature.",
          "Pip notices a little bird resting quietly beside the garden.|Birds have feathers, which help keep their bodies warm and protected.|Many birds also use their wing feathers when they fly.|Some birds do not fly, but they still have feathers too.|Pip watches the bird from a distance and leaves it undisturbed.",
          "bird bird bird bird tree", "birds,feathers,animal facts", "https://www.allaboutbirds.org/news/all-about-feathers/"),
    topic("frog", "facts", "A Tadpole Grows Into a Frog", "Learn a simple frog life cycle.",
          "Tilly looks at a picture of a frog's amazing life story.|A frog begins as an egg, often laid in the water.|A tadpole hatches, swimming with a tail before its legs grow.|As it changes into a frog, its tail slowly becomes smaller.|A little frog has grown! Real ponds are best watched with adults.",
          "pond eggs tadpole frog frog", "frogs,life cycles,animal facts", "https://www.britannica.com/animal/frog"),
    topic("bee", "facts", "A Bee Carries Pollen", "Learn how bees can help pollination.",
          "Pip watches a bee visiting flowers in the sunny garden.|The bee gathers food, and some pollen sticks to its body.|When it visits another flower, some pollen can move there too.|This helps many plants make seeds for new plants to grow.|Pip gives the bee plenty of space to do its work.",
          "bee flower bee seed flowers", "bees,pollination,animal facts", "https://www.fs.usda.gov/wildflowers/pollinators/animals/bees.shtml"),
    topic("share-apples", "kindness", "Two Friends Share a Picnic", "Notice another person's needs.",
          "Pip brings two pretend apples to the sunny garden picnic.|Tilly arrives with a blanket, but she has no snack.|Pip notices his friend and offers her one of his apples.|Now each friend has one apple to enjoy at the picnic.|Sharing what we can helps both friends feel welcome and included.",
          "apple:2 picnic apple:1 apple:2 picnic", "sharing,kindness,friendship"),
    topic("take-turns", "kindness", "A Turn for Pip, a Turn for Tilly", "Practice taking turns.",
          "Pip and Tilly both want to draw with one green crayon.|Tilly asks if they can each have a little drawing turn.|Pip draws a leaf first, then passes the crayon to Tilly.|Tilly draws a tree and gives the crayon back with thanks.|Their picture grows together because both friends get a fair turn.",
          "leaf leaf leaf tree tree", "taking turns,kindness,friendship"),
    topic("help-clean", "kindness", "The Garden Cleanup Team", "Help with a shared task.",
          "A gentle breeze scatters paper shapes from Tilly's little craft basket.|Tilly looks at the shapes and wonders where she should begin.|Pip offers to gather circles while Tilly gathers all the squares.|Working together, they put every paper shape back in the basket.|Helping with a small task can make a big difference for friends.",
          "mixed mixed circle:3 square:3 sorted", "helping,teamwork,kindness"),
    topic("listen", "kindness", "Pip Learns to Listen", "Listen while a friend speaks.",
          "Tilly wants to tell Pip about a flower she has found.|Pip starts talking too, and neither friend can hear the other.|Pip pauses, faces Tilly, and listens while she tells her story.|Then Tilly listens as Pip tells her about his garden drawing.|Taking turns to speak helps both friends feel heard and understood.",
          "flower flower flower tree flowers", "listening,kindness,friendship"),
    topic("welcome", "kindness", "Room on the Picnic Blanket", "Welcome someone into a shared activity.",
          "Pip has arranged a pretend picnic beside the big garden tree.|Tilly stands nearby, wondering whether there is room for her too.|Pip moves his basket aside and makes a comfortable little space.|He invites Tilly to join him, and she smiles with relief.|A small welcoming action can help a friend feel they belong.",
          "picnic tree picnic picnic flowers", "inclusion,kindness,friendship"),
    topic("odd-shape", "puzzle", "Which Shape Has Three Sides?", "Find a triangle using its sides.",
          "Pip has a gentle shape puzzle for you and Tilly.|Here are a circle, a square, and a triangle together.|Which shape has exactly three straight sides? Take a little look.|The triangle is the answer: count its three straight sides slowly.|Well spotted! The circle curves, and the square has four sides.",
          "mixed puzzle-shapes puzzle-shapes triangle:1 mixed", "shape puzzle,triangles,reasoning"),
    topic("missing-star", "puzzle", "What Comes Next in the Pattern?", "Continue an alternating pattern.",
          "Tilly has made a little pattern with circles and stars.|Circle, star, circle, star: the same two shapes keep repeating.|Next comes a circle. Which shape should follow that circle?|A star comes next, because our pattern alternates between two shapes.|Circle, star, circle, star! Pip and Tilly finish their pattern together.",
          "pattern pattern pattern-question star:1 pattern", "patterns,visual puzzle,reasoning"),
    topic("which-more", "puzzle", "Which Group Has More Flowers?", "Compare groups of two and four.",
          "Pip puts two flowers on one side of his picture.|Tilly puts four flowers on the other side of the picture.|Which group has more flowers? Let's count each group with care.|Two on Pip's side, and four on Tilly's side: four is more.|Counting helps us compare, and every flower makes their picture lovely.",
          "flower:2 flower:4 compare-flowers compare-flowers flowers", "comparing,counting,visual puzzle"),
    topic("shadow", "puzzle", "Find the Matching Shape", "Match a shape to its outline.",
          "Tilly draws a round circle beside three different shape outlines.|One outline is a triangle, one is square, and one is round.|Which outline has the same shape as Tilly's round circle?|The round outline matches, because both edges curve all around.|Pip places the circle inside, and the matching puzzle is complete.",
          "circle:1 puzzle-shapes puzzle-shapes circle:1 circle:1", "matching,shapes,visual puzzle"),
    topic("size", "puzzle", "Small, Medium, Then Big", "Order three objects by size.",
          "Pip draws three circles with three very different sizes today.|One is small, one is medium, and one is big.|Can we put them in order, starting with the smallest?|First small, then medium, then big: each circle grows in size.|Tilly follows the row and smiles at their neatly ordered circles.",
          "sizes sizes sizes sizes sizes", "sizes,ordering,visual puzzle"),
    topic("moon-light", "nature", "The Moon Reflects Sunlight", "Understand why we can see the Moon.",
          "Pip wonders why the Moon looks bright in the night sky.|The Moon does not make its own light like the Sun.|Sunlight reaches the Moon and bounces off its rocky surface.|Some of that reflected light travels toward us here on Earth.|That is how we see the Moon shining in our sky.",
          "moon sun sun-moon sun-moon moon", "moon,space,sunlight", "https://science.nasa.gov/moon/moon-facts/"),
    topic("earth-spin", "nature", "Earth Turns From Day to Night", "Connect Earth's rotation with day and night.",
          "Tilly imagines Earth as a big round ball in space.|The Sun lights the side of Earth that faces toward it.|Earth keeps turning, carrying places into sunlight and then away.|Facing the Sun brings daytime; facing away brings the nighttime sky.|One whole turn takes about a day. Our world keeps turning!",
          "earth sun-earth earth earth moon", "earth,day and night,space", "https://spaceplace.nasa.gov/days/en/"),
    topic("roots", "nature", "Roots Help a Plant Grow", "Learn a simple function of roots.",
          "Pip sees green leaves above the soil in Tilly's garden.|Underneath, roots spread through the soil where we cannot usually see.|Roots help hold the plant in place as it grows.|They also take in water that the plant needs to live.|Leaves above and roots below work together in a growing plant.",
          "sprout roots roots water sprout", "roots,plants,nature", "https://www.bbc.co.uk/bitesize/topics/zpxnyrd"),
    topic("rainbow", "nature", "Sunlight and Raindrops Make a Rainbow", "Learn a simple explanation of rainbows.",
          "Pip and Tilly notice a colorful rainbow after some rain.|Sunlight can enter water drops floating in the air around us.|Inside those drops, light bends, reflects, and spreads into different colors.|With the Sun behind us, we may see a rainbow ahead.|Our picture shows the lovely colors spreading across the gentle sky.",
          "rainbow sun rain rainbow rainbow", "rainbows,light,nature", "https://spaceplace.nasa.gov/rainbows/en/"),
    topic("sun-star", "nature", "Our Sun Is a Star", "Understand that the Sun is a star.",
          "Tilly looks at a picture of stars in the night sky.|Our Sun is a star too, much closer than other stars.|It gives Earth light and warmth that living things need.|In our drawing, the Sun looks big because it is nearby.|We enjoy its light safely, and never look straight at the Sun.",
          "star:5 sun sun-earth sun sun", "sun,stars,space", "https://spaceplace.nasa.gov/sun-compare/en/"),
    topic("patient-flower", "story", "Pip and the Patient Flower", "A story about patience.",
          "Pip plants a seed and hopes for a flower right away.|He checks again after lunch, but the soil looks just the same.|Tilly reminds him that growing takes water, sunlight, and plenty of time.|Over many days, a sprout grows leaves and then a bud.|At last a flower opens, and Pip feels glad he waited.",
          "seed soil sun sprout flower", "patience,short story,growing"),
    topic("leaf-boat", "story", "The Little Leaf Boat", "A story about adapting a plan.",
          "In our pretend garden, Pip builds a boat from a leaf.|He puts a pebble inside, and the little boat tips over.|Tilly suggests trying something much lighter than the heavy pebble.|Pip adds one tiny flower petal, and the leaf floats gently.|Their new plan works, and both friends enjoy their little creation.",
          "leaf pebble:1 leaf flower pond", "problem solving,short story,friendship"),
    topic("picture-gift", "story", "A Picture Full of Friendship", "A story about a thoughtful gift.",
          "Tilly wants to make a special little gift for Pip.|She draws their garden, with flowers beside the familiar shady tree.|One corner looks empty, so she adds two friends standing together.|Pip sees the picture and recognizes all their favorite garden places.|The thoughtful gift reminds them of the happy time they share.",
          "flowers tree tree picnic flowers", "friendship,gifts,short story"),
    topic("wrong-path", "story", "The Path Back to the Picnic", "A story about noticing clues.",
          "In our pretend garden, Pip forgets where their picnic blanket is.|Tilly remembers that they placed it beside a tall leafy tree.|They spot flowers first, then a pond, but neither place matches.|At the tree, their blanket waits just where they left it.|Remembering one useful clue helped both friends find their picnic again.",
          "picnic tree flowers pond picnic", "memory,short story,reasoning"),
    topic("cloud-picture", "story", "Tilly's Changing Cloud Picture", "A story about flexible thinking.",
          "Tilly draws a fluffy cloud shaped like a little bunny.|A breeze moves the real cloud, and its shape slowly changes.|Pip thinks the new shape looks more like a little turtle.|Tilly adds a second cloud to her drawing for her new idea.|Both pictures can be lovely, and changing a plan can be fun.",
          "cloud cloud cloud cloud cloud", "creativity,short story,clouds"),
]


def save_script(topic, config, selection, job, out):
    data = {
        "job_id": job, "topic": topic.key, "theme": topic.theme,
        "title": topic.title, "description": f"{topic.goal} Join Pip Bunny and Tilly Turtle in an original animated story from {config.channel_name}.",
        "hashtags": ["#Shorts", "#LearningForKids", "#" + {"adventure":"AnimalStories", "counting":"Counting", "shapes":"Shapes", "facts":"AnimalFacts", "kindness":"Kindness", "puzzle":"LearningPuzzles", "nature":"Nature", "story":"KidsStories"}[topic.theme]],
        "tags": ["original animation", "children's learning", *topic.tags],
        "learning_goal": topic.goal, "audience": config.audience,
        "selfDeclaredMadeForKids": True,
        "containsSyntheticMedia": config.contains_synthetic_media,
        "fingerprint": topic.fingerprint, "selection": selection,
        "educational_source": topic.source,
        "scenes": [{"narration": text, "visual": visual} for text, visual in zip(topic.beats, topic.visuals)],
    }
    (out / "script.json").write_text(json.dumps(data, indent=2))
    (out / "script.txt").write_text("\n\n".join(topic.beats))
    return data
