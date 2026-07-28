# schema.tpy grammar (v0.1)

Versioned language reference for the tamilPY schema DSL. Breaking grammar
changes before 1.0 follow the deprecation policy in [versioning.md](versioning.md).

## File shape

```tpy
# optional provider
database sqlite | postgres | mysql | mongodb

model ModelName {
  field: type constraint...
}

# optional named enum (values become CHECK / string validation)
enum Status {
  draft
  published
  archived
}
```

## Field types

| Type | Notes |
|------|--------|
| `int` | Integer |
| `string` | Text / VARCHAR |
| `float` | Floating point |
| `bool` | Boolean |
| `uuid` | UUID (often primary key) |
| `datetime` | Timestamp |
| `enum(a, b, …)` | Inline enum values |
| `enum Status` | Reference a named `enum` block |

## Field constraints

| Constraint | Effect |
|------------|--------|
| `primary` | Primary key |
| `required` | Required on create API |
| `unique` | Column UNIQUE |
| `nullable` | Allows NULL |
| `index` | Secondary index |
| `default <literal>` | Default (`0`, `"x"`, `true`/`false`) |
| `references Model` | FK to `Model.id` |
| `references Model.col` | FK to specific column |
| `on_delete cascade\|set_null\|restrict\|no_action` | FK delete behavior |
| `on_update cascade\|set_null\|restrict\|no_action` | FK update behavior |

Foreign-key example:

```tpy
user_id: uuid references User on_delete cascade on_update restrict
```

## Model-level composite unique

```tpy
model Enrollment {
  id: uuid primary
  student_id: uuid references Student
  course_id: uuid references Course
  unique(student_id, course_id)
}
```

## Comments

Lines starting with `#` are comments.

## Keywords

Keywords are case-insensitive (`model`, `Model`, `MODEL`).
