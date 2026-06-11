# Multi-account Zoho setup

This fork supports two static Zoho Analytics accounts for local/self-hosted use.

## Environment variables

Use `docker/.env.example` as the template.

Account 1 can use either the original variable names or the new suffixed names,
but the suffixed names are recommended:

```env
ANALYTICS_ACCOUNT_1_ALIAS=gran_azul
ANALYTICS_CLIENT_ID_1=
ANALYTICS_CLIENT_SECRET_1=
ANALYTICS_REFRESH_TOKEN_1=
ANALYTICS_ORG_ID_1=20103657962
ACCOUNTS_SERVER_URL_1=https://accounts.zoho.eu
ANALYTICS_SERVER_URL_1=https://analyticsapi.zoho.eu
```

Account 2 uses:

```env
ANALYTICS_ACCOUNT_2_ALIAS=cuenta_2
ANALYTICS_CLIENT_ID_2=
ANALYTICS_CLIENT_SECRET_2=
ANALYTICS_REFRESH_TOKEN_2=
ANALYTICS_ORG_ID_2=
ACCOUNTS_SERVER_URL_2=https://accounts.zoho.eu
ANALYTICS_SERVER_URL_2=https://analyticsapi.zoho.eu
```

Set `ANALYTICS_DEFAULT_ACCOUNT=1` or `2` to choose which account is used when
the MCP tool call does not include `account`.

## Calling tools

Every Zoho tool that talks to Analytics now accepts an optional `account`
argument.

Examples:

```json
{
  "include_shared_workspaces": false,
  "account": "gran_azul"
}
```

```json
{
  "workspace_id": "123456789",
  "sql_query": "SELECT * FROM \"Ventas\" LIMIT 20",
  "account": "2"
}
```

Valid account values are:

- `1`
- `2`
- `account_1`
- `account_2`
- the aliases configured in `ANALYTICS_ACCOUNT_1_ALIAS` and `ANALYTICS_ACCOUNT_2_ALIAS`

## Railway

In Railway, add the variables from `docker/.env.example` in the project
Variables tab. Do not upload a real `.env` file with secrets to GitHub.

This fork includes a root `Dockerfile` for Railway. It starts the static
credentials HTTP server and exposes the MCP endpoint at:

```text
https://your-railway-domain.up.railway.app/mcp
```

Use the root of the GitHub repo as the Railway project source. Railway should
detect the root `Dockerfile` automatically.

Required Railway variables:

```env
PORT=4000
ANALYTICS_DEFAULT_ACCOUNT=1
ANALYTICS_ACCOUNT_1_ALIAS=gran_azul
ANALYTICS_CLIENT_ID_1=
ANALYTICS_CLIENT_SECRET_1=
ANALYTICS_REFRESH_TOKEN_1=
ANALYTICS_ORG_ID_1=20103657962
ACCOUNTS_SERVER_URL_1=https://accounts.zoho.eu
ANALYTICS_SERVER_URL_1=https://analyticsapi.zoho.eu
ANALYTICS_ACCOUNT_2_ALIAS=cuenta_2
ANALYTICS_CLIENT_ID_2=
ANALYTICS_CLIENT_SECRET_2=
ANALYTICS_REFRESH_TOKEN_2=
ANALYTICS_ORG_ID_2=
ACCOUNTS_SERVER_URL_2=https://accounts.zoho.eu
ANALYTICS_SERVER_URL_2=https://analyticsapi.zoho.eu
ANALYTICS_MCP_DATA_DIR=/tmp/zoho-analytics-mcp
```
