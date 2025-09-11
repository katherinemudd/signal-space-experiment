from psynet.page import InfoPage
from markupsafe import Markup

def video_wait_page():
    """InfoPage with embedded YouTube video and custom barrier polling"""
    return InfoPage(
        Markup("""
        <div style='text-align: center; margin: 20px;'>
            <h3>Waiting for your partner...</h3>
            <p>Please watch this video while you wait:</p>
            <div style='margin: 20px 0;'>
                <iframe width="560" height="315" 
                        src="https://www.youtube.com/embed/L913rOIhWYo?autoplay=1&mute=1" 
                        title="YouTube video player" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen>
                </iframe>
            </div>
            <p><em>This page will automatically advance when your partner is ready.</em></p>
        </div>
        """),
        time_estimate=30,
        show_next_button=False,
        scripts=[
            """
            <script>
            function checkCanLeave() {
                if (!psynet.pageLoaded) {
                    return;
                }
                canLeave().then((canLeaveResult) => {
                    if (canLeaveResult) {
                        psynet.nextPage();
                    }
                });
            }

            function canLeave() {
                let route = "/participant_in_barrier/" + psynet.participantId;
                return dallinger.get(route).then((resp) => {
                    let participant_in_barrier = resp.result;
                    return !participant_in_barrier;
                });
            }

            setInterval(checkCanLeave, 1000);
            </script>
            """
        ]
    )