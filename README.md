# PyFlowAutomatorCore

PyFlowAutomatorCore is a highly scalable backend designed to work seamlessly with the PyFlowAutomator web-based visual scripting UI. It's built to handle the needs of both individual users and enterprises, and can be deployed horizontally or vertically to scale with your environment. While it's designed to work with the PyFlowAutomator UI, it can also be used as a standalone script or function as a web/websocket API or REST service. Its core purpose is to enable users to write scripts remotely through a user-friendly UI, making it easy to automate runbooks through webhooks, act as a first responder to alerts or incidents, and more. You can use any functions in any Python package or create custom functions to run, making it highly extendable.

## Usage

To use the PyFlowAutomatorCore, you first need to define a flow. PyFlowAutomator is designed spicifically for this purpose, but you can use anything that can create the proper schema, including just writing it yourself as a json file.

#### schema

TLDR: Just use the PyFlowAutomator UI

NOTES:

start_id is optional if there is an edge with "start" in the "sourceHandle".

@xyflow (formerly reactflow) which is used by the PyFlowAutomator UI returns a lot of fields but we ignore those. So don't worry if examples look beefy, we ignore all the useless stuff for the backend. 

FYI: We keep the junk around so the flows are interchangable between the frontend and the backend. 

Edges dictate the execution flow and the fields that should be populated by the results of other functions.

```json
{
    "$defs": {
        "Edge": {
            "additionalProperties": true,
            "properties": {
                "id": {
                    "title": "Id",
                    "type": "string"
                },
                "source": {
                    "title": "Source",
                    "type": "string"
                },
                "sourceHandle": {
                    "anyOf": [
                        {
                            "type": "integer"
                        },
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Sourcehandle"
                },
                "target": {
                    "title": "Target",
                    "type": "string"
                },
                "targetHandle": {
                    "anyOf": [
                        {
                            "type": "integer"
                        },
                        {
                            "type": "string"
                        }
                    ],
                    "title": "Targethandle"
                }
            },
            "required": [
                "id",
                "source",
                "target",
                "targetHandle"
            ],
            "title": "Edge",
            "type": "object"
        },
        "Node": {
            "additionalProperties": true,
            "properties": {
                "id": {
                    "title": "Id",
                    "type": "string"
                },
                "type": {
                    "title": "Type",
                    "type": "string"
                },
                "data": {
                    "$ref": "#/$defs/NodeData"
                }
            },
            "required": [
                "id",
                "type",
                "data"
            ],
            "title": "Node",
            "type": "object"
        },
        "NodeData": {
            "additionalProperties": true,
            "properties": {
                "function": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Function"
                },
                "args": {
                    "anyOf": [
                        {
                            "items": {},
                            "type": "array"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Args"
                },
                "kwargs": {
                    "anyOf": [
                        {
                            "type": "object"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Kwargs"
                },
                "next_function": {
                    "anyOf": [
                        {
                            "type": "integer"
                        },
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "title": "Next Function"
                }
            },
            "title": "NodeData",
            "type": "object"
        }
    },
    "properties": {
        "variables": {
            "title": "Variables",
            "type": "object"
        },
        "edges": {
            "items": {
                "$ref": "#/$defs/Edge"
            },
            "title": "Edges",
            "type": "array"
        },
        "nodes": {
            "items": {
                "$ref": "#/$defs/Node"
            },
            "title": "Nodes",
            "type": "array"
        },
        "start_id": {
            "anyOf": [
                {
                    "type": "string"
                },
                {
                    "type": "null"
                }
            ],
            "default": null,
            "title": "Start Id"
        }
    },
    "required": [
        "variables",
        "edges",
        "nodes"
    ],
    "title": "Flow",
    "type": "object"
}
```

#### running a flow

Either set it up using the sample Dockerfile (sets it up as http on port 80)

or use the following to run it via commandline

```
usage: run.py [-h] [--http] [--ws] [--script SCRIPT] [--host HOST] [--port PORT] [--debug] [--out OUT]

Run the application.

options:
  -h, --help       show this help message and exit
  --http           Run the HTTP server.
  --ws             Run the WebSocket server.
  --script SCRIPT  Run a Python script instead of the server. Provide the file path.
  --host HOST      The host to bind to for http and ws servers. Default is localhost.
  --port PORT      The port to bind to for http and ws servers. Default is 8000.
  --debug          Enable debug mode. Only available with --http and --script.
  --out OUT        Filepath to save results to or 'stdout' for displaying in console. Default is no save or display. Only available with --script.

Examples: 
python run.py --http --host 0.0.0.0 --port 8080 
python run.py --ws --host example.com --port 9000 
python run.py --script my_script.py --debug
```

## Examples

From the root of the project run `python run.py --script "tests/example_logic.json" --out stdout` or `python run.py --script "tests/example_logic.json" --out my_results.json` to save the results to file instead.

## License

PyFlowAutomatorCore © 2023 by Abinadi Cordova is licensed under CC BY-NC-SA 4.0. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/