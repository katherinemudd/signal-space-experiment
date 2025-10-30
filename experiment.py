# pylint: disable=unused-import,abstract-method

import logging
import random

from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNetwork, StaticNode, StaticTrial, StaticTrialMaker

# katie added
from .consent import CustomConsent
from .dat import dat
from dominate import tags
from psynet.modular_page import Control, Prompt, TextControl
from psynet.page import SuccessfulEndPage
from psynet.prescreen import ColorBlindnessTest, AudioForcedChoiceTest
from psynet.timeline import join, PageMaker
from .questionnaire import questionnaire

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


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

def get_color_dict():
    return {'yellow': [60, 100, 50],
            'orange': [38.8, 100, 50],
            'green': [120, 100, 50],
            'blue': [240, 100, 50],
            'purple': [277, 87, 53],
            'pink': [349.5, 100, 87.6],
            'red': [0, 100, 50],
            'brown': [30, 100, 29],
            'grey': [0, 0, 50]}


def get_nodes():
    domains = ["communication", "music"]
    grid_sizes = [4, 8]
    drum_kits = ["snare+kick", "hihat+snare+kick"]
    blocks = [(d, g, k) for d in domains for g in grid_sizes for k in drum_kits]

    nodes = [
        StaticNode(
            definition={"color": color,
                        "domain": d,
                        "grid_size": g,
                        "drum_kit": k},
            block=f"{d}_{g}_{k}"
        )
        for color in ["yellow", "orange", "green", "blue", "purple", "pink", "red", "brown", "grey" ]
        for (d, g, k) in blocks
    ]
    return nodes


class ColorTrial(StaticTrial):
    time_estimate = 10

    def show_trial(self, experiment, participant):
        current_color = self.definition.get("color")

        if self.definition["domain"] == "communication":
            color_hsl = get_color_dict().get(current_color)

            return join(
                ModularPage(
                "director-task-communication",
                    Prompt(
                        Markup("<div style='text-align:center;'>Create a rhythm to have someone else guess this color</div><br>"),
                        text_align="center"),
                    ColorCubeControl(color_hsl, self.definition["drum_kit"], self.definition["grid_size"]),
                    time_estimate=self.time_estimate,
                    save_answer="last_action"
                )
            )
        else:
            return join(
                ModularPage(
                "director-task-music",
                    Prompt(
                        Markup("<div style='text-align:center;'>Create an appealing rhythm.</div><br>"),
                        text_align="center"
                    ),
                    DrumMachineControl(self.definition["drum_kit"], self.definition["grid_size"]),
                    time_estimate=self.time_estimate,
                    save_answer="last_action"
                        )
                    )

class ColorTrialMaker(StaticTrialMaker):
    def performance_check(self, experiment, participant, participant_trials):
        """Should return a dict: {"score": float, "passed": bool}"""
        score = 0
        failed = False
        for trial in participant_trials:
            if trial.answer == "Not at all":
                failed = True
            else:
                score += 1
        return {"score": score, "passed": not failed}

    def compute_performance_reward(self, score, passed):
        # At the end of the trial maker, we give the participant 1 dollar for each point.
        # This is combined with their trial-level performance reward to give their overall performance reward.
        return 1.0 * score

    give_end_feedback_passed = True

    def get_end_feedback_passed_page(self, score):
        return InfoPage(
            Markup(f"You finished the color questions! Your score was {score}."),
            time_estimate=5,
        )


color_trial_maker = ColorTrialMaker(
    id_="colors",
    trial_class=ColorTrial,
    nodes=get_nodes,
    expected_trials_per_participant=9,
    max_trials_per_participant=9,
    max_trials_per_block=9,
    allow_repeated_nodes=False,
    balance_across_nodes=False,
    check_performance_at_end=False,
    check_performance_every_trial=False,
    target_n_participants=1,
    target_trials_per_node=None,
    recruit_mode="n_participants",
    n_repeat_trials=0,
)

def requirements():
    html = tags.div()
    with html:
        tags.h1("Experiment structure")
        tags.p(
            "Before starting the experiment, here is the structure of the experiment so you know what to expect:"
        )
        tags.p(
            "1. Three short pretests",
            tags.br(),
            "2. The main experiment: rhythm creation",
            tags.br(),
            "3. A short exit questionnaire"
        )
        tags.p(
            " "
        )
        tags.p(
            "For the duration of the experiment please sit in a quiet place with a good internet connection. You need to be able to hear sounds. The experiment will take approximately 15 minutes."
        )
        tags.p(
            "If you satisfy these requirements, please press 'Next' to begin the experiment. Thank you for taking part in our experiment! If you are not able to satisfy these requirements currently, please exit the experiment."
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


class Exp(psynet.experiment.Experiment):
    label = "Signal Space Experiment"
    initial_recruitment_size = 1

    timeline = Timeline(
        CustomConsent(),
        PageMaker(requirements, time_estimate=60),
        CustomColorBlindnessTest(
             label="color_blindness_test",
             performance_threshold=1,  # Participants can make 1 mistake
             time_estimate_per_trial=5.0,
             hide_after=3.0,  # Image disappears after 3 seconds
        ),
        CustomAudioForcedChoiceTest(
             csv_path="cats_dogs_birds.csv",
             answer_options=["cat", "dog", "bird"],
             performance_threshold=1,  # Participants can make 1 mistake
             instructions="""
                 <p>This test helps us ensure you can properly hear and classify audio stimuli.</p>
                 <p>In each trial, you will hear a sound of an animal. Which animal does this sound come from?</p>
                 """,
             question="Select the category which fits best to the played sound file.",
             label="audio_forced_choice_test",
             time_estimate_per_trial=8.0,
             n_stimuli_to_use=3  # Use 3 random stimuli from the CSV
        ),
        dat(),
        color_trial_maker,
        questionnaire(),
        debrief_and_feedback(),
        redirect_to_prolific(),
        SuccessfulEndPage(),
    )