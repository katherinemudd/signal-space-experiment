# pylint: disable=unused-import,abstract-method

import logging
import random

from markupsafe import Markup

import psynet.experiment
from psynet.modular_page import KeyboardPushButtonControl, ModularPage
from psynet.page import InfoPage
from psynet.timeline import Timeline
from psynet.trial.static import StaticNetwork, StaticNode, StaticTrial, StaticTrialMaker

from psynet.modular_page import Control, Prompt
from psynet.timeline import join

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
    domains = ["communication"]
    grid_sizes = [4, 8]
    drum_kits = ["snare+kick", "hihat+snare+kick"]
    blocks = [(d, g, k) for d in domains for g in grid_sizes for k in drum_kits]

    nodes = [
        StaticNode(
            definition={"color": color,
                        "drum": d,
                        "grid_size": g,
                        "drum_kit": k},
            block=f"{d}_{g}_{k}"
        )
        for color in ["yellow", "orange", "green", "blue", "purple", "pink", "red", "brown", "grey" ]
        for (d, g, k) in blocks
    ]
    return nodes


class ColorTrial(StaticTrial):
    time_estimate = 5

    def show_trial(self, experiment, participant):
        current_color = self.definition.get("color")
        color_hsl = get_color_dict().get(current_color)

        return join(ModularPage(
            "director-task",
            Prompt(
                Markup("<div style='text-align:center;'>Make a rhythm to have someone else guess this color</div><br>"),
                text_align="center"),
            ColorCubeControl(color_hsl, self.definition["drum_kit"], self.definition["grid_size"]),
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


trial_maker = ColorTrialMaker(
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


class Exp(psynet.experiment.Experiment):
    label = "Static experiment demo"
    initial_recruitment_size = 1

    timeline = Timeline(
        trial_maker,
    )