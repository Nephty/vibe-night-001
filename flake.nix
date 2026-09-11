{
  description = "Vibe Night";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
        lib = pkgs.lib;
        python = pkgs.python312;

        pythonEnv = python.withPackages (ps: [
          ps.django
          ps.gunicorn
          ps.whitenoise
        ]);

        # Source filtered to exclude dev/build cruft from the Nix store.
        src = lib.cleanSourceWith {
          src = ./.;
          filter = path: _type:
            let base = baseNameOf path; in
            !(lib.elem base [
              ".venv" ".git" ".direnv" "staticfiles" "result"
              "__pycache__" "node_modules" ".idea"
            ]);
        };

        # Derivation that collects static files (Django admin CSS/JS) at build time.
        appSrc = pkgs.stdenv.mkDerivation {
          pname = "vibenight-app";
          version = "0.1.0";
          inherit src;
          nativeBuildInputs = [ pythonEnv ];
          dontConfigure = true;

          buildPhase = ''
            runHook preBuild
            export HOME=$TMPDIR
            export DJANGO_SETTINGS_MODULE=config.settings
            export DJANGO_DEBUG=False
            export DJANGO_SECRET_KEY=build-time-only-not-secret
            export VIBENIGHT_STATIC_ROOT=$PWD/staticfiles
            python manage.py collectstatic --noinput
            runHook postBuild
          '';

          installPhase = ''
            runHook preInstall
            mkdir -p $out/share/vibenight
            cp -r vibenight config templates manage.py staticfiles \
                  $out/share/vibenight/
            runHook postInstall
          '';
        };

        appHome = "${appSrc}/share/vibenight";

        # Shell preamble shared by both wrappers.
        commonEnv = ''
          export DJANGO_SETTINGS_MODULE=config.settings
          export PYTHONPATH=${appHome}''${PYTHONPATH:+:$PYTHONPATH}
          export VIBENIGHT_STATIC_ROOT=''${VIBENIGHT_STATIC_ROOT:-${appHome}/staticfiles}
          export ALLOWED_HOSTS=''${ALLOWED_HOSTS:-*}
          export VIBENIGHT_DB_PATH=''${VIBENIGHT_DB_PATH:-/var/lib/vibenight/db.sqlite3}
        '';

        manageBin = pkgs.writeShellApplication {
          name = "vibenight-manage";
          runtimeInputs = [ pythonEnv ];
          text = ''
            ${commonEnv}
            exec python ${appHome}/manage.py "$@"
          '';
        };

        serverBin = pkgs.writeShellApplication {
          name = "vibenight-server";
          runtimeInputs = [ pythonEnv ];
          text = ''
            ${commonEnv}
            export DJANGO_DEBUG=''${DJANGO_DEBUG:-False}
            BIND=''${VIBENIGHT_BIND:-0.0.0.0:8000}
            WORKERS=''${VIBENIGHT_WORKERS:-3}

            echo "vibenight: migrating (db: $VIBENIGHT_DB_PATH)"
            python ${appHome}/manage.py migrate --noinput
            echo "vibenight: serving on $BIND ($WORKERS workers)"
            exec gunicorn config.wsgi:application \
              --chdir ${appHome} --bind "$BIND" --workers "$WORKERS"
          '';
        };

        vibenight = pkgs.symlinkJoin {
          name = "vibenight-0.1.0";
          paths = [ serverBin manageBin ];
        };
      in
      {
        packages = {
          default = vibenight;
          vibenight = vibenight;
          app = appSrc;
          pythonEnv = pythonEnv;
        };

        apps = {
          default = {
            type = "app";
            program = "${vibenight}/bin/vibenight-server";
          };
          manage = {
            type = "app";
            program = "${vibenight}/bin/vibenight-manage";
          };
        };

        devShells.default = pkgs.mkShell {
          name = "vibenight-shell";
          buildInputs = [
            pkgs.python312
            pkgs.python312Packages.pip
            pkgs.git
            pkgs.claude-code
          ];
          shellHook = ''
            if [ ! -d .venv ]; then
              python -m venv .venv
            fi
            source .venv/bin/activate
            pip install -r requirements.txt -q
            echo "Vibe Night dev shell — run: python manage.py runserver"
          '';
        };
      }))

    // {
      # NixOS module — add to your server's configuration.nix:
      #   inputs.vibenight.url = "github:you/vibe-night";
      #   imports = [ inputs.vibenight.nixosModules.default ];
      #   services.vibenight.enable = true;
      nixosModules.default = { config, pkgs, lib, ... }:
        let cfg = config.services.vibenight;
        in {
          options.services.vibenight = {
            enable = lib.mkEnableOption "Vibe Night";
            package = lib.mkOption {
              type = lib.types.package;
              default = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
              description = "The vibenight package to run.";
            };
            bind = lib.mkOption {
              type = lib.types.str;
              default = "127.0.0.1:8000";
              description = "host:port gunicorn binds to.";
            };
            workers = lib.mkOption {
              type = lib.types.int;
              default = 3;
            };
            allowedHosts = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = [ "localhost" "127.0.0.1" ];
              description = "Django ALLOWED_HOSTS (comma-joined into the env var).";
            };
            secretKeyFile = lib.mkOption {
              type = lib.types.nullOr lib.types.path;
              default = null;
              description = "Path to a file containing the Django SECRET_KEY (needed now for admin sessions/CSRF).";
            };
            urlPrefix = lib.mkOption {
              type = lib.types.str;
              default = "";
              description = "URL path prefix this app is reverse-proxied under (e.g. \"/vibenight\"). Empty means served at the domain root.";
            };
          };

          config = lib.mkIf cfg.enable {
            systemd.services.vibenight = {
              description = "Vibe Night";
              wantedBy = [ "multi-user.target" ];
              after = [ "network.target" ];
              environment = {
                DJANGO_DEBUG = "False";
                ALLOWED_HOSTS = lib.concatStringsSep "," cfg.allowedHosts;
                VIBENIGHT_BIND = cfg.bind;
                VIBENIGHT_WORKERS = toString cfg.workers;
                DJANGO_FORCE_SCRIPT_NAME = cfg.urlPrefix;
                VIBENIGHT_KEYLOG_PATH = "/var/lib/vibenight/keylog.jsonl";
                VIBENIGHT_DB_PATH = "/var/lib/vibenight/db.sqlite3";
              };
              serviceConfig = {
                ExecStart = pkgs.writeShellScript "vibenight-start" ''
                  ${lib.optionalString (cfg.secretKeyFile != null) ''
                    DJANGO_SECRET_KEY="$(cat ${cfg.secretKeyFile})"
                    export DJANGO_SECRET_KEY
                  ''}
                  exec ${cfg.package}/bin/vibenight-server
                '';
                DynamicUser = true;
                StateDirectory = "vibenight";
                StateDirectoryMode = "0755";
                Restart = "on-failure";
                RestartSec = 2;
              };
            };
          };
        };
    };
}
