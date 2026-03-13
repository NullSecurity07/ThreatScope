# CWE-79: Cross-Site Scripting (XSS)

## Description
Cross-Site Scripting (XSS) occurs when an application includes untrusted data in a web page without proper validation or escaping, or updates an existing web page with user-supplied data using a browser API that can create HTML or JavaScript.

## Execution Context
- Look for Jinja2 templates returning `|safe`.
- Look for Flask or Django views returning direct HTML interpolation.
- Look for Javascript `innerHTML` assignments without sanitization.

## Remediation
- Always use auto-escaping in templates.
- Use `textContent` instead of `innerHTML` in frontend JS.
- Sanitize inputs with libraries like DOMPurify before rendering HTML.
