tpy/templates/project/.gitignore# tamilPY (TPY Framework)

Schema-driven Python web framework by **Selvaganapathi Arumugam**.

## Install

```bash
pip install tamilPY
```

## Client flow

1. `tpy new myapp` — create the app  
2. Edit `schema.tpy` — define models  
3. `tpy build` — choose DB (SQLite / PostgreSQL / MySQL / MongoDB), enter connection details, generate code  
4. `tpy migrate` — apply migrations  
5. `tpy seed` — seed sample data  
6. `tpy serve` — run the API  

## Commands

| Command | Description |
|---------|-------------|
| `tpy new <name>` | Create a new project |
| `tpy build` | Interactive DB setup + generate app layers |
| `tpy build --skip-db` | Generate using existing `.env` |
| `tpy db configure` | Re-run DB wizard anytime |
| `tpy migrate` | Apply pending migrations |
| `tpy migrate rollback` | Roll back latest migration |
| `tpy seed` | Run `database/seeds` |
| `tpy serve` | Start FastAPI server |
| `tpy doctor` | Validate project structure |
| `tpy version` | Show framework version |

## Docs

Open [TamilPY](https://selvaganapathiarumugam.github.io/tamilPY/) for the full client guide.

## Author

**Selvaganapathi Arumugam**  
Software Developer
