import psynet.experiment
from psynet.modular_page import ModularPage, SurveyJSControl, Prompt
from psynet.page import DebugResponsePage, InfoPage
from psynet.timeline import Timeline, join
from dominate.tags import div, p, span, h1, strong, ul, li, em


def questionnaire():
    return join(
        InfoPage(
            div(
                h1("Exit questionnaire"),
                p("Please complete the following questions about your experience and background.")
            ),
            time_estimate=5
        ),
        ModularPage(
            "other questions",
            Prompt(
                "Please rate the following statements",
                text_align="center"
            ),
            SurveyJSControl(
                {
                    "logoPosition": "right",
                    "requiredText": "",
                    "pages": [
                        {
                            "name": "leapq_page",
                            "elements": [
                                {
                                    "type": "rating",
                                    "name": "creativity",
                                    "title": "I consider myself to be creative",
                                    "rateValues": [
                                        {"value": "1", "text": "1"},
                                        {"value": "2", "text": "2"},
                                        {"value": "3", "text": "3"},
                                        {"value": "4", "text": "4"},
                                        {"value": "5", "text": "5"},
                                        {"value": "6", "text": "6"},
                                        {"value": "7", "text": "7"}
                                    ],
                                    "minRateDescription": "Disagree",
                                    "maxRateDescription": "Agree",
                                    "isRequired": True,
                                },
                                {
                                    "type": "rating",
                                    "name": "musical_ability",
                                    "title": "I consider myself to have strong musical ability",
                                    "rateValues": [
                                        {"value": "1", "text": "1"},
                                        {"value": "2", "text": "2"},
                                        {"value": "3", "text": "3"},
                                        {"value": "4", "text": "4"},
                                        {"value": "5", "text": "5"},
                                        {"value": "6", "text": "6"},
                                        {"value": "7", "text": "7"}
                                    ],
                                    "minRateDescription": "Disagree",
                                    "maxRateDescription": "Agree",
                                    "isRequired": True,
                                }
                            ],
                        },
                    ],
                },
            ),
            time_estimate=5,
        ),
        ModularPage(
            "language experience",
            Prompt(
                "Please answer the following questions about your language background.",
                text_align="center"
            ),
            SurveyJSControl(
                {
                    "logoPosition": "right",
                    "requiredText": "",
                    "pages": [
                        {
                            "name": "leapq_page",
                            "elements": [
                                {
                                    "type": "panel",
                                    "name": "dominance_order_panel",
                                    "title": "1. Please list all the languages you speak, in order of proficiency (most fluent to least fluent):",
                                    "elements": [
                                        {"type": "text", "name": "language_1", "title": "Language 1",  "isRequired": True},
                                        {"type": "text", "name": "language_2", "title": "Language 2"},
                                        {"type": "text", "name": "language_3", "title": "Language 3"},
                                        {"type": "text", "name": "language_4", "title": "Language 4"},
                                        {"type": "text", "name": "language_5", "title": "Language 5"}
                                    ]
                                },
                                # {
                                #     "type": "html",
                                #     "name": "impairments_label",
                                #     "html": "Have you ever had (check all applicable):"
                                # },
                                # {
                                #     "type": "checkbox",
                                #     "name": "impairments",
                                #     "title": "",
                                #     "choices": [
                                #         "a language disability",
                                #         "a learning disability"
                                #     ],
                                #     "isRequired": False
                                # },
                                # {
                                #     "type": "comment",
                                #     "name": "explanation",
                                #     "title": "If yes to either, please explain (including any corrections):",
                                #     "isRequired": False
                                # },
                            ],
                        },
                    ],
                },
            ),
            time_estimate=5,
        ),
    )
