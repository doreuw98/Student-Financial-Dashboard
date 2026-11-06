---
name: Student Financial Dashboard
description: A local student finance dashboard based on the Purple reference.
colors:
  purple: "#A05AFF"
  purple-ink: "#7430B8"
  purple-hover: "#62289D"
  canvas: "#F2EDF5"
  secondary-surface: "#F8F6FC"
  white: "#FFFFFF"
  ink: "#342E42"
  muted: "#6B6477"
  metric-ink: "#2F253A"
  metric-label: "#43364E"
  pink: "#FE9496"
  pink-end: "#F77BB0"
  blue: "#4BCBEB"
  blue-end: "#7CB4FC"
  teal: "#1BCFB4"
  teal-end: "#68DDD0"
  chart-grid: "#F0EDF5"
  selection: "#E6D3FF"
  sidebar-control-border: "#E9E2F3"
  form-border: "#E8E1EF"
  chart-violet: "#9E58FF"
  chart-lilac: "#CDB4FF"
typography:
  body:
    fontFamily: '"Source Sans Pro", "Yu Gothic", "Hiragino Kaku Gothic ProN", sans-serif'
  title:
    fontSize: "clamp(1.45rem, 2vw, 1.8rem)"
    fontWeight: 650
    letterSpacing: "-0.02em"
  section:
    fontSize: "1.05rem"
    fontWeight: 600
  metric:
    fontSize: "clamp(1.35rem, 2.3vw, 2rem)"
  compact-metric:
    fontSize: "1.6rem"
  summary-metric:
    fontSize: "clamp(1.7rem, 2.5vw, 2.25rem)"
    fontWeight: 650
rounded:
  topbar: "6px"
  panel: "8px"
  metric-card: "9px"
  welcome: "10px"
  chart-mark: "2px"
spacing:
  compact: "1rem"
  panel: "1.4rem"
  welcome: "2rem"
components:
  topbar:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.topbar}"
    padding: "0.7rem 1.5rem"
  content-panel:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel}"
  summary-card:
    textColor: "{colors.metric-ink}"
    typography: "{typography.summary-metric}"
    rounded: "{rounded.metric-card}"
    padding: "1.3rem 1.4rem 1rem"
  welcome-panel:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.welcome}"
    padding: "{spacing.welcome}"
  button-primary:
    backgroundColor: "{colors.purple-ink}"
    textColor: "{colors.white}"
  button-primary-hover:
    backgroundColor: "{colors.purple-hover}"
---

# Design System: Student Financial Dashboard

## Overview

**Creative North Star: "Purple Dashboard"**

The user-selected Purple reference informs the light lilac canvas, white navigation and content panels, and three bright financial summary cards. Use these accents to separate the monthly snapshot from the detailed figures underneath. Keep interactive controls native to Streamlit.

## Colors

Purple is the theme accent. Deep purple marks primary buttons, keyboard focus and prominent sidebar or welcome headings. Canvas lilac frames white content surfaces. Use dark ink for figures and muted plum for captions and chart labels. Keep captions at full opacity.

Summary colors identify the cards by position and text: pink for income, blue for expenses and teal for monthly balance. Chart colors serve a separate role. The trend compares purple income with pink expenses. The category donut uses a multicolor palette with a text legend and amount tooltips.

## Typography

Use Source Sans Pro with Yu Gothic, Hiragino Kaku Gothic ProN and generic sans fallbacks. Headings use a compact scale and amounts use tabular numerals. The summary values have the strongest numeric emphasis. Japanese is the initial language, with English and Indonesian also supported. Retain comma-grouped yen and localized month labels.

## Layout

Keep the content within 1440px. The signed-in view opens with a slim white brand and account bar, followed by the page heading and month selector. The dashboard places three equal summary cards above the trend and category chart panels in a 1.65:1 grid. Recent records and goal progress follow in the same grid. The sidebar contains dataset, page, settings and sign-out controls.

At widths up to 700px, native columns reflow and outer padding leaves room for the sidebar control. Reduce the topbar, content panel and welcome padding. Summary cards use a shorter minimum height. Keep headings and the local-use caption visible when hiding supplementary welcome paragraphs and the divider.

## Elevation & Depth

Use white surfaces on lilac and rely on contrast and spacing to separate panels. Summary gradients and their clipped translucent circles supply the decorative depth. Preserve native interaction feedback and avoid custom entrance motion.

## Shapes

Use small rounded corners for the topbar, content panels, summary cards and welcome panel. Chart marks use gentle rounding. Keep progress tracks horizontal and native.

## Components

### Summary cards

Use three colored cards with a metric label, a tabular yen value and the selected month. Each uses a 115-degree gradient and a translucent white circle clipped to the top right. The circle is decorative and does not intercept input.

### Charts and records

Place grouped trend bars and the category donut in separate white panels with bottom legends. Keep tooltips and muted labels. Use the native table for records and retain the explicit numeric values and explanatory text around progress tracks.

### Account surfaces

Pair the white welcome panel with native login and registration tabs. Settings uses a native form and explicit language save. The sidebar keeps translated settings and sign-out labels with their Material icons. Preserve the deep purple keyboard outline for buttons and form inputs.

## Do's and Don'ts

- **Do** keep the lavender canvas, white panels and colored summary cards in their distinct roles.
- **Do** use chart labels, legends and tooltips to explain financial values.
- **Don't** use chart series colors as replacements for the summary card palette.
- **Don't** let decorative marks interrupt focus or readability.
