{
  description = "Prometheus exporter for my-PV AC ELWA devices";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      inherit (nixpkgs) lib;

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      forAllSystems = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      version = (lib.importTOML ./pyproject.toml).project.version;

      # Only ship what is needed to build and test the package.
      src = lib.fileset.toSource {
        root = ./.;
        fileset = lib.fileset.unions [
          ./pyproject.toml
          ./README.md
          ./src
          ./tests
        ];
      };
    in
    {
      packages = forAllSystems (
        pkgs:
        let
          mypv-elwa-prometheus-exporter = pkgs.python3Packages.buildPythonApplication {
            pname = "mypv-elwa-prometheus-exporter";
            inherit version src;

            pyproject = true;
            build-system = [ pkgs.python3Packages.uv-build ];

            dependencies = with pkgs.python3Packages; [
              typer
              requests
              rich
              prometheus-client
            ];

            # Tests are fully mocked with `responses`; no network access needed.
            nativeCheckInputs = with pkgs.python3Packages; [
              pytestCheckHook
              responses
            ];
            pythonImportsCheck = [ "mypv_elwa_prometheus_exporter" ];

            meta = {
              description = "Export my-PV AC ELWA device statistics as Prometheus metrics";
              homepage = "https://git.h.oluflorenzen.de/finkregh/mypv-elwa-prometheus-exporter";
              license = lib.licenses.mit;
              mainProgram = "mypv-elwa-prometheus-exporter";
              platforms = lib.platforms.unix;
            };
          };
        in
        {
          default = mypv-elwa-prometheus-exporter;
          inherit mypv-elwa-prometheus-exporter;
        }
      );

      overlays.default = final: _prev: {
        mypv-elwa-prometheus-exporter = self.packages.${final.stdenv.hostPlatform.system}.default;
      };

      nixosModules.default =
        {
          config,
          lib,
          pkgs,
          ...
        }:
        let
          cfg = config.services.mypv-elwa-exporter;
        in
        {
          options.services.mypv-elwa-exporter = {
            enable = lib.mkEnableOption "the my-PV AC ELWA Prometheus exporter";

            package = lib.mkOption {
              type = lib.types.package;
              default = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
              defaultText = lib.literalExpression "mypv-elwa-exporter.packages.\${system}.default";
              description = "The exporter package to use.";
            };

            url = lib.mkOption {
              type = lib.types.nonEmptyListOf lib.types.str;
              example = [ "http://192.168.178.125" ];
              description = ''
                Device URL(s). Multiple devices are passed comma-separated to
                the exporter, which scrapes all of them.
              '';
            };

            port = lib.mkOption {
              type = lib.types.port;
              default = 8000;
              description = "Port the exporter listens on (all interfaces).";
            };

            logLevel = lib.mkOption {
              type = lib.types.enum [
                "DEBUG"
                "INFO"
                "WARNING"
                "ERROR"
                "CRITICAL"
              ];
              default = "INFO";
              description = "Log level of the exporter.";
            };

            openFirewall = lib.mkOption {
              type = lib.types.bool;
              default = false;
              description = "Whether to open the exporter port in the firewall.";
            };
          };

          config = lib.mkIf cfg.enable {
            systemd.services.mypv-elwa-exporter = {
              description = "my-PV AC ELWA Prometheus exporter";
              wantedBy = [ "multi-user.target" ];
              after = [ "network-online.target" ];
              wants = [ "network-online.target" ];

              serviceConfig = {
                ExecStart = "${cfg.package}/bin/mypv-elwa-prometheus-exporter serve";
                Environment = [
                  "MYPVELWAEXPORTER_SERVE_URL=${lib.concatStringsSep "," cfg.url}"
                  "MYPVELWAEXPORTER_SERVE_PORT=${toString cfg.port}"
                  "MYPVELWAEXPORTER_SERVE_LOG_LEVEL=${cfg.logLevel}"
                ];
                Restart = "always";
                RestartSec = 10;

                # The exporter is stateless and only logs to stderr.
                DynamicUser = true;
                ProtectSystem = "strict";
                ProtectHome = true;
                PrivateTmp = true;
                PrivateDevices = true;
                NoNewPrivileges = true;
                CapabilityBoundingSet = "";
                RestrictAddressFamilies = [
                  "AF_INET"
                  "AF_INET6"
                  "AF_UNIX"
                ];
              };
            };

            networking.firewall.allowedTCPPorts = lib.mkIf cfg.openFirewall [ cfg.port ];
          };
        };

      devShells = forAllSystems (
        pkgs:
        let
          inherit (pkgs) python3;
        in
        {
          default = pkgs.mkShell {
            packages =
              with python3.pkgs;
              [
                uv-build
                pytest
                responses
                black
                mypy
              ]
              ++ [
                python3
                pkgs.uv
              ];
          };
        }
      );

      formatter = forAllSystems (pkgs: pkgs.nixfmt);
    };
}
