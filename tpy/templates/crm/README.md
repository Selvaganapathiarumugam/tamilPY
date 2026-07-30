# CRM starter

Models companies, contacts, deals, and activities with stage/type enums.

## Relations

- Company → has_many Contact
- Contact → has_many Deal
- Deal → has_many Activity

## Next steps

```bash
tpy build --skip-db
tpy migrate
tpy seed
tpy serve
tpy admin
```
