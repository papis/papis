{
  description = "Papis - Powerful command-line document and bibliography manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3;
      pypkgs = pkgs.python3Packages;
      lib = pkgs.lib;

      runtime_py_deps = let
        # manually package arxiv.py since it is not yet in upstream nixpkgs
        arxivpy = python.pkgs.buildPythonPackage rec {
          pname = "arxiv";
          version = "1.4.8";

          src = python.pkgs.fetchPypi {
            inherit pname version;
            sha256 = "sha256-KoGOp0nqpipuJPwx1Tt2m00z/1XPxd2nx7fTCaOyk3M=";
          };

          doCheck = false;
          checkInputs = [ ];
          propagatedBuildInputs = [pypkgs.feedparser];

          meta = with lib; {
            homepage = "https://github.com/lukasschwab/arxiv.py";
            description = " Python wrapper for the arXiv API ";
            license = licenses.mit;
          };
        };
      in
        with pypkgs; [
          arxivpy
          beautifulsoup4
          bibtexparser
          chardet
          click
          colorama
          dominate
          filetype
          habanero
          isbnlib
          jinja2
          lxml
          prompt_toolkit
          pygments
          pyparsing
          python-doi
          python-slugify
          pyyaml
          requests
          stevedore
          tqdm
          whoosh
        ];
      develop_py_deps = with pypkgs; [
        pip
        virtualenv

        flake8-bugbear
        flake8
        mypy
        pep8-naming
        pylint
        pytest
        pytest-cov
        python-lsp-server
        sphinx_rtd_theme

        # not packaged
        # python-coveralls
        # sphinx-click
        # flake8-quotes
        # types-PyYAML
        # types-Pygments
        # types-beautifulsoup4
        # types-python-slugify
        # types-requests
        # types-tqdm
      ];

      buildf = isDevEnv:
        python.pkgs.buildPythonPackage rec {
          pname = "papis";
          version = "0.13";
          format = "setuptools";

          # disabled = pythonOlder "3.8";

          src = ./.;

          propagatedBuildInputs = runtime_py_deps ++ lib.optionals isDevEnv develop_py_deps;

          doCheck = false;
          checkInputs = with python.pkgs; [
            pytestCheckHook
          ];

          preCheck = ''
            export HOME=$(mktemp -d);
          '';

          pytestFlagsArray = [
            "papis tests"
          ];

          disabledTestPaths = [
            "tests/downloaders"
          ];

          disabledTests = [
            "get_document_url"
            "match"
            "test_doi_to_data"
            "test_downloader_getter"
            "test_general"
            "test_get_data"
            "test_validate_arxivid"
            "test_yaml"
            # ]
            # ++ lib.optionals stdenv.isDarwin [
            "test_default_opener"
          ];

          pythonImportsCheck = [
            "papis"
          ];

          meta = with pkgs.lib; {
            description = "Powerful command-line document and bibliography manager";
            homepage = "https://papis.readthedocs.io/";
            changelog = "https://github.com/papis/papis/blob/v${version}/CHANGELOG.md";
            license = licenses.gpl3Only;
          };
        };
    in {
      packages = {
        default = buildf false;
        papis = buildf false;
      };
      devShells = {
        default = pkgs.mkShell {
          buildInputs = with pkgs;
            [python]
            ++ []
            ++ runtime_py_deps
            ++ develop_py_deps;

          shellHook = ''
            python --version
            python -m venv .venv
            source .venv/bin/activate
            pip install -e ".[develop,optional]"
          '';
        };
      };
    });
}
