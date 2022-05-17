from sys import argv
from re import compile, Pattern
from fnmatch import fnmatch, translate
from functools import partial
from pathlib import Path
from typing import Iterator, Callable
from json import load
from base64 import b64encode
from hashlib import md5
from configparser import ConfigParser

def main(workspace: str, output: str) -> None:
    fix_path = path_fixer_from_configuration()

    workspace_dir = Path(workspace)
    output_dir = Path(output)
    for child in workspace_dir.glob("*.slipcover+json"):
        with child.open() as infile:
            output_path = output_dir / (child.stem + ".lcov")
            with output_path.open("w") as outfile:
                print(f"writing converted {child} to {output_path}")
                slipcover2lcov(infile, outfile, fix_path)


def glob_to_matching_pattern(glob: str) -> Pattern:
    # Obviously not a general translation from glob to regex ... but works
    # well enough for the paths we have to deal with at the moment.
    bare_pattern = glob.replace(".", "\\.").replace("*", ".*").replace("\\", "\\\\")
    grouped_pattern = f"{bare_pattern}(?P<relative>.*)"
    return compile(grouped_pattern)


def path_fixer_from_configuration() -> Callable[[str], str]:
    p = ConfigParser()
    with open(".coveragerc") as cfg:
        p.read_file(cfg)

    source = p.get("paths", "source")
    paths = source.split()
    canonical = paths.pop(0)
    prefix_patterns = [glob_to_matching_pattern(glob) for glob in paths]
    return partial(make_relative_name, prefix_patterns, canonical)


def make_relative_name(prefix_patterns: list[Pattern], make_relative_to: str, filename: str) -> str:
    for prefix_pattern in prefix_patterns:
        match = prefix_pattern.match(filename)
        if match is not None:
            # XXX Windows dirsep sometimes
            return make_relative_to + match.group("relative").replace("\\", "/")
    return filename


def slipcover2lcov(infile, outfile, transform_filename) -> None:
    # slipcover data looks like
    # {"files": {"filename": {"executed_lines": [ints], "missing_lines": [ints]}}}
    #
    # lcov data looks like
    #
    # TN:
    # SF:<source file>
    # DA:<int - line number>,<int - times executed>,<str - base64 encoded md5 hashed line>
    # LF:<int - number of statements>
    # LH:<int - number of executed statements>
    # BRDA:<int - uncovered branch line number>,<int - block number>,<int - branch number>,-
    # BRDA:<int - covered line number>,<int - block number>,<int - branch number>,1
    # BRF:<int - some kind of branch stat sum>
    # BRH:<int - some other kind of branch stat sum>
    # end_of_record
    # <repeat>
    slipcover_data = load(infile)
    for filename, info in slipcover_data["files"].items():
        outfile.writelines(one_lcov_entry(transform_filename(filename), info))


def one_lcov_entry(filename: str, info: dict) -> Iterator[str]:
    with open(filename) as source:
        lines = source.read().splitlines()

    yield "TN:\n"
    yield f"SF:{filename}\n"
    executed_lines = info["executed_lines"]
    missing_lines = info["missing_lines"]
    for lineno in executed_lines:
        try:
            src = lines[lineno - 1]
        except IndexError:
            src = f"<missing:{lineno}>"
        yield f"DA:{lineno},1,{digest_line(src)}\n"
    for lineno in missing_lines:
        try:
            src = lines[lineno - 1]
        except IndexError:
            src = f"<missing:{lineno}>"
        yield f"DA:{lineno},0,{digest_line(src)}\n"
    yield f"LF:{len(executed_lines) + len(missing_lines)}\n"
    yield f"LF:{len(executed_lines)}\n"

    # slipcover doesn't have branch coverage information I suppose
    # and I dunno what those trailing aggregate stats are

    yield "end_of_record\n"


def digest_line(source: str) -> str:
    digest = md5()
    digest.update(source.encode("utf-8"))
    return b64encode(digest.digest()).decode("ascii").rstrip("=")

if __name__ == "__main__":
    main(*argv[1:])
