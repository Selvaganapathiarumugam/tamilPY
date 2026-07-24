import argparse

import uvicorn


def app_parse_args():
    """Build CLI arguments for the development server."""
    parser = argparse.ArgumentParser(description="Run the app")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port",
    )
    return parser


if __name__ == "__main__":
    arg_parser = app_parse_args()
    args = arg_parser.parse_args()
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
