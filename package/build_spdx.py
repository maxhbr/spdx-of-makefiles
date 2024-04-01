import re
import os
import sys
import csv
import json
import logging
import datetime
import subprocess
import multiprocessing
from collections import defaultdict

class SPDXBuilderConfig:
    def __init__(self, src_dir, out_dir):
        self.src_dir = src_dir
        self.out_dir = out_dir


class SPDXBuilder:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('SPDXBuilder')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())


def main():
    src_dir = sys.argv[1]
    out_dir = sys.argv[2]
    config = SPDXBuilderConfig(src_dir, out_dir)
    builder = SPDXBuilder(config)
    builder.build_spdx()
