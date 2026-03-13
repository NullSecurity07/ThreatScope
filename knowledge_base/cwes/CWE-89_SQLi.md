# CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')

## Description
The software constructs all or part of an SQL command using externally-influenced input from an upstream component, but it does not neutralize or incorrectly neutralizes special elements that could modify the intended SQL command.

## Execution Context
- Look for f-strings or string concatenation in queries: `execute(f"SELECT * FROM users WHERE id = {user_id}")`
- Look for raw SQL usage bypassing ORMs (e.g. `User.objects.raw()` in Django or `session.execute()` in SQLAlchemy).

## Remediation
- Use parameterized queries or prepared statements.
- Use an ORM (Object Relational Mapper) correctly instead of building raw SQL strings.
