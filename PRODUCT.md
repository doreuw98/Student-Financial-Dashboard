# Student Financial Dashboard
<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
Python + Streamlit, selected by the user. Local development in VS Code; GitHub backup after review.

## Users and purpose
Students managing monthly finances; also a classroom presentation and Python learning project.

## Capabilities and constraints
Original conversation specifies Japanese yen, income/expense overview, category analysis, monthly trends, budgets, savings goals, transaction add/edit/delete and spending insights.
Data stays on the user's computer; secrets and personal financial records must not enter Git.

## Delegated decisions
User asked to continue all work with attractive UI and concise code. Builder chooses a light green-accented interface, SQLite persistence and an isolated, clearly marked demo dataset. User now requests SQLite-backed local registration/login and a settings button in the left sidebar. No bank connection or public/cloud deployment is requested.

## Presentation language
Japanese is the initial presentation language. User subsequently requests Japanese/English/Indonesian switching from sidebar Settings. Store each account's choice in SQLite. Translate application labels, charts, exports, messages and synthetic demo notes; preserve user-written notes, stored type/category identifiers and JPY currency.

User clarified that the same account must retain exactly the same finances across languages. The language selected on signup/login is authoritative for the dashboard and updates the account preference. Successful login opens personal records; synthetic demo remains an explicit sidebar option. Language never participates in financial database paths or account identity.

## Local account boundaries
Passwords use salted scrypt hashes. Usernames are normalized ASCII identifiers; display names may include Japanese. Authentication is required before any dashboard reads. Each server-validated user ID owns a separate private/demo database pair under data/private/users/. Existing unowned legacy databases remain untouched and are not assigned to the first registrant. Accounts are local to this computer, not internet identities. No shared default account, email verification or password recovery is provided.

## Evidence
Only synthetic demonstration data is supplied. Do not present it as the user's finances.

## Principles
Readable Python, a small number of modules, meaningful calculations, accessible native controls, explicit demo/private separation.

## Approved visual reference
User explicitly replaces the prior sage/forest look with the supplied Purple dashboard screenshot: white sidebar/top bar and content panels, pale lavender canvas, three pink/blue/teal summary cards, bar chart and doughnut distribution. Pinned palette: primary #A05AFF and #1BCFB4; supporting #4BCBEB, #FE9496, #9E58FF. Keep the product's real financial data and account/language behavior. Use dark text on bright cards for readable contrast; do not invent reference screenshot sales/traffic statistics.
