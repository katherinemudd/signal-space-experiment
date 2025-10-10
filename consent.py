from dominate.tags import div, p, span, h1, strong, ul, li, em, img

from psynet.consent import NoConsent
from psynet.modular_page import ModularPage, CheckboxControl
from psynet.page import InfoPage
from psynet.timeline import Module, join

information_and_consent = div()

with information_and_consent:
    div(
        h1("Information sheet", style="display: inline-block; margin: 0;"),
        img(src="static/figs/sbu_logo.jpeg", alt="Stony Brook University Logo", style="max-width: 200px; margin: 10px 0; float: right;"),
        style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;"
    )
    p(strong("Project title:  Dynamics of creative exploration", style="text-decoration: underline;"))
    p(
        """
        You are being asked to be in a research study. The purpose of the study is to understand how creativity interacts with using a signal space in the domains of music and communication. 
        """,
        style="clear: both;"
    )
    p(
        """
        If you agree to participate, your part will be to be paired up with a partner: you will either have the role of creating sounds on the drum machine or giving feedback on the sounds created by your partner. This will continue over 9 rounds. Finally, you will be asked to answer a short questionnaire about your personal musical abilities and language experience. The amount of time spent in the study is approximately 30 minutes.
        """
    )
    p(
        """
        All the information about you will be kept private. All the study data that we get from you will be kept secure. If any papers and talks are given about this research, your name will not be used. The information collected during your participation (without any identifiers) may be used for future research studies or distributed to another investigator for future research studies.
        """
    )
    p(
        """
        There are no foreseeable risks or benefits to you for participating in the study.
        """
    )
    p(
        """
        You will not be paid for letting us use your records. You will be paid the equivalent of 16 USD per hour (as set by Prolific Academic, paid based on the amount of time taken in the study) for completing the experiment and questionnaire.
        """
    )
    p(
        """
        Your participation is completely voluntary. You do not have to participate if you don't want to. Refusal to participate will not involve any penalties or loss of benefits to which you are entitled. You can also discontinue your participation at any time without penalty or loss of benefits to which you are entitled.
        """
    )
    p(
        """
        If you have any questions, concerns or complaints about the study, you may contact the Principal Investigator, Margaret Schedel, by telephone (631)-632 7330, or by email at margaret.schedel@stonybrook.edu. If you have any questions about your rights as a research subject or if you would like to obtain information or offer input, you may contact the Stony Brook University Research Subject Advocate, Ms. Lu-Ann Kozlowski, BSN, RN, (631) 632-9036, or by e-mail, lu-ann.kozlowski@stonybrook.edu.
        """
    )
    p(
        """
        If you participate in the experiment and questionnaire it means that you have read (or had to read to you) the information in this information sheet, and would like to be a participant. 
        """
    )
    p(
        """
         By clicking onto the next page, you confirm that you give your full informed consent.
        """
    )


def consent():
    return Module(
        "consent",
        join(
            NoConsent(),
            InfoPage(information_and_consent, time_estimate=60),
        )
    )