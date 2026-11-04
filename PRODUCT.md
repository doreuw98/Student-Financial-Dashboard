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
User asked to continue all work with attractive UI and concise code. Builder chooses a light green-accented interface, SQLite persistence and an isolated, clearly marked demo dataset. No bank connection, authentication or cloud deployment is requested.

## Presentation language
User explicitly requests Japanese throughout the application for presentation. Use Japanese labels, chart text, messages and synthetic-demo descriptions; JPY thousands use commas and months use YYYY年M月. Preserve existing stored values and personal notes. English/Indonesian/Japanese language selection is planned for a later update before finalization; do not implement a language switcher yet.

## Evidence
Only synthetic demonstration data is supplied. Do not present it as the user's finances.

## Principles
Readable Python, a small number of modules, meaningful calculations, accessible native controls, explicit demo/private separation.
