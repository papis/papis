{
  description = "Papis - Powerful command-line document and bibliography manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix.url = "github:nix-community/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    pyproject-nix,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3.override {
        packageOverrides = self: super: {
          arxiv = arxiv;
          python-coveralls = python-coveralls;
          types-pygments = types-pygments;
          types-python-slugify = types-python-slugify;
          sphinx-click = sphinx-click;
        };
      };
      pypkgs = pkgs.python3Packages;
      project = pyproject-nix.lib.project.loadPyproject {
        projectRoot = ./.;
      };

      arxiv = python.pkgs.buildPythonPackage rec {
        pname = "arxiv";
        version = "2.1.0";

        src = python.pkgs.fetchPypi {
          inherit pname version;
          sha256 = "sha256-60sdWrnf1mAnw0S7MkwgviHVb+FfbOIW7VsgnfdH3qg=";
        };

        doCheck = false;
        checkInputs = [];
        propagatedBuildInputs = [pypkgs.feedparser];

        meta = with pkgs.lib; {
          homepage = "https://github.com/lukasschwab/arxiv.py";
          description = "Python wrapper for the arXiv API";
          license = licenses.mit;
        };
      };

      python-coveralls = python.pkgs.buildPythonPackage rec {
        pname = "python-coveralls";
        version = "2.9.3";

        src = python.pkgs.fetchPypi {
          inherit pname version;
          sha256 = "sha256-v694EefcVijoO2sWKWKk4khdv/GEsw5J84A3TtG87lU=";
        };

        doCheck = false;
        checkInputs = [];

        meta = with pkgs.lib; {
          homepage = "http://github.com/z4r/python-coveralls";
          description = "Python interface to coveralls.io API ";
          license = licenses.asl20;
        };
      };

      types-pygments = python.pkgs.buildPythonPackage rec {
        pname = "types-Pygments";
        version = "2.17.0.20240310";

        src = python.pkgs.fetchPypi {
          inherit pname version;
          sha256 = "sha256-sdl+kFzjY0PHKDsDGRgq5tT5ZxiPNh9FUCoYrkPgPh8=";
        };

        doCheck = false;
        checkInputs = [];

        meta = with pkgs.lib; {
          homepage = "https://github.com/python/typeshed";
          description = "Typing stubs for Pygments";
          license = licenses.asl20;
        };
      };

      types-python-slugify = python.pkgs.buildPythonPackage rec {
        pname = "types-python-slugify";
        version = "8.0.2.20240310";

        src = python.pkgs.fetchPypi {
          inherit pname version;
          sha256 = "sha256-UVe1CMf+1YdSDHDXf2KuoPr9xmIIk8LsiXLxOh+vVWA=";
        };

        doCheck = false;
        checkInputs = [];

        meta = with pkgs.lib; {
          homepage = "https://github.com/python/typeshed";
          description = "Typing stubs for python-slugify";
          license = licenses.asl20;
        };
      };

      sphinx-click = python.pkgs.buildPythonPackage rec {
        pname = "sphinx-click";
        version = "5.1.0";

        src = python.pkgs.fetchPypi {
          inherit pname version;
          sha256 = "sha256-aBLC22LT+ucaSt2+WooKFsl+tJHzzWP+NLTtfgcjbzM=";
        };

        doCheck = false;
        checkInputs = [];
        propagatedBuildInputs = [pypkgs.pbr];

        meta = with pkgs.lib; {
          homepage = "https://github.com/click-contrib/sphinx-click";
          description = "Sphinx extension that automatically documents click applications";
          license = licenses.mit;
        };
      };
    in {
      packages = {
        papis = let
          # Returns an attribute set that can be passed to `buildPythonPackage`.
          attrs = project.renderers.buildPythonPackage {
            inherit python;
            extras = ["optional"];
          };
        in
          # Pass attributes to buildPythonPackage.
          # Here is a good spot to add on any missing or custom attributes.
          python.pkgs.buildPythonPackage (attrs
            // {
              # Because we're following main, use the git rev as version
              version =
                if (self ? rev)
                then self.shortRev
                else self.dirtyShortRev;
            });
        default = self.packages.${system}.papis;
      };
      devShells = {
        default = let
          # Returns a function that can be passed to `python.withPackages`
          arg = project.renderers.withPackages {
            inherit python;
            extras = ["develop" "docs" "lsp" "optional"];
          };

          # Returns a wrapped environment (virtualenv like) with all our packages
          pythonEnv = python.withPackages arg;

          # used in below scripts to check if docker or podman is available
          check-container-cmd =
            # bash
            ''
              if command -v podman &> /dev/null
              then
                  container_cmd="podman"
              elif command -v docker &> /dev/null
              then
                  container_cmd="docker"
              else
                  echo "Neither Podman or Docker could be found. Aborting..."
                  exit 1
              fi
            '';

          # convenience command to build a Papis container with docker/podman
          papis-build-container = pkgs.writeShellApplication {
            name = "papis-build-container";
            text =
              check-container-cmd
              +
              # bash
              ''
                "$container_cmd" build -t papisdev .
              '';
          };

          # convenience command to run containerised tests
          papis-run-container-tests = pkgs.writeShellApplication {
            name = "papis-run-container-tests";
            text =
              check-container-cmd
              +
              # bash
              ''
                "$container_cmd" run -v "$(pwd)":/papis --rm -it papisdev
              '';
          };

          # convenience command to enter a container with a populated test library
          papis-run-container-interactive = pkgs.writeShellApplication {
            name = "papis-run-container-interactive";
            text =
              check-container-cmd
              +
              # bash
              ''
                populateLibPy=$(cat << END
                import papis.testing
                papis.testing.populate_library('/root/Documents/papers')
                END
                )
                entryCmd="python -c \"$populateLibPy\"; bash"

                "$container_cmd" run -v "$(pwd)":/papis --rm -it papisdev bash -c "$entryCmd"
              '';
          };
        in
          # Create a devShell like normal.
          pkgs.mkShell {
            packages = [
              self.packages.${system}.papis
              pythonEnv
              papis-build-container
              papis-run-container-tests
              papis-run-container-interactive
            ];
            shellHook = ''
              export PYTHONPATH="$(pwd):$PYTHONPATH"
            '';
          };
      };
    });
}
