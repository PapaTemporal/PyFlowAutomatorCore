# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import json
import argparse
import uvicorn
from app.main import run_from_file, create_app

parser = argparse.ArgumentParser(description="Run the application.")
parser.add_argument("--http", action="store_true", help="Run the HTTP server.")
parser.add_argument(
    "--script",
    type=str,
    default=None,
    help="Run a Python script instead of the server. Provide the file path.",
)
parser.add_argument(
    "--host",
    type=str,
    help="The host to bind to for http and ws servers. Default is localhost.",
)
parser.add_argument(
    "--port",
    type=int,
    help="The port to bind to for http and ws servers. Default is 8000.",
)
parser.add_argument(
    "--reload",
    action="store_true",
    help="Reloads on code change. Only available with --http. (BROKEN)",
)
parser.add_argument(
    "--stdout",
    action="store_true",
    help="Prints the function call and results to stdout.",
)
parser.add_argument(
    "--out",
    type=str,
    default=None,
    help="Filepath to save results to. Only available with --script.",
)
examples = """Examples:
    python run.py --http --host 0.0.0.0 --port 8080
    python run.py --script my_script.py --out my_saved_results.json --debug
"""
parser.epilog = examples
args = parser.parse_args()

if args.script:
    results = run_from_file(args.script, debug=args.stdout)
    if args.out:
        with open(args.out, "w") as f:
            f.write(json.dumps(results, indent=4))
elif args.http:
    uvicorn.run(
        "app.main:create_debug_app" if args.stdout else "app.main:create_app",
        host=args.host or "localhost",
        port=args.port or 8000,
        reload=args.reload,
    )
else:
    print("Please specify either --http or --script.")
