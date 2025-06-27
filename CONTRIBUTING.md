# Contributing to Document Matching Service

## Development Setup

1. **Environment Setup**
   ```bash
   source .venv/bin/activate
   ```

2. **Running the Service**
   ```bash
   PYTHONPATH=src uvicorn app:app
   ```

3. **Code Formatting**
   ```bash
   black src/ tests/
   ```

## Testing

### Running Tests

```bash
# Run all tests and linting
nox

# Download models
nox -s download_models

# Run just tests
nox -s test

# Run just linting  
nox -s lint

# Run specific test categories
pytest -m api              # API tests
pytest -m smoke            # Smoke tests
pytest -m core_matching    # Core matching functionality
```

### Work-in-Progress (WIP) Tests

When developing new tests that aren't ready for CI, use the WIP marker system:

```bash
# Run all tests except WIP (default behavior - safe for CI)
pytest

# Run work-in-progress tests (for developers actively working on them)
pytest --run-wip

# Run only WIP tests for development
pytest -m wip --run-wip

# Check which tests are marked as WIP
pytest --collect-only -m wip
```

### Developing New BDD Tests

1. **Add scenario to feature file** with `@wip` tag:
   ```gherkin
   @deviations @currency_mismatch @wip
   Scenario: Match with Different Currencies
     Given I have a primary invoice document with currency "USD"
     And I have a candidate purchase order with currency "EUR"
     # ... rest of scenario
   ```

2. **Create test file** with `@pytest.mark.wip` and stub step definitions:
   ```python
   @pytest.mark.wip
   @scenario(str(get_feature_path("api-consumer/deviations.feature")), "Match with Different Currencies")
   def test_match_with_currency_deviations():
       """Test currency deviations - WIP."""
       pass
   
   @given(parsers.parse('I have a primary invoice document with currency "{currency}"'))
   def primary_invoice_with_currency(context, currency):
       pytest.skip("Step definition not implemented yet")
   ```

3. **Develop incrementally**:
   - Use `pytest -m wip --run-wip` to run only your WIP test
   - Implement step definitions one by one
   - Test iteratively without affecting others

4. **When complete**:
   - Remove `@wip` tags from feature file and test
   - Ensure test passes in regular test suite
   - Test runs automatically in CI

### BDD Test Structure

- **Feature files**: `features/` - Gherkin scenarios organized by user perspective
- **Step definitions**: `tests/acceptance/steps/` - Reusable step implementations
- **Test files**: `tests/acceptance/*/` - pytest-bdd scenario runners
- **Test data**: `features/api-consumer/test_data/` - Sample documents for testing

### Best Practices

1. **Use real test data**: Base tests on actual document formats from `features/api-consumer/test_data/`
2. **Test real pipeline**: Use whitelisted sites ("test-site") to test ML pipeline, not dummy logic
3. **Validate actual API behavior**: Update BDD scenarios to match real system responses
4. **Reuse step definitions**: Check existing steps in `tests/acceptance/steps/api_steps.py`
5. **Mark appropriately**: 
   - `@wip` for incomplete tests
   - `@not_implemented` for planned but not started tests
   - Remove markers when tests are complete
6. **Limit file size**: Try to keep every file below 500 lines.