# This script generates SQL queries from natural language questions using a language model hosted on Hugging Face.
# It uses LangChain for prompt management and connects to a PostgreSQL database to execute the queries.
# Ensure you have the required packages installed: huggingface_hub, langchain, psycop
import os
from huggingface_hub import InferenceClient
from langchain.prompts import PromptTemplate

# Replace with your HF API token (set it or export beforehand)
os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

# Initialize client (auto-select host/provider)
client = InferenceClient(api_key='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', provider="auto")

# LangChain prompt definition
schema = """CREATE TABLE public.employees (
    id serial4 NOT NULL PRIMARY KEY,
    full_name varchar(100),
    email varchar(100),
    department varchar(50),
    position varchar(50),
    joining_date date,
    experience_years int4,
    salary numeric(10,2),
    is_active bool,
    country varchar(50)
);"""

template = PromptTemplate(
    input_variables=["schema", "question"],
    template="""
You are an AI SQL assistant. Convert the natural language question into valid PostgreSQL SQL using the schema below.

Schema:
{schema}

Question:
{question}

SQL:
"""
)

def generate_sql(question: str) -> str:
    prompt = template.format(schema=schema, question=question)
    resp = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",  # hosted model with chat support
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.0
    )
    return resp.choices[0].message.content.strip()

if __name__ == "__main__":
    print("Ask data something (type 'exit' to quit):\n")
    while True:
        q = input("Question: ")
        if q.lower() in ["exit", "quit"]:
            break
        try:
            print("\nGenerated SQL:\n", generate_sql(q), "\n")
        except Exception as e:
            print("❌ Error:", e)
