{
  description = "Papis - Powerful command-line document and bibliography manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix.url = "github:nix-community/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      pyproject-nix,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3.override {
          packageOverrides = final: prev: {

            flake8-pyproject = final.buildPythonPackage {
              pname = "flake8-pyproject";
              version = "1.2.3";
              pyproject = true;

              src = pkgs.fetchFromGitHub {
                owner = "john-hen";
                repo = "Flake8-pyproject";
                rev = "30b8444781d16edd54c11df08210a7c8fb79258d";
                hash = "sha256-bPRIj7tYmm6I9eo1ZjiibmpVmGcHctZSuTvnKX+raPg=";
              };

              doCheck = false;
              checkInputs = [ ];
              propagatedBuildInputs = [
                final.flit-core
                final.flake8
              ];

              meta = with pkgs.lib; {
                homepage = "https://github.com/john-hen/Flake8-pyproject";
                description = "Flake8 plug-in loading the configuration from pyproject.toml";
                license = licenses.mit;
              };
            };

            types-pygments = final.buildPythonPackage rec {
              pname = "types-Pygments";
              version = "2.19.0.20250305";

              src = final.fetchPypi {
                inherit version;
                pname = "types_pygments";
                sha256 = "sha256-BExQ6A7NQSjACnJo8gNV4W9cVUZtPUnf2gm+kgr0C0s=";
              };

              doCheck = false;
              checkInputs = [ ];

              meta = with pkgs.lib; {
                homepage = "https://github.com/python/typeshed";
                description = "Typing stubs for Pygments";
                license = licenses.asl20;
              };
            };

            types-python-slugify = final.buildPythonPackage rec {
              pname = "types-python-slugify";
              version = "8.0.2.20240310";

              src = final.fetchPypi {
                inherit pname version;
                sha256 = "sha256-UVe1CMf+1YdSDHDXf2KuoPr9xmIIk8LsiXLxOh+vVWA=";
              };

              doCheck = false;
              checkInputs = [ ];

              meta = with pkgs.lib; {
                homepage = "https://github.com/python/typeshed";
                description = "Typing stubs for python-slugify";
                license = licenses.asl20;
              };
            };
          };
        };

        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };

      in
      {
        packages = {
          papis =
            let
              # Returns an attribute set that can be passed to `buildPythonPackage`.
              attrs = project.renderers.buildPythonPackage {
                inherit python;
                extras = [ "optional" ];
              };
            in
            # Pass attributes to buildPythonPackage.
            # Here is a good spot to add on any missing or custom attributes.
            python.pkgs.buildPythonPackage (
              attrs
              // {
                # Because we're following main, use the git rev as version
                version = if (self ? rev) then self.shortRev else self.dirtyShortRev;
              }
            );
          default = self.packages.${system}.papis;
        };
        devShells = {
          default =
            let
              # Returns a function that can be passed to `python.withPackages`
              arg = project.renderers.withPackages {
                inherit python;
                # extras = ["develop" "docs" "lsp" "optional"];
                # Until https://github.com/pyproject-nix/pyproject.nix/issues/278 is
                # resolved, we must explicitly enumerate the components of develop
                extras = [
                  "lint"
                  "typing"
                  "test"
                  "docs"
                  "lsp"
                  "optional"
                ];
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
      }
    );
}
