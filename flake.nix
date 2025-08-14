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

            papis =
              let
                # Returns an attribute set that can be passed to `buildPythonPackage`.
                attrs = project.renderers.buildPythonPackage {
                  inherit python;
                  extras = [ "optional" ];
                };
              in
              assert
                project.validators.validateVersionConstraints {
                  inherit python;
                  extras = [
                    "develop"
                    "docs"
                    "optional"
                  ];
                } == { };
              # Pass attributes to buildPythonPackage.
              # Here is a good spot to add on any missing or custom attributes.
              final.buildPythonPackage (
                attrs
                // {
                  # Because we're following main, use the git rev as version
                  version = if (self ? rev) then self.shortRev else self.dirtyShortRev;
                }
              );
          };
        };

        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };

      in
      {
        packages = {
          default = self.packages.${system}.papis;
          inherit (python.pkgs) papis;
        };
        devShells = {
          default =
            let
              # Returns a function that can be passed to `python.withPackages`
              arg = project.renderers.withPackages {
                inherit python;
                extras = [
                  "develop"
                  "docs"
                  "optional"
                ];
              };

              # Returns a wrapped environment (virtualenv like) with all our packages
              pythonEnv = python.withPackages arg;

              # Tools useful to have in the dev environment but not strictly
              # necessary to our workflow
              extra-dev-tools = python.withPackages (ps: [
                ps.python-lsp-server
              ]);

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
                extra-dev-tools
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
