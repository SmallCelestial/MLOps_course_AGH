import base64
import io
import matplotlib.pyplot as plt
from typing import Annotated
from fastmcp import FastMCP

plt.switch_backend('Agg')

mcp = FastMCP("Visualization Server")


@mcp.tool(description="Create a line plot from given data and return it as a base64 encoded PNG image.")
def line_plot(
        data: Annotated[
            dict[str, list[float]], "Dictionary where keys are series names and values are lists of numbers to plot."],
        title: Annotated[str | None, "The title of the plot."] = None,
        x_label: Annotated[str | None, "The label for the X-axis."] = None,
        y_label: Annotated[str | None, "The label for the Y-axis."] = None,
        legend: Annotated[bool, "Whether to display the legend."] = True,
) -> str:
    plt.figure(figsize=(10, 6))

    for label, points in data.items():
        plt.plot(points, label=label)

    if title:
        plt.title(title)
    if x_label:
        plt.xlabel(x_label)
    if y_label:
        plt.ylabel(y_label)
    if legend:
        plt.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    plt.close()

    return image_base64


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8003, host="0.0.0.0")
