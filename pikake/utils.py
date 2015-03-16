#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess

def get_ips():
    ips = []
    s = subprocess.Popen("/sbin/ip a",
                         shell=True, stdout=subprocess.PIPE)
    for line in s.stdout.readlines():
        line = line.strip()
        match = re.search(b"inet ([0-9.]*)/[0-9]* ", line)
        if match is not None:
            ips.append(match.group(1).decode())
    return ips


