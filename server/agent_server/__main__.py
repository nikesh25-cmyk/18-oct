"""Run the local prototype API: python -m agent_server --provider demo|deepseek."""

import argparse
import os

from .deepseek_provider import DeepSeekProvider
from .demo_provider import DemoProvider
from .http_api import create_server
from .jobs import JobManager


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("demo", "deepseek"), default="demo")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.provider == "deepseek":
        key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not key:
            parser.error("DEEPSEEK_API_KEY must be set in the backend environment.")
        provider = DeepSeekProvider(key)
    else:
        provider = DemoProvider()
    server = create_server("127.0.0.1", args.port, JobManager(provider))
    print(f"Agent District {args.provider} API listening on 127.0.0.1:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
