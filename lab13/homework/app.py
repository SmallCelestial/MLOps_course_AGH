import asyncio
import json
import sys

# Używamy AsyncOpenAI, żeby nie blokować pętli podczas generowania tekstu
from openai import AsyncOpenAI, OpenAI

from guards import guard_input, guard_output
from settings import VLLM_BASE_URL, WEATHER_MCP_URL, TAVILY_MCP_URL
from mcp_client import MCPManager

async def main():
    client = OpenAI(api_key="EMPTY", base_url=VLLM_BASE_URL)

    mcp_servers = {
        "weather": WEATHER_MCP_URL,
        "tavily": TAVILY_MCP_URL
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful travel assistant. You help users plan trips by checking weather "
                "and finding information about destinations using your tools. "
                "Keep your answers concise and relevant to travel."
            )
        },
    ]

    async with MCPManager(mcp_servers) as mcp:
        print("\nAI Trip Planning Assistant\n")
        print("\nSystem ready. Type 'quit' to exit.")

        while True:
            user_input = input("\nUser: ")
            user_input = user_input.strip()

            try:
                guard_input.validate(user_input)
            except Exception as e:
                print(f"Security Alert: {e}")
                continue

            if user_input.lower() in ("quit", "exit"):
                break
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})

            for _ in range(10):
                response = client.chat.completions.create(
                    model="",
                    messages=messages,
                    tools=mcp.tools,
                    tool_choice="auto",
                    max_completion_tokens=1000,
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                )

                response = response.choices[0].message

                if not response.tool_calls:
                    content = response.content

                    try:
                        guard_output.validate(content)
                        messages.append({"role": "assistant", "content": content})
                        print(f"Assistant: {content}")
                    except Exception as e:
                        print(f"Assistant: [Redacted due to topic violation] {e}")
                    break

                messages.append(response)

                for tool_call in response.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    print(f"Executing tool '{func_name}'")
                    func_result = await mcp.call_tool(func_name, func_args)
                    print(f"\nTool '{func_name}' returned: {func_result}\n")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": str(func_result),
                        }
                    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")