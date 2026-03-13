# CWE-287: Improper Authentication

## Description
When an actor claims to have a given identity, the software does not prove or insufficiently proves that the claim is correct. This leads to authentication bypasses where users can perform actions without logging in or as another user.

## Execution Context
- Look for API routes that lack authentication decorators (e.g., `@login_required` or `@jwt_required`).
- Look for hardcoded admin passwords or tokens.
- Look for weak session cookie generation or JWTs without proper secret signing.
- Look for routes like `/api/admin/delete_user` that don't verify roles.

## Remediation
- Apply robust authentication wrappers to all sensitive endpoints.
- Ensure JWT signatures are strictly enforced using high-entropy secrets.
- Map every route explicitly to role-based access control evaluations.
