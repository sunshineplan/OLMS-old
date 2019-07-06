#!/usr/bin/env python3

import os
from glob import glob

filelist = glob('OLMS/templates/**/*.html', recursive=True)

with open('translation.txt', encoding='utf8') as f:
    translation=f.readlines()
    translation = [tuple(i.rstrip('\n').split('=')) for i in translation]

def safe_open(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'w', encoding='utf8')

for file in filelist:
    with open(file, encoding='utf8') as f:
        content = f.read()
        for i in translation:
            content = content.replace(i[0], i[1])
    with safe_open(file.replace('templates', 'templates-zh')) as f:
        f.write(content)
