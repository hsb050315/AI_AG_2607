# Notion DB Creation & API Connection Guide

A step-by-step guideline for creating a Notion database and connecting it to your own tooling via the Notion API. Follow the sections in order.

## 1. Prerequisites

- A Notion account with permission to create integrations (workspace member; for internal integrations an workspace owner may need to approve).
- The workspace/page where the target database will live.
- A place to store secrets (`.env` file, secret manager). Never commit the token.

## 2. Create the Integration

1. Go to https://www.notion.so/my-integrations
2. Click **New integration**.
3. Set:
   - **Name**: e.g. `AI_AG_2607-bot`
   - **Associated workspace**: select the correct workspace.
   - **Type**: *Internal* (default). Use *Public* only if third parties will authorize it via OAuth.
4. Under **Capabilities**, enable what you need:
   - Read content
   - Update content
   - Insert content
   - (Optional) Read user information — only if you must resolve people.
5. Click **Save**.

## 3. Get the API Token

- After saving, open the integration's **Configuration** tab.
- Copy the **Internal Integration Secret** (starts with `ntn_` for new tokens, older ones start with `secret_`).
- Store it as an environment variable, e.g.:

```
NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- The token inherits the capabilities you selected. Rotating: return to Configuration → **Regenerate**.

## 4. Create the Database in Notion

1. In Notion, open the parent page that will hold the database.
2. Type `/database` → choose **Table view - Full page** (or inline).
3. Define the schema (properties). Recommended baseline:

| Property | Type | Notes |
|----------|------|-------|
| Name | Title | Required, always present |
| Status | Status or Select | e.g. Todo / In progress / Done |
| Date | Date | Due date or event date |
| Tags | Multi-select | Categorization |
| Owner | People | Assignee |
| Notes | Rich text | Free text |

4. Property names and types matter — the API references properties by **name** (and type). Keep names stable.

## 5. Share the Database with the Integration

The integration has **no access** until you explicitly connect it.

1. Open the database as a full page.
2. Click the **•••** menu (top-right) → **Connections** (or **+ Add connections**).
3. Search for your integration name → select it → **Confirm**.
4. The integration now has access to this database and all its child pages.

> If the database is nested under a page you share, access is inherited. Sharing at the highest sensible level is fine, but scope tightly for least privilege.

## 6. Get the Database ID

The database ID is a 32-character UUID.

- Open the database as a full page in the browser.
- URL looks like:
  `https://www.notion.so/<workspace>/<DATABASE_ID>?v=<VIEW_ID>`
- The `DATABASE_ID` is the 32 hex chars before `?v=`. Format with dashes (8-4-4-4-12) or send raw — the API accepts both.

Store it:

```
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 7. Verify the Connection

All requests need these headers:

| Header | Value |
|--------|-------|
| `Authorization` | `Bearer <NOTION_API_KEY>` |
| `Notion-Version` | `2022-06-28` (current stable) |
| `Content-Type` | `application/json` |

### Retrieve the database (schema check)

```bash
curl https://api.notion.com/v1/databases/$NOTION_DATABASE_ID \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28"
```

A `200` with the property list confirms the token + sharing are correct.
A `404` almost always means the database was not shared with the integration (step 5).

### Query rows

```bash
curl -X POST https://api.notion.com/v1/databases/$NOTION_DATABASE_ID/query \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{ "page_size": 5 }'
```

### Create a row (page)

```bash
curl -X POST https://api.notion.com/v1/pages \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": { "database_id": "'"$NOTION_DATABASE_ID"'" },
    "properties": {
      "Name":   { "title": [ { "text": { "content": "First item" } } ] },
      "Status": { "status": { "name": "Todo" } },
      "Date":   { "date": { "start": "2026-08-27" } },
      "Tags":   { "multi_select": [ { "name": "demo" } ] }
    }
  }'
```

## 8. Property Value Shapes (cheat sheet)

| Type | Write shape |
|------|-------------|
| Title | `{ "title": [ { "text": { "content": "..." } } ] }` |
| Rich text | `{ "rich_text": [ { "text": { "content": "..." } } ] }` |
| Number | `{ "number": 42 }` |
| Select | `{ "select": { "name": "Option" } }` |
| Multi-select | `{ "multi_select": [ { "name": "A" }, { "name": "B" } ] }` |
| Status | `{ "status": { "name": "In progress" } }` |
| Date | `{ "date": { "start": "2026-08-27", "end": null } }` |
| Checkbox | `{ "checkbox": true }` |
| People | `{ "people": [ { "id": "<user_id>" } ] }` |
| URL / Email / Phone | `{ "url": "https://..." }` etc. |
| Relation | `{ "relation": [ { "id": "<page_id>" } ] }` |

## 9. Common Pitfalls

- **404 on a resource you can see in the UI** → integration not added via Connections.
- **`Notion-Version` missing** → 400. Always send it.
- **Property name mismatch** → 400 "is not a property that exists". Names are case-sensitive and must match exactly.
- **Select/Status option doesn't exist** → for Select/Multi-select the API can create new options; for **Status** it cannot — the option must already exist in the DB.
- **Rate limit** → ~3 requests/sec average. Handle `429` with `Retry-After`.
- **Pagination** → responses cap at 100 items; loop using `next_cursor` / `has_more`.
- **Token leak** → keep out of git (`.env` is already gitignored patterns; verify), rotate immediately if exposed.

## 10. Recommended Project Setup

```
.env                  # NOTION_API_KEY, NOTION_DATABASE_ID  (git-ignored)
scripts/notion/        # API helper scripts
```

Load `.env` in scripts; never hard-code the token. For CI, inject the token as a masked secret.

## Official References

- Integrations dashboard: https://www.notion.so/my-integrations
- API docs: https://developers.notion.com/reference/intro
- Create a page: https://developers.notion.com/reference/post-page
- Query a database: https://developers.notion.com/reference/post-database-query
- Working with databases guide: https://developers.notion.com/docs/working-with-databases
