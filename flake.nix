{
  description = "CHAINSCOPE — Crypto Intelligence Platform";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    spider-nix = {
      url = "git+ssh://git@github.com/marcosfpina/spider-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      spider-nix,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };

        # ── Python dependencies disponíveis no nixpkgs ───────────────────────
        pythonDeps = with pkgs.python313Packages; [
          # HTTP clients
          httpx
          aiohttp
          websockets

          # Serialization
          orjson
          msgpack
          zstandard

          # Validation
          pydantic
          jsonschema

          # Storage clients
          asyncpg            # TimescaleDB / Postgres
          redis              # Redis async
          neo4j              # Neo4j driver
          # qdrant-client    # via pip (não está no nixpkgs ainda)
          # clickhouse-connect # via pip

          # Web3 / blockchain
          web3               # Ethereum JSON-RPC + ABI decoding

          # Document parsing
          feedparser         # RSS/Atom
          pypdf2             # PDF extraction (pypdf)
          lxml
          beautifulsoup4
          markdownify

          # GraphQL client
          # gql              # via pip

          # Scheduling
          apscheduler

          # Observability
          structlog
          prometheus-client
          opentelemetry-sdk
          opentelemetry-exporter-otlp

          # Crypto / math
          numpy
          pandas
          scipy
          scikit-learn

          # API framework
          fastapi
          uvicorn

          # Dev tools
          pytest
          pytest-asyncio
          ruff
          mypy
          pip
          ipython
        ];

        pythonEnv = pkgs.python313.withPackages (_: pythonDeps);

      in
      {
        devShells.default = pkgs.mkShell {
          name = "chainscope-dev";

          buildInputs = with pkgs; [
            pythonEnv

            # Package manager (para deps não no nixpkgs)
            uv

            # Infra
            docker
            docker-compose

            # Database CLIs (debug)
            postgresql_16      # psql
            redis              # redis-cli
            # clickhouse        # clickhouse-client (se disponível)

            # Dev utilities
            just
            git
            jq
            httpie             # debug de APIs
            curl

            # Observabilidade
            prometheus
            grafana
          ];

          shellHook = ''
            # ── Variáveis de ambiente de desenvolvimento ─────────────────────
            export CHAINSCOPE_ENV="development"
            export PYTHONPATH="$PWD:$PYTHONPATH"

            # Spider-nix path (dependência local)
            export SPIDER_NIX_PATH="${spider-nix}"
            export PYTHONPATH="${spider-nix}/src:$PYTHONPATH"

            # Storage (defaults locais via docker-compose)
            export TIMESCALE_URL="postgresql://chainscope:chainscope@localhost:5432/chainscope"
            export REDIS_URL="redis://localhost:6379/0"
            export NEO4J_URL="bolt://localhost:7687"
            export NEO4J_USER="neo4j"
            export NEO4J_PASSWORD="chainscope"
            export QDRANT_URL="http://localhost:6333"
            export CLICKHOUSE_HOST="localhost"
            export CLICKHOUSE_PORT="8123"

            # Inference service (B300)
            export INFERENCE_URL="http://localhost:9000"

            # ── Instalar deps não disponíveis no nixpkgs via uv ──────────────
            if [ ! -d ".venv" ]; then
              echo "Criando .venv com deps extras (qdrant-client, clickhouse-connect, gql)..."
              uv venv .venv --python python3.13
              uv pip install \
                qdrant-client>=1.8.0 \
                clickhouse-connect>=0.7.0 \
                "gql[aiohttp]>=3.5.0" \
                "spider-nix @ file://${spider-nix}"
            fi
            source .venv/bin/activate 2>/dev/null || true

            # ── Banner ────────────────────────────────────────────────────────
            echo ""
            echo "╔══════════════════════════════════════════════════════════╗"
            echo "║            CHAINSCOPE — Dev Environment                 ║"
            echo "║        Crypto Intelligence Platform (B300)               ║"
            echo "╚══════════════════════════════════════════════════════════╝"
            echo ""
            echo "Python : $(python --version)"
            echo "uv     : $(uv --version)"
            echo ""
            echo "Infra:"
            echo "  docker compose -f infra/docker-compose.foundation.yml up -d"
            echo ""
            echo "Pipeline:"
            echo "  python -m services.collector.engine          # collector"
            echo "  python -m services.enrichment.pipeline       # enrichment (B300)"
            echo "  python -m services.delivery.api.app          # API server"
            echo ""
            echo "Adapters:"
            echo "  python -c \"from services.collector.adapters.discourse import DiscourseAdapter\""
            echo ""
          '';
        };

        # ── Package buildável (sem deps externas ao nixpkgs) ─────────────────
        packages.default = pkgs.python313Packages.buildPythonApplication {
          pname = "chainscope";
          version = "0.1.0";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with pkgs.python313Packages; [
            hatchling
          ];

          propagatedBuildInputs = pythonDeps;

          meta = with pkgs.lib; {
            description = "CHAINSCOPE — Crypto Intelligence Platform";
            license = licenses.mit;
            platforms = platforms.linux;
          };
        };
      }
    );
}
