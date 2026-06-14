#!/usr/bin/env python3
"""Test the MCP server end-to-end via JSON-RPC over stdio."""

import json
import subprocess
import sys
import time


def send(proc, msg):
    body = json.dumps(msg)
    proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
    proc.stdin.flush()


def recv(proc, timeout=120):
    header = ""
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError("No response from MCP server")
        ch = proc.stdout.read(1)
        if not ch:
            raise EOFError("MCP server closed stdout")
        header += ch
        if header.endswith("\r\n\r\n"):
            break
    length = int(
        [l for l in header.strip().split("\r\n") if "Content-Length" in l][0].split(": ")[1]
    )
    body = proc.stdout.read(length)
    return json.loads(body)


def main():
    print("Starting MCP server...")
    proc = subprocess.Popen(
        ["uv", "run", "python", "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(2)

    try:
        # 1. Initialize
        print("\n[1] Initialize")
        send(proc, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1"},
            },
        })
        r = recv(proc)
        info = r.get("result", {}).get("serverInfo", {})
        print(f"  ✓ Server: {info.get('name')} v{info.get('version')}")

        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 2. List tools
        print("\n[2] List tools")
        send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        r = recv(proc)
        tools = r.get("result", {}).get("tools", [])
        print(f"  ✓ {len(tools)} tool(s) registered:")
        for t in tools:
            print(f"     - {t['name']}: {t.get('description', '')[:70]}")

        # 3. Call the agent tool with a simple query
        print("\n[3] Call ask_electricity_agent_tool")
        query = "What are the supported European countries?"
        print(f"  Query: \"{query}\"")
        send(proc, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "ask_electricity_agent_tool", "arguments": {"query": query}},
        })
        print("  Waiting for agent response (may take a moment)...")
        r = recv(proc, timeout=120)

        if "error" in r:
            print(f"  ✗ Error: {r['error']}")
        else:
            content = r.get("result", {}).get("content", [])
            text = content[0].get("text", "") if content else ""
            print(f"  ✓ Response received ({len(text)} chars):")
            print()
            # Print first 800 chars
            print("  " + text[:800].replace("\n", "\n  "))
            if len(text) > 800:
                print(f"  ... [{len(text) - 800} more chars]")

        print("\n✅ MCP server test complete")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        stderr = proc.stderr.read()
        if stderr:
            print(f"Server stderr:\n{stderr[:500]}")
        sys.exit(1)
    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
