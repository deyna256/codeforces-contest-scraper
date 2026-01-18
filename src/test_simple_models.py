from domain.models.problem import ProblemData, ProblemIdentifier

# Create a ProblemIdentifier
pid = ProblemIdentifier(contest_id=123, problem="A")

# Create a ProblemData
p = ProblemData(
    identifier=pid,
    title="Two Sum",
    url="https://codeforces.com/problemset/problem/123/A",
    contest_name="Example Contest",
    possible_editorial_links=[],
)

print("ProblemData test:", p)
print("ProblemIdentifier test:", pid)
