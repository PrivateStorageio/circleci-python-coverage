let
  sources = import ./nix/sources.nix;
in
{ pkgs ? import sources.nixpkgs { }
, pypiData ? sources.pypi-deps-db
, python ? "python39"
, mach-nix ? import sources.mach-nix { inherit pkgs pypiData python; }
}:
let
  pkg = mach-nix.buildPythonPackage {
    python = "python39";
    src = ./.;
    pname = "circleci-python-coverage";
    version = "2022.05.13";
    requirements = ''
    setuptools
    '';
  };

  python = mach-nix.mkPython {
    python = "python39";
    requirements = ''
      coverage
      coverage_enable_subprocess
      slipcover
    '';
    packagesExtra = [ pkg ];
  };

  tests = pkgs.runCommand "circleci-python-coverage" {
  } ''
    set -x
    ${python}/bin/python -m coverage run --debug=config -m unittest discover --verbose circleci_python_coverage.tests
    SOURCE=$(${python}/bin/python -c 'import circleci_python_coverage; print(circleci_python_coverage.__file__.rsplit("/", 1)[0])')
    ${python}/bin/python -m slipcover --source $SOURCE --json --pretty-print --out slipcover.json -m unittest discover --verbose circleci_python_coverage.tests

    mkdir $out
    mv .coverage* slipcover.json $out/
  '';
in
{
  inherit pkg tests;
}
