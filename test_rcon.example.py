"""Example RCON smoke test.

Copy to test_rcon.py locally and fill in private values before running.
"""

from mcrcon import MCRcon

RCON_HOST = "example.com"
RCON_PORT = 25575
RCON_PASSWORD = ""


def main() -> None:
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as client:
        print(client.command("list"))


if __name__ == "__main__":
    main()
