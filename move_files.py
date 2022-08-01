import os
import shutil
import re


if __name__ == '__main__':
    file_names = os.listdir("../data/data")
    pattern_string = "AGC\d+_M\d+_file\d+.fits"
    p = re.compile(pattern_string)

    for name in file_names:
        if p.match(name):
            abs_path = os.path.join("../data/data", name)
            shutil.move(abs_path, "data/beams")