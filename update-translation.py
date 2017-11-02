#!/usr/bin/python2

from subprocess import call

from os import (
    walk,
    makedirs
)
from os.path import (
    dirname,
    join,
    isdir,
    isfile,
)
from re import compile

locale_files = []

ml_pattern = compile(" mlget +as +_[, \n]")

root_dir = dirname(__file__)
root_prefix_len = len(root_dir) + 1

for root, dirs, files in walk(root_dir):
    for file in files:
        if file[-3:] != ".py":
            continue

        file_name = join(root, file)
        f = open(file_name, "rb")
        lines = list(f.readlines())
        f.close()

        for line in lines:
            if ml_pattern.search(line):
                break
        else:
            continue

        locale_files.append(file_name[root_prefix_len:])

locale_files.sort()

langs = [
    "ru_RU"
]

print("Updating *.po file by those files:")
for f in locale_files:
    print("    " + f)
print("...")

for l in langs:
    directory = join("locale", l, "LC_MESSAGES")
    if not isdir(directory):
        makedirs(directory)

    call(
        [   "xgettext",
            "-o", join(directory, "messages.po"),
        ] + locale_files
    )

    if isfile(join(directory, "qdc.po")):
        call(
            [   "msgmerge",
                "-U",
                "-N", join(directory, "qdc.po"),
                join(directory,"messages.po")
            ]
        )
        call(
            [   "rm",
                join(directory, "messages.po")
            ]
        )
    else:
        call(
            [   "mv",
                join(directory, "messages.po"),
                join(directory, "qdc.po")
            ]
        )

    call(
        [
            "msgfmt",
            "-o", join(directory, "qdc.mo"),
            join(directory, "qdc.po")
        ]
    )
