# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import json
import argparse
import uvicorn
from app.main import run_from_file, create_http_app, create_ws_app

parser = argparse.ArgumentParser(description="Run the application.")
parser.add_argument("--http", action="store_true", help="Run the HTTP server.")
parser.add_argument("--ws", action="store_true", help="Run the WebSocket server.")
parser.add_argument(
    "--script",
    type=str,
    default=None,
    help="Run a Python script instead of the server. Provide the file path.",
)
parser.add_argument(
    "--host",
    type=str,
    default="localhost",
    help="The host to bind to for http and ws servers. Default is localhost.",
)
parser.add_argument(
    "--port",
    type=int,
    default=8000,
    help="The port to bind to for http and ws servers. Default is 8000.",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="Enable debug mode. Only available with --http and --script.",
)
parser.add_argument(
    "--out",
    type=str,
    default=None,
    help="Filepath to save results to or 'stdout' for displaying in console. Default is no save or display. Only available with --script.",
)
examples = """Examples:
    python run.py --http --host 0.0.0.0 --port 8080
    python run.py --ws --host example.com --port 9000
    python run.py --script my_script.py --debug
"""
parser.epilog = examples
args = parser.parse_args()

if args.http and args.ws:
    print("Please specify either --http or --ws, not both.")
elif args.script:
    results = run_from_file(args.script, debug=args.debug)
    if args.out == "stdout":
        print(json.dumps(results, indent=4))
    elif args.out:
        with open(args.out, "w") as f:
            f.write(json.dumps(results, indent=4))
elif args.http:
    uvicorn.run(
        create_http_app(),
        host=args.host,
        port=args.port,
        reload=args.debug,
    )
elif args.ws:
    uvicorn.run(
        create_ws_app(),
        host=args.host,
        port=args.port,
        reload=args.debug,
    )
else:
    print("Please specify either --http or --ws or --script.")
