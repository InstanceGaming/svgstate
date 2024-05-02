import os
import time
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from utils import fix_path


def get_cla():
    ap = ArgumentParser(description='Export all from svg files in parallel.')
    ap.add_argument('-f', '--format',
                    default='png',
                    dest='export_format')
    ap.add_argument('-I', '--inkscape',
                    type=str,
                    default='inkscape',
                    dest='inkscape_path')
    ap.add_argument('-w', '--working-dir',
                    type=fix_path,
                    dest='working_dir')
    ap.add_argument(type=Path,
                    dest='svg_dir')
    return ap.parse_args()


def parallel(working_dir, inkscape_path, svg_files, export_format):
    processes = set()
    
    for name in svg_files:
        cla = (inkscape_path, f'--actions=export-type:{export_format};export-do;', name)
        processes.add(subprocess.Popen(cla, cwd=working_dir))
    
    while len(processes) >= os.cpu_count():
        time.sleep(0.1)
        processes.difference_update([p for p in processes if p.poll() is not None])


def run():
    cla = get_cla()
    svg_dir: Path = cla.svg_dir
    export_format = cla.export_format
    inkscape_path = cla.inkscape_path
    working_dir: Path | None = cla.working_dir or svg_dir
    
    if not svg_dir.is_dir():
        print('svg_dir not a directory')
        exit(2)
    
    if working_dir and not working_dir.is_dir():
        print('working_dir not a directory')
        exit(3)
    
    svg_files = set()
    for file in os.listdir(svg_dir):
        if file.endswith('.svg'):
            svg_files.add(file)
    
    parallel(working_dir, inkscape_path, svg_files, export_format)


if __name__ == '__main__':
    run()
