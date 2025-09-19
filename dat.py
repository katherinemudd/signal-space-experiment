from dominate.tags import div, p, span, h1, strong, ul, li, em

import psynet.experiment
from psynet.modular_page import ModularPage, SurveyJSControl, Prompt
from psynet.page import DebugResponsePage
from psynet.timeline import Timeline, join


def dat():
    return ModularPage(
        "DAT",
        Prompt(
            "Please list 10 nouns that are as different from each other as possible in all meanings and uses of the words.",
            text_align="center"
        ),
        SurveyJSControl(
            {
                "requiredText": "",
                "logoPosition": "right",
                "pages": [
                    {
                        "name": "page1",
                        "elements": [
                            {
                                "type": "text",
                                "name": "noun_1",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_2",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_3",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_4",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_5",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_6",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_7",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_8",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_9",
                                "title": " ",
                                "isRequired": True
                            },
                            {
                                "type": "text",
                                "name": "noun_10",
                                "title": " ",
                                "isRequired": True
                            },
                        ],
                    },
                ],
            },
        ),
        time_estimate=60
    )
