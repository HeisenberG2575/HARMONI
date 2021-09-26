#!/usr/bin/env python3
##############################################################################
# Imports
##############################################################################

import argparse
import functools
from py_trees.blackboard import Blackboard
from py_trees.idioms import either_or
import py_trees
import time
import subprocess
import py_trees.console as console
import os
from harmoni_pytree import either_custom
from harmoni_pytree import visual_bg
from harmoni_pytree import interaction_bg 
from harmoni_pytree import mainactivity
from harmoni_pytree import on_modules
from harmoni_pytree import therapist

##############################################################################
# Classes
##############################################################################


def description(root):
    content = "\n\n"
    content += "\n"
    content += "EVENTS\n"
    if py_trees.console.has_colours:
        banner_line = console.green + "*" * 79 + "\n" + console.reset
        s = "\n"
        s += banner_line
        s += console.bold_white + "Session".center(79) + "\n" + console.reset
        s += banner_line
        s += "\n"
        s += content
        s += "\n"
        s += banner_line
    else:
        s = content
    return s


def epilog():
    if py_trees.console.has_colours:
        return console.cyan + "And his noodly appendage reached forth to tickle the blessed...\n" + console.reset
    else:
        return None


def command_line_argument_parser():
    parser = argparse.ArgumentParser(description=description(create_root()),
                                     epilog=epilog(),
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-r', '--render', action='store_true', help='render dot tree to file')
    group.add_argument('-i', '--interactive', action='store_true', help='pause and wait for keypress at each tick')
    return parser


def pre_tick_handler(behaviour_tree):
    print("\n--------- Run %s ---------\n" % behaviour_tree.count)


def post_tick_handler(snapshot_visitor, behaviour_tree):
    print(
        "\n" + py_trees.display.unicode_tree(
            root=behaviour_tree.root,
            visited=snapshot_visitor.visited,
            previously_visited=snapshot_visitor.previously_visited
        )
    )
    print(py_trees.display.unicode_blackboard())


def create_root(name = "Session"):
    root = py_trees.composites.Selector(name = name,memory=False)

    therapist = therapist.create_root()

    on_module = on_module.create_root()

    inverter_camera = py_trees.decorators.Inverter(name="InverterCamera",child=on_module)

    mainactivity = mainactivity.create_root()

    inverter_mainactivity = py_trees.decorators.Inverter(name="InverterMainActivity",child=mainactivity)

    visual_bg = visual_bg.create_root()

    visual_bg_inverter = py_trees.decorators.Inverter(name="VisualBgInverter",child=visual_bg)

    interaction_bg = interaction_bg.create_root()

    interaction_bg_inverter = py_trees.decorators.Inverter(name="InverterNonMiParli",child=interaction_bg)

    root.add_children([therapist ,inverter_camera, visual_bg_inverter, interaction_bg_inverter, inverter_mainactivity])

    return root

##############################################################################
# Main
##############################################################################

def main():
    """
    Entry point for the demo script.
    """
    args = command_line_argument_parser().parse_args()
    py_trees.logging.level = py_trees.logging.Level.DEBUG
    root = create_root()
    print(description(root))

    ####################
    # Rendering
    ####################
    if args.render:
        print("**************START RENDERING**************")
        target_directory = os.path.join(os.getcwd(), "dot_folder/")
        py_trees.display.render_dot_tree(root = root,target_directory = target_directory)
        if py_trees.utilities.which("xdot"):
            try:
                subprocess.call(["xdot", target_directory+"%s.dot" % root.name])
            except KeyboardInterrupt:
                pass
        else:
            print("")
            console.logerror("No xdot viewer found, skipping display [hint: sudo apt install xdot]")
            print("")
        print("**************END RENDERING**************")
        
    ####################
    # Tree Stewardship
    ####################
    behaviour_tree = py_trees.trees.BehaviourTree(root)
    behaviour_tree.add_pre_tick_handler(pre_tick_handler)
    behaviour_tree.visitors.append(py_trees.visitors.DebugVisitor())
    snapshot_visitor = py_trees.visitors.SnapshotVisitor()
    behaviour_tree.add_post_tick_handler(functools.partial(post_tick_handler, snapshot_visitor))
    behaviour_tree.visitors.append(snapshot_visitor)
    behaviour_tree.setup(timeout=15)

    ####################
    # Tick Tock
    ####################

    if args.interactive:
        py_trees.console.read_single_keypress()
    for unused_i in range(1, 12):
        try:
            behaviour_tree.tick()
            if args.interactive:
                py_trees.console.read_single_keypress()
            else:
                time.sleep(0.5)
        except KeyboardInterrupt:
            break
    print("\n")


if __name__ == "__main__":
    main()