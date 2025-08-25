from pathlib import Path

from agno.agent import Agent
from agno.models.azure.openai_chat import AzureOpenAI
from agno.tools.duckdb import DuckDbTools
from agno.utils.load_env import load_env
from pydantic import BaseModel

load_env(dotenv_dir=Path.cwd())


class UseCaseResult(BaseModel):
    input_file: str
    output_file: str


class UC1Result(UseCaseResult):
    is_sparse: bool
    has_nulls: bool


class UC4Result(UseCaseResult):
    has_duplicates: bool


uc1_agent = Agent(
    model=AzureOpenAI("gpt-4o"),
    response_model=UC1Result,
    tools=[DuckDbTools(export_tables=True)],
    description="You are a data completeness checking agent.",
    instructions=[
        "Step 1: Use DuckDb toolset to read the input path provided. The table name should match the file name.",
        "Step 2: Check if the table is sparse or has nulls. If the dataset is empty, then consider it as sparse.",
        "Step 3: Export the table in the same format as the input at the output directory (do not add the table name to the output directory while calling DuckDb export) without any modifications.",
        "Step 4: Verify if the table is exported correctly to the output path.",
    ],
    debug_mode=True,
)

uc4_agent = Agent(#as well as original table
    model=AzureOpenAI("gpt-4o"),
    response_model=UC4Result,
    tools=[DuckDbTools(export_tables=True)],
    description="You are a data duplication removal agent.",
    instructions=[
        "Step 1: Use DuckDb toolset to read the input path provided. The table name should match the file name.",
        "Step 2: Make sure no to look at the contents of the table, if required only do it with strict limit of 10.",
        "Step 2: Check if the table contains any duplicates and remove them, updating the table.",
        "Step 3: Export the updated table in the same format as the input at the output directory (do not add the table name to the output directory while calling DuckDb export). Ensure the deduplicated table name is consistent, e.g., append '_dedup' to the original file name.",
        "Step 4: Verify if the table is exported correctly to the output path.",
    ],
    debug_mode=True,
)

# input_file = Path("inputs/example_dataset_0.csv").absolute()
# output_file = Path("outputs").absolute()
# for path in output_file.iterdir():
#     path.unlink()

# # uc1_agent.print_response(
# #     f"Process the input file path at {input_file} and output directory path at {output_file}"
# # )
# uc4_agent.print_response(
#     f"Process the input file path at {input_file} and output directory path at {output_file}"
# )
