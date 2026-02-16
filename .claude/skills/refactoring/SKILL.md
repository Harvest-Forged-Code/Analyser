# ---
# name: refactoring
# description: >
#   Use when improving code structure without changing behavior — extract
#   method/class, inline, apply design patterns, reduce cyclomatic complexity,
#   eliminate code smells, and pay down technical debt.
# trigger: >
#   When user mentions tech debt, code smells, refactoring, cleanup,
#   reducing complexity, or improving code structure.
# type: rigid
# references:
#   - CLAUDE.md [STANDARDS]
#   - CLAUDE.md [ARCHITECTURE]
# ---

# Refactoring Skill

## Purpose

Improve code structure, readability, and maintainability without changing
external behavior. This is a RIGID skill — every step must be followed in
exact order. Skipping steps leads to broken code and silent behavior changes.

## RIGID WORKFLOW — Follow Exactly, Do Not Skip Steps

### Step 1: STOP — Do NOT Refactor Without Tests

**This step is non-negotiable.** Before touching any code:

1. Check if tests exist for the code you plan to refactor
2. Run the existing tests to confirm they pass
3. Assess test coverage of the specific code paths you will change

**If tests do not exist or coverage is insufficient:**

- STOP refactoring
- Write tests FIRST that capture the current behavior
- Tests must cover:
  - All public methods/functions being refactored
  - Edge cases and error paths
  - Integration points with other modules
  - Any behavior that callers depend on
- Run the new tests and confirm they pass against the CURRENT code
- Only then proceed to Step 2

```python
# Example: Before refactoring UserService.create_user(), ensure tests exist:
class TestUserServiceCreateUser:
    def test_creates_user_with_valid_data(self):
        result = service.create_user(name="Alice", email="alice@example.com")
        assert result.name == "Alice"
        assert result.email == "alice@example.com"

    def test_raises_on_duplicate_email(self):
        service.create_user(name="Alice", email="alice@example.com")
        with pytest.raises(DuplicateEmailError):
            service.create_user(name="Bob", email="alice@example.com")

    def test_raises_on_invalid_email(self):
        with pytest.raises(ValidationError):
            service.create_user(name="Alice", email="not-an-email")

    def test_sends_welcome_email(self, mock_email):
        service.create_user(name="Alice", email="alice@example.com")
        mock_email.send.assert_called_once()
```

### Step 2: Identify the Code Smell

Inspect the code and classify the problem. Common code smells and their
indicators:

| Code Smell              | Indicators                                                    |
|-------------------------|---------------------------------------------------------------|
| **Long Method**         | Method > 20 lines; does multiple things; hard to name         |
| **God Class**           | Class > 300 lines; too many responsibilities; too many fields |
| **Feature Envy**        | Method uses another class's data more than its own            |
| **Shotgun Surgery**     | One change requires editing many files/classes                |
| **Data Clumps**         | Same group of parameters appears in multiple methods          |
| **Primitive Obsession** | Using primitives instead of small objects (Money, Email, etc) |
| **Long Parameter List** | Method takes > 3 parameters                                  |
| **Divergent Change**    | One class is changed for multiple unrelated reasons           |
| **Switch Statements**   | Repeated switch/if-else on same type discriminator            |
| **Refused Bequest**     | Subclass does not use most of parent's methods                |
| **Dead Code**           | Unreachable code, unused variables, commented-out blocks      |
| **Duplicate Code**      | Same or very similar logic in multiple places                 |

Document the specific smell, its location, and why it is a problem.

### Step 3: Explore All Callers and Consumers

Before changing anything, understand the full impact surface:

1. **Find all callers** of the function/method/class being refactored:
   - Use grep/ripgrep to find all references
   - Check imports across the codebase
   - Search for dynamic calls (string-based lookups, reflection)
2. **Check for external consumers**:
   - Is this a public API? Are external services calling it?
   - Is this used in configuration files, scripts, or templates?
   - Are there serialized forms that depend on class/field names?
3. **Map the dependency graph**:
   - What does this code depend on?
   - What depends on this code?
   - Are there circular dependencies?
4. **Identify contracts**:
   - What are the implicit contracts (return types, side effects, ordering)?
   - What will break if the signature or behavior changes?

### Step 4: Choose the Refactoring Technique

Select the appropriate technique based on the identified code smell:

#### Extract Method / Extract Class
**Use for:** Long methods, god classes, methods doing multiple things

```python
# BEFORE: Long method
def process_order(order):
    # validate
    if not order.items:
        raise ValueError("Empty order")
    if order.total < 0:
        raise ValueError("Negative total")
    # calculate discount
    discount = 0
    if order.customer.is_premium:
        discount = order.total * 0.1
    if order.total > 100:
        discount += order.total * 0.05
    # apply and save
    order.total -= discount
    db.save(order)
    email.send_confirmation(order)

# AFTER: Extracted methods
def process_order(order):
    validate_order(order)
    discount = calculate_discount(order)
    apply_discount_and_save(order, discount)
    email.send_confirmation(order)
```

#### Replace Conditional with Polymorphism
**Use for:** Complex if/else chains, switch statements on type

```python
# BEFORE: Switch on type
def calculate_shipping(order):
    if order.type == "standard":
        return order.weight * 0.5
    elif order.type == "express":
        return order.weight * 1.5 + 10
    elif order.type == "overnight":
        return order.weight * 3.0 + 25

# AFTER: Polymorphism
class ShippingCalculator(ABC):
    @abstractmethod
    def calculate(self, order): ...

class StandardShipping(ShippingCalculator):
    def calculate(self, order):
        return order.weight * 0.5

class ExpressShipping(ShippingCalculator):
    def calculate(self, order):
        return order.weight * 1.5 + 10
```

#### Introduce Parameter Object
**Use for:** Long parameter lists, data clumps

```python
# BEFORE: Too many parameters
def create_user(name, email, phone, street, city, state, zip_code, country):
    ...

# AFTER: Parameter object
@dataclass
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str

def create_user(name: str, email: str, phone: str, address: Address):
    ...
```

#### Move Method
**Use for:** Feature envy — method uses another class more than its own

#### Replace Inheritance with Composition
**Use for:** Rigid class hierarchies, refused bequest

```python
# BEFORE: Inheritance
class FileLogger(Logger):
    ...  # only uses 2 of 15 Logger methods

# AFTER: Composition
class FileLogger:
    def __init__(self, formatter: LogFormatter):
        self.formatter = formatter
```

#### Apply Strategy / Factory / Observer Pattern
**Use for:** When a well-known design pattern cleanly fits the problem

- **Strategy**: When algorithm varies by context (sorting, pricing, validation)
- **Factory**: When object creation logic is complex or varies by type
- **Observer**: When multiple components react to the same event

### Step 5: Make ONE Small Change at a Time

**Critical rule: one change per step.** A single change is:

- Extract one method
- Move one function to a new module
- Rename one variable/method
- Replace one conditional branch with a polymorphic class
- Inline one unnecessary abstraction

Do NOT batch multiple changes together. Each change must be independently
verifiable.

### Step 6: Run Tests After Each Change

After completing the single change from Step 5:

1. Run the unit tests for the affected module
2. Confirm all tests pass
3. If any test fails:
   - The change introduced a behavior difference
   - Revert the change immediately
   - Analyze why it broke
   - Adjust approach and try again
4. If all tests pass, the change is safe — commit mentally and proceed

### Step 7: Repeat Steps 5-6 Until Refactoring Is Complete

Continue the cycle of small changes + test runs until the full refactoring
is done. Track progress:

- [ ] Change 1: [describe] -- tests pass
- [ ] Change 2: [describe] -- tests pass
- [ ] Change 3: [describe] -- tests pass
- ...

If at any point tests fail and you cannot resolve it, stop and reassess the
overall refactoring approach.

### Step 8: Run Full Test Suite

After all individual changes are complete:

1. Run the entire project test suite, not just the affected module
2. Include integration tests, end-to-end tests, and any contract tests
3. If any test fails that was not in the immediate scope, investigate:
   - Did the refactoring change a subtle behavior?
   - Is there an implicit dependency you missed in Step 3?
   - Fix the issue or revert the change that caused it

### Step 9: Review Against Project Standards

Verify the refactored code meets project guidelines:

1. **CLAUDE.md [STANDARDS]** compliance:
   - Naming conventions followed
   - Code organization matches project structure
   - Error handling patterns used correctly
   - Logging and documentation standards met
2. **CLAUDE.md [ARCHITECTURE]** compliance:
   - Module boundaries respected
   - Dependency direction correct (no circular deps introduced)
   - Layer separation maintained (controller/service/repository)
   - Patterns used consistently with the rest of the codebase
3. **General quality**:
   - Cyclomatic complexity reduced
   - Methods are shorter and have single responsibility
   - Names clearly communicate intent
   - No dead code left behind

### Step 10: Final Verification

Complete the final verification checklist:

- [ ] All tests pass (unit, integration, e2e)
- [ ] No behavior has changed (same inputs produce same outputs)
- [ ] Code is cleaner, simpler, or more maintainable than before
- [ ] No new warnings or linting errors introduced
- [ ] Removed code is truly unused (not referenced anywhere)
- [ ] Changes are consistent with CLAUDE.md [STANDARDS] and [ARCHITECTURE]

## Enforced Standards

### Google-Style Docstrings (MANDATORY)
Every function, method, and class written or modified during refactoring MUST have a Google-style docstring. No exceptions. This includes:
- One-line summary in imperative mood
- Args section for all parameters
- Returns section describing what is returned
- Raises section for all exceptions
- See CLAUDE.md [STANDARDS] for full specification and examples.

### Git Commit Format (MANDATORY)
All commits created during refactoring MUST follow this format:
- **Signed commits**: Always use `git commit -S`
- **Semantic prefix**: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `ci:`
- **File-change table** in the commit body:
  ```
  type: concise description

  | File (Location) | Summary of Change |
  |---|---|
  | path/to/file.py | What changed in this file |

  Author: PrabhukumarSivamoorthy@gmail.com
  ```
- See CLAUDE.md [GIT] for full specification.

## Rules

1. **Never refactor without tests.** If tests are missing, write them first.
2. **Never change behavior during refactoring.** If you need to change behavior,
   that is a separate task — do it before or after refactoring, not during.
3. **One small change at a time.** Verify after each change.
4. **If tests break, revert immediately.** Do not fix forward blindly.
5. **This workflow is rigid.** Do not skip steps, reorder steps, or combine
   steps. Each step exists for a reason.
