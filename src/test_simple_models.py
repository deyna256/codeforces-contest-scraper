# test_simple_models.py

from domain.models.problem import ProblemData, ProblemIdentifier

# Test ProblemData
p = ProblemData(name="Two Sum", rating=1200, tags=["array"])
print("ProblemData test:", p)

# Test ProblemIdentifier
pid = ProblemIdentifier(contest_id=123, index="A")
print("ProblemIdentifier test:", pid)
