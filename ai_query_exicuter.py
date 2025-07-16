# This script allows you to ask natural language questions about a PostgreSQL database
# and generates SQL queries using a language model hosted on Hugging Face.
# It also executes the generated SQL against a PostgreSQL database and returns results.
# Make sure to have the required packages installed: huggingface_hub, langchain, psy
import os
import re
import psycopg2
from huggingface_hub import InferenceClient
from langchain.prompts import PromptTemplate

# === SETUP ===
# Set your Hugging Face API token
os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

# Initialize Hugging Face Inference Client
client = InferenceClient(
    api_key=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    provider="auto"
)

# PostgreSQL DB configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "postgres",
    "user": "admin",
    "password": "admin123"
}

# Schema for AI context
schema = """CREATE TABLE employees (
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

# LangChain prompt
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

# === FUNCTIONS ===

# Generate SQL using the model
def generate_sql(question: str) -> str:
    prompt = template.format(schema=schema, question=question)
    resp = client.chat.completions.create(
        model="HuggingFaceH4/zephyr-7b-beta",  # Hosted model with chat support
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.0
    )
    response_text = resp.choices[0].message.content.strip()

    # Extract only the first SQL block after "SQL:"
    match = re.search(r"SQL:\s*(.*)", response_text, re.IGNORECASE | re.DOTALL)
    if match:
        sql_text = match.group(1).strip()
        # Stop at next "Question:" or any other explanation
        lines = sql_text.splitlines()
        filtered_lines = []
        for line in lines:
            if line.strip().lower().startswith("question:"):
                break
            filtered_lines.append(line)
        return "\n".join(filtered_lines).strip()

    return response_text  # fallback (if no SQL: found)

# Execute the generated SQL in PostgreSQL
def execute_sql(sql: str):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                print("\n🚀 Executing SQL:\n", sql)
                cur.execute(sql)
                if cur.description:  # e.g., SELECT
                    rows = cur.fetchall()
                    print("\n📊 Query Results:")
                    for row in rows:
                        print(row)
                else:  # e.g., INSERT/UPDATE/DELETE
                    conn.commit()
                    print(f"\n✅ Query executed successfully.")
    except Exception as e:
        print("❌ DB Error:", e)

# === CLI LOOP ===

if __name__ == "__main__":
    print("🤖 Ask your data something (type 'exit' to quit):\n")
    while True:
        q = input("🔍 Question: ")
        if q.lower() in ["exit", "quit"]:
            break
        try:
            sql = generate_sql(q)
            print("\n🧠 Generated SQL:\n", sql)
            execute_sql(sql)
        except Exception as e:
            print("❌ Error:", e)
