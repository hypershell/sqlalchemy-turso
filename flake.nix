{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils = {
      url = "github:numtide/flake-utils";
    };
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        formatter = pkgs.nixpkgs-fmt;
        devShells.default = with pkgs; mkShell {
          buildInputs = [
            ruff
            uv
            python312
            python312Packages.pip
            python312Packages.virtualenv
            python312Packages.pytest
            python312Packages.pyperf

            # to debug `libsql-experimental`
            maturin
            cmake
          ];
          shellHook = ''
            virtualenv .venv
            source .venv/bin/activate
          '';
        };
      });
}
