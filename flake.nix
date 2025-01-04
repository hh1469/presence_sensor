{
  description = "Simple presence sensor checker";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
    ...
  } @ inputs: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
      overlays = [self.overlay];
    };
  in {
    overlay = final: prev: {
      presence_sensor = prev.python3Packages.buildPythonPackage rec {
        pname = "presence_sensor";
        version = "0.2.0";

        src = ./.;

        format = "other";

        installPhase = ''
          mkdir -p $out/bin
          cp presence_sensor.py $out/bin/presence_sensor
        '';

        meta = with pkgs.lib; {
          description = "Simple presence sensor checker";
          license = licenses.mit;
        };

        propagatedBuildInputs = with prev; [
          python3Packages.paho-mqtt
          python3Packages.requests
        ];
      };
    };

    packages.${system}.default = pkgs.presence_sensor;

    devShell.${system} = pkgs.mkShell {
      buildInputs = with pkgs; [
        python3.pkgs.paho-mqtt
        python3.pkgs.requests
      ];
    };
  };
}
