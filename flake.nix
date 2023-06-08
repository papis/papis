{
  description = "Papis - Powerful command-line document and bibliography manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python310;
      pypkgs = pkgs.python310Packages;
      lib = pkgs.lib;

      runtime_py_deps = with pypkgs; [
        pyyaml
        arxiv2bib
        beautifulsoup4
        bibtexparser
        chardet
        click
        colorama
        dominate
        filetype
        habanero
        isbnlib
        lxml
        prompt_toolkit
        pygments
        pyparsing
        python-doi
        python-slugify
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
            pip install -e .[develop,optional]
          '';
        };
      };
    });
}
