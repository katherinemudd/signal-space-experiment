import random
from typing import List

from dominate import tags
from markupsafe import Markup

import psynet.experiment
from .consent import consent
from .dat import dat
from .questionnaire import questionnaire
from .generate_sounds import parse_and_generate_audio
from psynet.consent import NoConsent
from psynet.modular_page import AudioPrompt, ColorPrompt, ModularPage, PushButtonControl, Prompt, Control, TextControl
from psynet.page import InfoPage, SuccessfulEndPage, WaitPage
from psynet.participant import Participant
from psynet.sync import GroupBarrier, SimpleGrouper
from psynet.timeline import Timeline, join, Event, while_loop, CodeBlock, Module, PageMaker
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker
from psynet.trial.chain import ChainTrialMaker
from psynet.trial.main import TrialMaker, TrialMakerState
from psynet.utils import as_plain_text, get_logger
from psynet.experiment import get_experiment, experiment_route
from psynet.prescreen import ColorBlindnessTest, AudioForcedChoiceTest
from psynet.asset import S3Storage
from .wait_video_old import video_wait_page

logger = get_logger()

set_condition_on = True

if set_condition_on:
    DOMAIN = "communication"         # options: "communication", "music"
    DRUM_KIT = "hihat+snare+kick"  # options: "snare+kick", "hihat+snare+kick"
    GRID_SIZE = 8            # options: 4, 8

else:
    DOMAIN = random.choice(["communication", "music"])
    GRID_SIZE = random.choice([4, 8])
    DRUM_KIT = random.choice(["snare+kick", "hihat+snare+kick"])

color_dict = {'yellow': [60, 100, 50],
              'orange': [38.8, 100, 50],
              'green': [120, 100, 50],
              'blue': [240, 100, 50],
              'purple': [277, 87, 53],
              'pink': [349.5, 100, 87.6],
              'red': [0, 100, 50],
              'brown': [30, 100, 29],
              'grey': [0, 0, 50]}

# before experiment starts, generate color lists for both participants
if DOMAIN == "communication":
    nodes = []  # Create one node for each color, where director_index 0 will always be director
    colors = list(color_dict.keys())
    for color in colors:
        nodes.append(
            StaticNode(definition={
                "director_index": 0,  # First participant will always be director
                "color": color,
                "matcher_choice":  'add color',
                "attempts": 0,  # Track number of attempts for this color
                "completed": False  # Track if this color has been completed
            })
        )
elif DOMAIN == "music":
    nodes = []
    melodies = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
    for melody in melodies:
        nodes.append(
            StaticNode(definition={
                "director_index": 0,  # First participant will always be director
                "melody": melody,
                "attempts": 0,  # Track number of attempts for this node
                "completed": False  # Track if node has been completed
            })
        )

class ColorCubeControl(Control):
    macro = "color_cube"
    external_template = "custom-controls.html"

    def __init__(self, color_hsl, drum_kit, grid_size, initial_pattern=None):
        super().__init__()
        self.color_hsl = color_hsl
        self.drum_kit = drum_kit
        self.grid_size = grid_size
        self.initial_pattern = initial_pattern

    @property
    def metadata(self):
        return {
            "color_hsl": self.color_hsl,
            "drum_kit": self.drum_kit,
            "grid_size": self.grid_size,
            "initial_pattern": self.initial_pattern,
            "style": "margin-bottom: 0; padding-bottom: 0;"
        }

class DrumMachineControl(Control):
    macro = "drum_machine"
    external_template = "custom-controls.html"

    def __init__(self, drum_kit, grid_size, initial_pattern=None):
        super().__init__()
        self.drum_kit = drum_kit
        self.grid_size = grid_size
        self.initial_pattern = initial_pattern

    @property
    def metadata(self):
        return {
            "drum_kit": self.drum_kit,
            "grid_size": self.grid_size,
            "initial_pattern": self.initial_pattern,
            "style": "margin-bottom: 0; padding-bottom: 0;"
        }

class SigSpaceTrialMaker(StaticTrialMaker):
    def __init__(self, id_, trial_class, nodes, expected_trials_per_participant, max_trials_per_participant, allow_repeated_nodes, sync_group_type):
        # Create a single block with all nodes
        super().__init__(
            id_=id_,
            trial_class=trial_class,
            nodes=nodes,
            expected_trials_per_participant=expected_trials_per_participant,
            max_trials_per_participant=max_trials_per_participant,
            allow_repeated_nodes=allow_repeated_nodes,
            sync_group_type=sync_group_type,
        )
    
    def get_next_trial(self, participant):
        """Override to only select uncompleted nodes"""
        # Get all uncompleted nodes
        completed_nodes = participant.vars.get("node_completion", {})
        uncompleted_nodes = []
        
        for node in self.nodes:
            if DOMAIN == "music":
                node_content = node.definition["melody"]
            else:  # communication
                node_content = node.definition["color"]
            
            if not completed_nodes.get(node_content, False):
                uncompleted_nodes.append(node)

        if uncompleted_nodes:
            # Randomly select from uncompleted nodes
            selected_node = random.choice(uncompleted_nodes)
            #print(f"selected node content={selected_node.definition.get('melody', selected_node.definition.get('color'))}")
            return selected_node
        else:
            # All nodes completed
            print(f"All nodes completed")
            return None

class SigSpaceTrial(StaticTrial):
    time_estimate = 5
    accumulate_answers = True
    time_credit_before_trial = 0
    time_credit_after_trial = 0

    def show_trial(self, experiment, participant):
        # Role assignment is now done in director_message function
        if DOMAIN == 'communication':
            participant.vars["current_color"] = self.definition["color"]
            participant.vars["director_color"] = self.definition["color"]  # Store the director's color separately

        # Add debugging for node progression
        node_content = self.definition.get("color") if DOMAIN == "communication" else self.definition.get("melody")
        print(f"DEBUG - Starting trial for participant {participant.id}, role={participant.vars.get('role')}, node_content={node_content}, domain={DOMAIN}")
        print(f"DEBUG - Node definition: {self.definition}")
        print(f"DEBUG - Participant's node completion: {participant.vars.get('node_completion', {})}")

        # Create a while loop that continues until this specific node is completed
        return while_loop(
                "node_attempt_loop",
                lambda participant: not participant.vars.get("node_completion", {}).get(
                    self.definition.get("color") if DOMAIN == "communication" else self.definition.get("melody"),
                    False
                ),  # Use participant's own completion state
                # Continue looping as long as the current node is NOT completed for this participant
                join(
                    GroupBarrier(
                        id_="wait_for_trial",
                        group_type="sigspace",
                        max_wait_time=300,
                    ),
                    self.director_turn(participant=participant),
                    GroupBarrier(
                        id_="director_finished_trial",
                        group_type="sigspace",
                        on_release=self.save_director_answer,
                        max_wait_time=300,
                    ),
                    self.matcher_turn(participant=participant),
                    GroupBarrier(
                        id_="matcher_finished_trial",
                        group_type="sigspace",
                        on_release=self.get_matcher_answer,
                        max_wait_time=300,
                    ),
                    WaitPage(
                        1,
                        content="Waiting for your partner...",
                    ),
                    self.feedback_page(experiment=experiment, participant=participant),
                    GroupBarrier(
                        id_="trial_completed",
                        group_type="sigspace",
                        max_wait_time=300,
                    ),
                ),
                expected_repetitions=9,  # Allow up to 9 attempts per node
            )

    def director_turn(self, participant):
        if participant.vars.get("role") == "director":
            node_content = self.definition.get("color") if DOMAIN == "communication" else self.definition.get("melody")
            
            # Check if we already have a rhythm for this node (use node content as key)
            existing_rhythm = participant.vars.get("node_rhythms", {}).get(node_content)
            
            if existing_rhythm and existing_rhythm is not None:
                # Show the existing rhythm with the drum machine pre-filled
                if DOMAIN == "communication":
                    director_color = participant.vars["current_color"]
                    director_color_hsl = color_dict.get(director_color)
                    
                    return join(
                        ModularPage(
                            "director-task",
                            Prompt(
                                Markup(
                                    f"<div style='text-align:center;'>Make a rhythm to have your partner guess this color.</div><br>"
                                ),
                                text_align="center"
                            ),
                            ColorCubeControl(director_color_hsl, DRUM_KIT, GRID_SIZE, initial_pattern=existing_rhythm),
                            time_estimate=60,
                            save_answer="last_action"
                        )
                    )
                else:  # DOMAIN == "music"
                    return join(
                        ModularPage(
                            "director-task",
                            Prompt(
                                Markup(
                                    f"<div style='text-align:center;'>Make a rhythm to have your partner guess this color.</div><br>"
                                ),
                                text_align="center"
                            ),
                            DrumMachineControl(DRUM_KIT, GRID_SIZE, initial_pattern=existing_rhythm),
                            time_estimate=60,
                            save_answer="last_action"
                        )
                    )
            else:
                # First time for this node - allow them to create a rhythm
                if DOMAIN == "communication":
                    director_color = participant.vars["current_color"]
                    director_color_hsl = color_dict.get(director_color)
                    #print(f'DEBUG - Director turn: node content is {node_content}, node is {self.definition}')

                    return join(
                        ModularPage(
                            "director-task",
                            Prompt(
                                Markup(
                                    "<div style='text-align:center;'>Make a rhythm to have your partner guess this color</div><br>"
                                ),
                                text_align="center"
                            ),
                            ColorCubeControl(director_color_hsl, DRUM_KIT, GRID_SIZE),
                            time_estimate=60,
                            save_answer="last_action"
                        )
                    )
                else:  # DOMAIN == "music"
                    return join(
                        ModularPage(
                            "director-task",
                            Prompt(
                                Markup(
                                    "<div style='text-align:center;'>Send an appealing rhythm to your partner.</div><br>"
                                ),
                                text_align="center"
                            ),
                            DrumMachineControl(DRUM_KIT, GRID_SIZE),
                            time_estimate=60,
                            save_answer="last_action"
                        )
                    )
        else:
            return join(
                WaitPage(
                    wait_time=1,
                    content='Waiting for your partner...',
                )
            )

    def save_director_answer(self, participants: List[Participant]):
        for p in participants:
                if p.vars.get("role") == "director":
                    # Get the current node content from the trial definition
                    # We need to access the trial definition through the experiment
                    experiment = get_experiment()
                    current_trial = p.current_trial
                    if current_trial:
                        node_content = current_trial.definition.get("color") if DOMAIN == "communication" else current_trial.definition.get("melody")
                    
                    # Always get the current rhythm from last_action
                    answer = p.vars.get("last_action")
                    self.node.var.director_rhythm = answer

                    # Check if we already have a rhythm for this node
                    existing_rhythm = p.vars.get("node_rhythms", {}).get(node_content)

                    if existing_rhythm and existing_rhythm is not None and answer == existing_rhythm:
                        # Rhythm hasn't changed - reuse existing audio
                        audio_filename = p.vars.get("node_audio_filenames", {}).get(node_content)
                    else:
                        # New or modified rhythm - store it and generate new audio
                        if "node_rhythms" not in p.vars:
                            p.vars["node_rhythms"] = {}
                        p.vars["node_rhythms"][node_content] = answer

                        # Generate audiofile for the rhythm
                        try:
                            print("DEBUG - try generate audio for rhythm")
                            audio_filename = parse_and_generate_audio(answer)
                            
                            # Store the audio filename for this node
                            if "node_audio_filenames" not in p.vars:
                                p.vars["node_audio_filenames"] = {}
                            p.vars["node_audio_filenames"][node_content] = audio_filename

                            if "node_rhythms" not in p.vars:
                                p.vars["node_rhythms"] = {}
                            p.vars["node_rhythms"][node_content] = answer
                        except Exception as e:
                            raise Exception(f"Audio generation failed for rhythm '{answer}': {str(e)}")

                    # save to participant vars so matcher can access
                    for pp in participants:
                        if pp.vars.get("role") == "matcher":
                            pp.vars["director_answer"] = answer
                            if audio_filename:
                                pp.vars["audio_filename"] = audio_filename

    def matcher_turn(self, participant):
        if participant.vars.get("role") == "matcher":
            try:
                # Retrieve the director's answer from participant vars
                director_answer = participant.vars.get("director_answer")
                audio_filename = parse_and_generate_audio(director_answer)  # generate here (instead of reading file from director)

                # Create audio player HTML
                audio_player_html = f"""
                <div style='margin-bottom: 20px; text-align: center;'>
                    <audio id='rhythm-audio' autoplay loop style='display: none;'>
                        <source src='/static/{audio_filename}' type='audio/mp3'>
                        Your browser does not support the audio element.
                    </audio>
                    <script>
                        // Auto-play the audio when the page loads
                        window.addEventListener('load', function() {{
                            var audio = document.getElementById('rhythm-audio');
                            // Ensure the audio loops seamlessly like the drum machine
                            audio.loop = true;
                            audio.volume = 1.0;
                            audio.play().catch(function(error) {{
                                console.log('Audio playback failed:', error);
                            }});
                        }});
                        
                        // Ensure audio continues playing even if interrupted
                        document.addEventListener('visibilitychange', function() {{
                            var audio = document.getElementById('rhythm-audio');
                            if (!document.hidden && audio.paused) {{
                                audio.play().catch(function(error) {{
                                    console.log('Audio playback failed:', error);
                                }});
                            }}
                        }});
                    </script>
                </div>
                """

                if DOMAIN == "communication":
                    # Communication domain: Show color grid
                    choices = list(color_dict.keys())
                    # Shuffle the color choices for each trial
                    shuffled_choices = choices.copy()
                    random.shuffle(shuffled_choices)
                    
                    # build the grid HTML
                    grid_html = (
                        f"{audio_player_html}"
                        "<div id='color-grid' style='display: grid; grid-template-columns: repeat(3, 70px); gap: 5px; justify-content: center;'>"
                    )
                    for i, color in enumerate(shuffled_choices):
                        hsl = color_dict[color]
                        grid_html += (
                            f"<div class='color-cube' "
                            f"data-color='{color}' "
                            f"style='background-color: hsl({hsl[0]}, {hsl[1]}%, {hsl[2]}%); "
                            "width: 60px; height: 60px; border-radius: 50%; border: 1px solid black; cursor: pointer;'></div>"
                        )
                    grid_html += "</div>"
                    # Add JS to trigger the hidden button
                    grid_html += """
                    <script>
                    document.querySelectorAll('.color-cube').forEach(function(el, idx) {
                        el.onclick = function() {
                            // Find the corresponding hidden button and click it
                            var btns = document.querySelectorAll('button');
                            btns[idx].click();
                        }
                    });
                    </script>
                    """

                    # Create hidden PushButtonControl with shuffled choices
                    hidden_labels = ["" for _ in shuffled_choices]  # No visible label
                    return ModularPage(
                        "matcher-task",
                        Prompt(Markup(
                            "<div style='text-align:center;'>Your partner produced this rhythm. What color were they referring to?</div><br>" +
                            grid_html
                        )),
                        PushButtonControl(
                            shuffled_choices,  # Use shuffled choices
                            labels=hidden_labels,
                            style="display:none;",
                            arrange_vertically=False,
                            show_next_button=False
                        ),
                        time_estimate=60,
                        save_answer="last_action"
                    )
                else:  # DOMAIN == "music"
                    return ModularPage(
                        "matcher-task",
                        Prompt(Markup(
                            "<div style='text-align:center;'>Your partner produced this rhythm. What do you think of this rhythm?</div><br>" +
                            audio_player_html +
                            "<style>.btn-primary { background-color: black !important; border-color: black !important; color: white !important; }</style>"
                        )),
                        PushButtonControl(
                            ["Not appealing", "Appealing"],
                            labels=["Not appealing", "Appealing"],
                            arrange_vertically=False,  # Changed to horizontal layout
                            show_next_button=False
                        ),
                        time_estimate=60,
                        save_answer="last_action"
                    )
            except Exception as e:
                print(f"Error in matcher_turn: {str(e)}")
                return InfoPage(
                    "An error occurred. Please try again.",
                    time_estimate=5
                )
        else:  # director sees this
            return join(
                WaitPage(
                    1,
                    content='Waiting for your partner...',
                )
            )

    def get_matcher_answer(self, participants: List[Participant]):
        try:
            # this is just to set the matcher_choice as an accessible attribute to both participants
            assert len(participants) == 2
            
            # Find which participant is the matcher
            matcher_participant = None
            director_participant = None
            for participant in participants:
                if participant.vars.get("role") == "matcher":
                    matcher_participant = participant
                elif participant.vars.get("role") == "director":
                    director_participant = participant
            
            # Get the matcher's choice
            matcher_choice = matcher_participant.vars.get("last_action")
            director_choice = director_participant.vars.get("last_action")

            # Share the choices with both participants
            for participant in participants:
                self.node.var.matcher_choice = matcher_participant.vars.get("last_action")  # todo
                if not hasattr(participant, 'var'):
                    participant.var = {}
                participant.var.last_trial = {
                    "action_self": participant.vars.get("last_action"),
                    "action_other": matcher_choice if participant.vars.get("role") == "director" else director_choice,
                }
                # Also store in vars for easier access
                participant.vars["last_trial"] = {
                    "action_self": participant.vars.get("last_action"),
                    "action_other": matcher_choice if participant.vars.get("role") == "director" else director_choice,
                }
            #print(f'get_matcher_answer self node definition {self.node.definition}')  # todo: works here (matcher_choice = color)
        except Exception as e:
            print(f"Error in get_matcher_answer: {str(e)}")

    def feedback_page(self, experiment, participant):
        #print(f'feedback_page self node definition {self.node.definition}')  # todo: doesn't have matcher_choice, but it does have it on line 504
        if DOMAIN == "communication":
            if participant.vars.get("role") == "matcher":
                matcher_choice = participant.vars.get("last_action")  # Get the matcher's choice from last_action
                matcher_choice_hsl = color_dict.get(matcher_choice, [0, 0, 0])

                director_color = participant.vars["director_color"]  # Use the stored director color
                director_color_hsl = color_dict.get(director_color, [0, 0, 0])

                if matcher_choice != director_color:
                    result = "Unsuccessful!"
                    self.node.var.attempts = self.definition.get("attempts", 0) + 1  # todo: Increment attempts counter
                elif matcher_choice == director_color:
                    result = "Successful!"
                    # Mark as completed using node content as key
                    node_content = self.definition.get("color")
                    participant.vars["node_completion"][node_content] = True

                    # Check if there are any uncompleted nodes left
                    uncompleted_nodes = [node for node in nodes if not participant.vars.get("node_completion", {}).get(
                        node.definition.get("color"), False
                    )]
                    if uncompleted_nodes:
                        print('skip')
                        #self.increase_current_node(participant)

                if result == "Successful!":
                    prompt = Markup(f"<strong>{result}</strong><br><br>"
                                    f"You guessed the right color.<br>")
                elif result == "Unsuccessful!":
                    prompt = Markup(f"<strong>{result}</strong><br><br>"
                                    f"You guessed the wrong color. Try again!<br>")

            else:  # "director"
                matcher_choice_alt = participant.vars.get("last_trial")
                matcher_choice = participant.vars.get("last_trial", {}).get("action_other")  # Get the matcher's choice from last_trial
                matcher_choice_hsl = color_dict.get(matcher_choice, [0, 0, 0])

                director_color = participant.vars["director_color"]  # Use the stored director color
                director_color_hsl = color_dict.get(director_color, [0, 0, 0])

                if matcher_choice == director_color:
                    result = "Successful!"
                    # Mark as completed using node content as key
                    node_content = self.definition.get("color")
                    participant.vars["node_completion"][node_content] = True
                    
                    # Check if there are any uncompleted nodes left
                    uncompleted_nodes = [node for node in nodes if not participant.vars.get("node_completion", {}).get(
                        node.definition.get("color"), False
                    )]
                    if uncompleted_nodes:
                        print('skip')
                        #self.increase_current_node(participant)
                    else:
                        # All nodes completed
                        print(f'DEBUG: All nodes completed')
                else:
                    # Don't set completed flag - let the while loop continue
                    result = "Unsuccessful!"

                # Set prompt based on result
                if result == "Successful!":
                    prompt = Markup(f"<strong>{result}</strong><br><br>"
                                    f"Your partner guessed the right color.<br>")
                elif result == "Unsuccessful!":
                    prompt = Markup(f"<strong>{result}</strong><br><br>"
                                    f"Your partner guessed the wrong color. Try again!<br>")

        elif DOMAIN == "music":
            if participant.vars.get("role") == "matcher":
                matcher_choice = participant.vars.get("last_action")  # Get the matcher's choice from last_action (same as communication domain)

                if matcher_choice == "Appealing":
                    prompt = Markup(f"<strong>Successful!</strong><br><br>"
                                f"You found your partner's rhythm appealing.")
                    # Mark as completed using node content as key
                    node_content = self.definition.get("melody")
                    participant.vars["node_completion"][node_content] = True

                    # Check if there are any uncompleted nodes left
                    uncompleted_nodes = [node for node in nodes if not participant.vars.get("node_completion", {}).get(
                        node.definition.get("melody"), False
                    )]
                    if uncompleted_nodes:
                        print('skip')
                        #self.increase_current_node(participant)  # todo
                    else:
                        # All nodes completed
                        print(f'DEBUG: All nodes completed')
                else:  # Don't set completed flag - let the while loop continue
                    prompt = Markup(f"<strong>Unsuccessful!</strong><br><br>"
                            f"You did not find your partner's rhythm appealing.")
            else:  # director
                matcher_choice = participant.vars.get("last_trial", {}).get("action_other")

                if matcher_choice == "Appealing":
                    prompt = Markup(f"<strong>Successful!</strong><br><br>"
                                f"Your partner found your rhythm appealing.")
                    # Mark as completed using node content as key
                    node_content = self.definition.get("melody")
                    participant.vars["node_completion"][node_content] = True

                    # Check if there are any uncompleted nodes left
                    uncompleted_nodes = [node for node in nodes if not participant.vars.get("node_completion", {}).get(
                        node.definition.get("melody"), False
                    )]
                    if uncompleted_nodes:
                        print('skip')
                        #self.increase_current_node(participant)
                    else:
                        # All nodes completed
                        print(f'DEBUG: All nodes completed')
                else:
                    prompt = Markup(f"<strong>Unsuccessful!</strong><br><br>"
                            f"Your partner did not find your rhythm appealing.")

        return ModularPage(
            "feedback",
            Prompt(
                text=Markup(f"{prompt}<style>#next-button {{ display: block; margin: 20px auto; background-color: black !important; border-color: black !important; }}</style>"),
                text_align="center"
            ),
            time_estimate=60,
            show_next_button=True
        )

def save_conditions(participant, experiment):
    """Store experiment conditions in participant vars"""
    participant.vars["domain"] = DOMAIN
    participant.vars["grid_size"] = GRID_SIZE
    participant.vars["drum_kit"] = DRUM_KIT

def requirements():
    html = tags.div()
    with html:
        tags.h1("Experiment structure")
        tags.p(
            "Before starting the experiment, here is the structure of the experiment so you know what to expect:"
        )
        tags.p(
            "1. Four short pretests",
            tags.br(),
            "2. The main experiment with a partner",
            tags.br(),
            "3. A short exit questionnaire"
        )
        tags.p(
            " "
        )
        tags.p(
            "For the duration of the experiment please sit in a quiet place with a good internet connection. Please do not use headphones. You will need to be able to record yourself tapping and you will need to be able to hear sounds. The experiment will take approximately 30 minutes."
        )
        tags.p(
            "It is important to note that you will have a time limit for each task. Please keep going through the experiment to avoid timing out and having to end the experiment early."
        )
        tags.p(
            "If you satisfy these requirements, please press 'Next' to begin the experiment. Thank you for taking part in our experiment! If you are not able to satisfy these requirements currently, please exit the experiment."
        )

    return InfoPage(html, time_estimate=60)

def experiment_start():
    html = tags.div()
    with html:
        tags.h1("Experiment with a partner")
        tags.p(
            "You will soon begin an experiment with another participant."
        )
        if DOMAIN == "communication":
            tags.p(
                "You will either have the role of creating sounds on a drum machine to describe colors or guessing which color your partner was referring to with a rhythm created on a drum machine."
               )
        if DOMAIN == "music":
            tags.p(
                "You will either have the role of creating sounds on a drum machine or giving feedback on the sounds created by your partner."
               )

        tags.p(
            "There are time limits for each experiment phase, so it is important that you keep progressing through the experiment to avoid timing out and ending the experiment early for you and your partner."
        )
        tags.p(
            "Please press 'Next' when you are ready to be paired with a participant."
        )
    return InfoPage(html, time_estimate=60)

def director_message(participant):
    """Show role-specific instructions before the experiment starts"""
    # Set role based on participant ID (even/odd) if not already set
    if "role_index" not in participant.vars:
        participant.vars["role_index"] = participant.id % 2  # 0 for director, 1 for matcher
        participant.vars["role"] = "director" if participant.vars["role_index"] == 0 else "matcher"
        # Initialize participant's own completion tracking with all nodes as False
        if DOMAIN == "music":
            participant.vars["node_completion"] = {melody: False for melody in ["A", "B", "C", "D", "E", "F", "G", "H", "I"]}
        elif DOMAIN == "communication":
            participant.vars["node_completion"] = {color: False for color in color_dict.keys()}
    
    # Show role-specific instructions
    if participant.vars.get("role") == "director" or participant.vars.get("role") == "producer":
        html = tags.div()
        with html:
            if DOMAIN == "communication":
                tags.h1("Director Instructions")
                tags.p("You will see a color and will be asked to create a rhythm that represents that color to send to your partner. Your partner will guess which color you are referring to.")
                tags.p("You and your partner will receive a bonus based on how quickly your partner guesses the color you were shown. The fewer trials it takes them to guess the color you were shown, the larger your bonus will be.")
            if DOMAIN == "music":
                tags.h1("Producer Instructions")
                tags.p("As the producer, you will use a drum machine to create rhythms that your partner will rate as 'not appealing' or 'appealing'.")
                tags.p("You and your partner will receive a bonus based on how quickly your partner finds your rhythms appealing. The fewer trials it takes them to find your rhythm appealing, the larger your bonus will be.")
            tags.p("Press 'Next' when you are ready to begin.")
        return InfoPage(html, time_estimate=60)

def debrief_and_feedback():
    return ModularPage(
        "debrief_and_feedback",
        Markup("""
        <h1>Debrief and Feedback</h1>
        <p>Thank you for participating in this study. The data you have submitted will be used to better understand the relationship between (divergent) creativity, exploration and success on the musical or communication task. Your data will be kept strictly anonymous. If you would like to provide feedback on your experience with this experiment, please type it in the box below.</p>
        """),
        TextControl(one_line=False),
        time_estimate=60
    )

def redirect_to_prolific():
    html = tags.div()
    with html:
        tags.p(
            """You will now be redirected directly to the prolific page.""",
        )
        tags.script(
            """
            setTimeout(function() {
                window.location.href = 'https://app.prolific.com/submissions/complete?cc=CQCDYRO7';
            }, 2000);
            """
        )

    return InfoPage(html, time_estimate=60)

class CustomColorBlindnessTest(ColorBlindnessTest):  # Custom ColorBlindnessTest with custom introduction
    @property
    def introduction(self):
        return InfoPage(
            tags.div(
                tags.h1("Color test"),
                tags.p("This test helps us ensure you can properly see and distinguish colors."),
                tags.p("You will see colored circles and need to identify the number or pattern within them."),
                tags.p("In each trial, you will be presented with an image that contains a number."),
                tags.p(f"This image will disappear after {self.hide_after} seconds."),
                tags.p("You must enter the number that you see into the text box.")
            ),
            time_estimate=10
        )

class CustomAudioForcedChoiceTest(AudioForcedChoiceTest):  # Custom AudioForcedChoiceTest with custom introduction
    @property
    def introduction(self):
        return InfoPage(
            tags.div(
                tags.h1("Audio Test"),
                tags.p("This test helps us ensure you can properly hear and classify audio stimuli."),
                tags.p("In each trial, you will hear a sound of an animal. Which animal does this sound come from?"),
                tags.p("Select the category which fits best to the played sound file.")
            ),
            time_estimate=10
        )

class Exp(psynet.experiment.Experiment):
    # Configure local storage for static assets and generated audio files
    variables = {"max_participant_payment": 20.0}
    #asset_storage = S3Storage("sigspace-bucket", "sigspace-experiment")  # Comment out S3 for local development

    def __init__(self, session):
        super().__init__(session)
        self.all_nodes = nodes  # Initialize the list of all nodes
        self.current_node_index = 0  # Start with the first node

    @experiment_route("/participant_in_barrier/<participant_id>", methods=["GET"])
    @classmethod
    def participant_in_barrier(cls, participant_id):
        from psynet.participant import Participant
        from flask import jsonify
        participant = Participant.query.get(participant_id)
        return jsonify(len(participant.active_barriers) > 0)

    timeline = Timeline(
        consent(),
        # PageMaker(requirements, time_estimate=60),
        # CustomColorBlindnessTest(
        #      label="color_blindness_test",
        #      performance_threshold=1,  # Participants can make 1 mistake
        #      time_estimate_per_trial=5.0,
        #      hide_after=3.0,  # Image disappears after 3 seconds
        # ),
        # CustomAudioForcedChoiceTest(
        #      csv_path="cats_dogs_birds.csv",
        #      answer_options=["cat", "dog", "bird"],
        #      performance_threshold=1,  # Participants can make 1 mistake
        #      instructions="""
        #          <p>This test helps us ensure you can properly hear and classify audio stimuli.</p>
        #          <p>In each trial, you will hear a sound of an animal. Which animal does this sound come from?</p>
        #          """,
        #      question="Select the category which fits best to the played sound file.",
        #      label="audio_forced_choice_test",
        #      time_estimate_per_trial=8.0,
        #      n_stimuli_to_use=3  # Use 3 random stimuli from the CSV
        # ),
        # dat(),

        SimpleGrouper(
            group_type="sigspace",
            initial_group_size=2,
            max_wait_time=300,
        ),
        CodeBlock(save_conditions),  # todo: how can I generate the conditions here instead of at the beg?

        PageMaker(experiment_start, time_estimate=10),

        CodeBlock(lambda participant: participant.set_answer("continue")),

        PageMaker(director_message, time_estimate=10),
        Module(
            "experiment",
            SigSpaceTrialMaker(
                id_="sigspace_trial",
                trial_class=SigSpaceTrial,
                nodes=nodes,  # Pass all nodes
                expected_trials_per_participant=len(nodes),
                max_trials_per_participant=len(nodes),
                allow_repeated_nodes=False,
                sync_group_type="sigspace",
            ),
        ),
        questionnaire(),
        debrief_and_feedback(),
        redirect_to_prolific(),
        SuccessfulEndPage(),
    )
