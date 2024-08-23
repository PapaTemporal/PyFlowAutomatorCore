# This file is licensed under the CC BY-NC-SA 4.0 license.
# See https://creativecommons.org/licenses/by-nc-sa/4.0/ for details.

import os
import json
import argparse
import uvicorn
from argparse import RawDescriptionHelpFormatter
from dotenv import load_dotenv

load_dotenv()
from app import run_from_file

parser = argparse.ArgumentParser(
    description="Run the application.", formatter_class=RawDescriptionHelpFormatter
)
parser.add_argument(
    "--script",
    type=str,
    default=None,
    help="Run a Python script instead of the server. Provide the file path.",
)
parser.add_argument(
    "--out",
    type=str,
    default=None,
    help="Filepath to save results to. Only available with --script.",
)
parser.add_argument("--http", action="store_true", help="Run FastAPI HTTP/WS server.")
parser.add_argument(
    "--host",
    type=str,
    help="The host to bind to for http/ws services (overrides PFA_HOST env variable). Default is localhost.",
)
parser.add_argument(
    "--port",
    type=int,
    help="The port to bind to for http/ws services (overrides PFA_PORT env variable). Default is 8000.",
)

examples = """Examples:
    python run.py --http --host 0.0.0.0 --port 8080
    python run.py --script my_script.py --out my_saved_results.json
Environment Variables:
    PFA_LOCAL: set to True when running locally so CORS can be enabled 
    PFA_DB_CLASS: for any ORM/DB extensibility, a class with CRUD operations for flows 
                that takes no arguments (see app.utils.database for examples) 
                defaults to SimpleInMemoryDB
    PFA_HOST: host to use when starting http/ws server
    PFA_PORT: port to use when starting http/ws server
"""
parser.epilog = examples
args = parser.parse_args()

if args.script:
    results = run_from_file(args.script)
    if args.out:
        with open(args.out, "w") as f:
            f.write(json.dumps(results, indent=4))
elif args.http:
    uvicorn.run(
        "app:create_app",
        host=args.host or os.getenv("PFA_HOST", "localhost"),
        port=args.port or int(os.getenv("PFA_PORT", "8000")),
    )
else:
    print("Please specify either --http or --script.")
