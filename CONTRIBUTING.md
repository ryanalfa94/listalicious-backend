# Contributing

Thank you for contributing to Listalicious! This document explains the preferred workflow for code changes and pull requests.

## How to contribute

1. Fork the repository.
2. Create a feature branch:
   ```bash
git checkout -b feature/my-change
```
3. Make your changes.
4. Run tests locally:
   ```bash
pytest -q
```
5. Commit with a clear message.
6. Push your branch and open a pull request.

## Branch naming

Use descriptive branch names, such as:
- `feature/add-share-invite`
- `fix/pagination-headers`
- `chore/docker-docs`

## Coding standards

- Keep Python code clear and idiomatic.
- Follow PEP 8 where possible.
- Keep functions small and single-purpose.
- Document any new public behavior in `README.md` or `DEVELOPMENT.md`.

## Testing

- Run the full test suite before submitting changes.
- If your change affects a specific area, run only those tests:
  ```bash
pytest -q tests/test_auth.py
```

## Pull request checklist

- [ ] Code compiles and runs correctly
- [ ] Tests pass
- [ ] Docs updated as needed
- [ ] No secret keys or credentials committed
