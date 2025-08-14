"""
CalculatorPlugin server module.

MCP Server to expose two calculator tools: add_numbers and subtract_numbers over an SSE transport.

"""

from mcp.server.fastmcp import FastMCP

NAME = "Calculator Tool"
HOST = "0.0.0.0"
PORT = 9001

mcp = FastMCP(NAME, host=HOST, port=PORT)


class CalculatorPlugin:
    """
    Exposes basic arithmetic operations as MCP tools.

    - add_numbers: sum a list of integers.
    - subtract_numbers: subtract two integers.
    """
    @staticmethod
    @mcp.tool()
    def add_numbers(numbers: list[int]) -> int:
        """Adds all the numbers provided in the list."""
        return sum(numbers)

    @staticmethod
    @mcp.tool()
    def subtract_numbers(num_a: int, num_b: int) -> int:
        """Subtracts two numbers and returns the result."""
        print("subtract_numbers plugin called", num_a, num_b)
        return num_a - num_b

    @staticmethod
    def display_runtime_info():
        """Prints out the server’s host and port information to the console."""
        if HOST == "0.0.0.0":
            print(f"{NAME} : Server running on IP: localhost and Port: {PORT}")
            print(f"{NAME} : Server running on IP: 127.0.0.1 and Port: {PORT}")
        print(f"{NAME} : Server running on IP: {HOST} and Port: {PORT}")

    def run(self, transport: str = "sse"):
        """Starts the MCP server and displays the IP address and port."""
        self.display_runtime_info()
        mcp.run(transport=transport)


if __name__ == "__main__":
    server = CalculatorPlugin()
    server.run()
