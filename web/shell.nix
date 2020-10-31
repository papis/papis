with import <nixpkgs> {};

let
  nixPackages = [
    purescript
    yarn
    spago
    pscid
    ];
in
mkShell rec {
  buildInputs = nixPackages;
}
