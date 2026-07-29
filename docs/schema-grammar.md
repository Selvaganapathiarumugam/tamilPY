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

## Relationships

Optional `relations { }` block inside a model (v0.1.9+):

```tpy
model User {
  id: uuid primary
  email: string unique required
  relations {
    has_many Post as posts
    has_one Profile as profile
    belongs_to_many AuthRole as roles through UserRole
  }
}

model Post {
  id: uuid primary
  user_id: uuid references User on_delete cascade
  title: string required
  relations {
    belongs_to User as author via user_id
  }
}
```

| Kind | Meaning | Notes |
|------|---------|--------|
| `belongs_to Model as name via fk` | Parent holds FK | `via` defaults to `model_id` |
| `has_many Model as name` | Related holds FK | FK defaults to `parent_id` |
| `has_one Model as name` | Same as has_many, one row | |
| `belongs_to_many Model as name through Pivot` | M2M via pivot model | Pivot model must exist in schema |

Eager load at runtime: `repo.query().with_("author", "tags").get()`.

## Comments

Lines starting with `#` are comments.

## Keywords

Keywords are case-insensitive (`model`, `Model`, `MODEL`).
