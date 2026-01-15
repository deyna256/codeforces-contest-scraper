# src/test_all_models.py

from datetime import datetime
from domain.models.problem import ProblemIdentifier, ProblemData
from domain.models.editorial import Editorial, CodeSnippet, CachedEditorial

# --- Test ProblemIdentifier ---
pid = ProblemIdentifier(contest_id=123, problem="A", is_gym=False)
print("ProblemIdentifier test:", pid)

# --- Test ProblemData ---
p = ProblemData(
    identifier=pid,
    title="Two Sum",
    url="https://codeforces.com/problemset/problem/123/A",
    contest_name="Example Contest",
    possible_editorial_links=[]
)
print("ProblemData test:", p)

# --- Test CodeSnippet ---
snippet = CodeSnippet(language="Python", code="print('Hello, World!')", description="Example code snippet")
print("CodeSnippet test:", snippet)

# --- Test Editorial ---
e = Editorial(
    problem="123A",
    solution_text="This is the solution text for Two Sum",
    approach="Use a hashmap to store visited numbers",
    algorithm="Single pass hashmap",
    time_complexity="O(n)",
    space_complexity="O(n)",
    code_snippets=[snippet],
    hints=["Check for duplicates", "Consider negative numbers"],
    notes="This is just a sample editorial",
    source_url="https://codeforces.com/blog/entry/12345"
)
print("Editorial test:", e)

# --- Test CachedEditorial ---
cached = CachedEditorial(editorial=e)
print("CachedEditorial test:", cached)
print("Is cached editorial expired?", cached.is_expired)
