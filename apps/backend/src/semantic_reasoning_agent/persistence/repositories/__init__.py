"""ORM-backed repositories.

Each repository is the only place outside `infrastructure/` and `core/container.py`
that may import `sqlalchemy` or ORM types. Services consume repos for typed,
test-friendly access to durable state.

R2 introduces the layer with minimal methods. Services migrate over time;
the prior pattern of `database_manager.session()` calls inside services
remains valid until each service is refactored.
"""
