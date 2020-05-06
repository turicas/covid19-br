import argparse

from spiders import run_state_spider


parser = argparse.ArgumentParser()
parser.add_argument("state")
args = parser.parse_args()

run_state_spider(args.state, subprocess=False)
