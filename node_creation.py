# https://pmcharrison.github.io/psynet-tutorial-ismir-2025/01-topics/05-static-experiments-i.html
from psynet.trial.static import StaticNode

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
    nodes = [
        StaticNode(
            definition={
                item_key: item,
                "attempts": 0,  # todo: remove, test
                "completed": False,  # todo: move to participant vars?
                "domain": domain,
                "grid_size": grid_size,
                "drum_kit": drum_kit,
                **({"matcher_choice": "add color"} if domain == "communication" else {})
            },
            #block=f'{domain}_{grid_size}_{drum_kit}',  # todo: not sure, maybe block instead otherwise?
        )
        for domain in ["communication", "music"]
        for grid_size in [4, 8]
        for drum_kit in ["snare+kick", "hihat+snare+kick"]
        for item in (list(get_color_dict().keys()))
        for item_key in (["color"] if domain == "communication" else ["melody"])
    ]
    return nodes


def get_testing_nodes():
    domain = "communication"
    grid_size = 4
    drum_kit = "hihat+snare+kick"
    #condition = "test"

    nodes = [
        StaticNode(
            definition={
                item_key: item,
                "attempts": 0,  # todo: change to participant vars
                "completed": False,  # todo: change to participant vars
                "domain": domain,
                "grid_size": 4,
                "drum_kit": "hihat+snare+kick",
                #"condition": condition,
                **({"matcher_choice": "add color"} if domain == "communication" else {})
            },
            block=f'{domain}_{grid_size}_{drum_kit}',
        )
        for item in (list(get_color_dict().keys()))
        for item_key in (["color"] if domain == "communication" else ["melody"])
    ]
    return nodes


# for checking nodes
#nodes = get_nodes()
#for i, node in enumerate(nodes):
#    print(f"Node {i+1}: {node.definition}")



