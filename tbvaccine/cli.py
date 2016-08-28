import argparse
import sys

from tbvaccine import __version__
from tbvaccine import TBVaccine


def main():
    parser = argparse.ArgumentParser(description="Upload a file to Pastery, the "
                                     " best pastebin in the world.")
    parser.add_argument("-d", "--dir", metavar="dir", type=str, default="", nargs="?",
                        help="the directory of the code to highlight in the traceback [default: current dir]")
    parser.add_argument("-i", "--dont-isolate", action="store_false",
                        help="highlight all lines, not just the ones in the code directory")
    parser.add_argument("-V", "--version", action="store_true",
                        help="show the version and quit")

    args = parser.parse_args()

    if args.version:
        sys.exit("TBVaccine, version %s." % __version__)

    tbv = TBVaccine(
        code_dir=args.dir,
        isolate=args.dont_isolate,
    )

    for line in iter(sys.stdin.readline, ''):
        output = tbv.process_line(line)
        sys.stderr.write(output)


if __name__ == "__main__":
    main()
