---
name: Student Financial Dashboard
description: Calm campus wayfinding for everyday student finances.
colors:
  forest: "#17644D"
  expense-orange: "#B45A31"
  paper: "#F7F8F2"
  sage: "#E8EEE2"
  summary-sage: "#E0EDDF"
  ink: "#183C30"
  muted: "#52685D"
  metric-label: "#345441"
  sidebar-border: "#D5DFCE"
  selection: "#CDE7CE"
typography:
  display:
    fontFamily: '"Source Serif Pro", "Yu Mincho", "Hiragino Mincho ProN", Georgia, serif'
    fontSize: "clamp(2rem, 3vw, 3rem)"
    fontWeight: 600
    letterSpacing: "-0.025em"
  sidebar-title:
    fontFamily: '"Source Serif Pro", "Yu Mincho", "Hiragino Mincho ProN", Georgia, serif'
    fontSize: "1.65rem"
    fontWeight: 600
  title:
    fontSize: "1.25rem"
    letterSpacing: "-0.015em"
  body:
    fontFamily: "sans-serif"
  metric:
    fontSize: "clamp(1.3rem, 2.5vw, 2.1rem)"
rounded:
  summary: "14px"
  history-bar: "3px"
  category-bar: "4px"
spacing:
  compact: "1rem"
  medium: "1.25rem"
  summary-block: "1.3rem"
  summary-inline: "1.5rem"
  welcome: "2rem"
  page-top: "2.5rem"
components:
  summary-band:
    backgroundColor: "{colors.summary-sage}"
    rounded: "{rounded.summary}"
    padding: "1.3rem 1.5rem"
  welcome-panel:
    backgroundColor: "{colors.summary-sage}"
    rounded: "{rounded.summary}"
    padding: "{spacing.welcome}"
  sidebar:
    backgroundColor: "{colors.sage}"
  metric:
    textColor: "{colors.ink}"
    typography: "{typography.metric}"
---

# Design System: Student Financial Dashboard

## Overview

**Creative North Star: "Campus Botanical Wayfinding"**

A quiet student workspace uses warm paper, sage navigation and forest accents to make financial records approachable. Botanical character comes from color and typography; controls remain familiar Streamlit components. Clear labels and visible amounts carry the meaning.

**Key Characteristics:**
- Pale tonal surfaces with restrained green emphasis.
- Serif product titles paired with native bundled sans text.
- Readable financial values and straight progress tracks.

## Colors

### Primary
- **Forest:** primary actions, income series, category bars and progress feedback.

### Secondary
- **Expense Orange:** expenses in the paired income/expense history chart.

### Neutral
- **Paper:** main page canvas.
- **Sage:** sidebar and native secondary surfaces.
- **Summary Sage:** monthly metric band.
- **Ink:** headings, body text and metric values.
- **Muted:** captions and chart labels; captions retain full opacity.
- **Metric Label:** summary labels.
- **Sidebar Border:** quiet division between navigation and content.
- **Selection:** selected text background with ink text.

**The Semantic Pair Rule.** Preserve forest for income and orange for expenses in comparative history. A single-series category chart stays forest. Native warning and error colors communicate exceptional states.

## Typography

Product and page titles use bundled Source Serif Pro with installed Japanese Mincho faces (Yu Mincho / Hiragino Mincho ProN) and Georgia/serif fallbacks. Body text uses Streamlit's bundled sans-serif theme and system Japanese fallback; avoid an external font dependency. Smaller section headings inherit the native Streamlit family. Japanese is the initial language; account settings also support English and Indonesian. Preserve the layout and hierarchy in all three languages. Use comma-grouped yen, Japanese YYYY年M月 and localized year/month periods.

Use the frontmatter display scale for page titles and sidebar-title for the navigation title. Section titles use the title scale. Metrics use the metric scale and tabular numerals; tables also use tabular numerals. At the compact breakpoint metric values use (1.7rem). Heading levels two and three share the title letter spacing.

## Layout

The wide Streamlit page has a maximum content width of (1440px), page-top spacing above and compact spacing below. Native columns and their responsive behavior own the grid. The current overview places four values in one summary band, then unequal history/goal and category/recent-record columns. These arrangements are surface patterns, not mandatory templates for every screen.

At widths up to (700px), content padding becomes medium vertically and compact horizontally; summary padding becomes compact. Keep dataset selection and task navigation in the native sidebar and the month selector near the page title. Preserve visible demo/private context.

## Elevation & Depth

Custom surfaces use tonal layering without added shadows. Paper, sage and summary sage establish hierarchy; the sidebar has a thin separating border. Keep native Streamlit overlays and interaction feedback intact. Motion is native control feedback only.

## Shapes

The summary band has gently curved corners using the summary radius. History bars round their top corners using history-bar; category bars round their ends using category-bar. Native controls keep their framework shapes. Progress tracks remain straight horizontal measures rather than decorative gauges.

## Components

### Summary band
A shared tonal container groups monthly values with summary-block/summary-inline padding and compact spacing above. Labels remain subdued; values remain ink and tabular.

### Login and account settings
Login pairs a sage welcome panel (14px radius, 2rem padding) with native login/register tabs and forms. On compact screens, panel padding is 1rem and supplementary welcome paragraphs/divider are hidden so the form remains reachable. Headings and the local-use caption stay visible. Settings extends the same native form language, with an explicit language-save action. Sidebar settings/logout use Material icons and translated labels.

### Buttons and inputs
Use native Streamlit buttons, form controls, tabs and selectors. Primary submissions use the forest theme. Preserve native hover, disabled and error behavior. Buttons, inputs and textareas receive a forest focus outline (2px) with an offset (3px); caret color is forest.

### Charts and progress
History uses paired forest/orange bars, bottom legend, readable muted axis labels and value tooltips. Category bars use forest. Progress tracks retain adjacent numeric values and explanatory text, including when their visual fill reaches its limit.

### Navigation and records
Use sidebar radio navigation with native selected states. Tables retain native sorting, scrolling and density; monetary columns use tabular figures. Captions provide secondary explanation without opacity reduction.

## Do's and Don'ts

### Do:
- **Do** reuse the palette and native controls before adding custom components.
- **Do** pair progress and chart color with labels and numeric values.
- **Do** preserve visible keyboard focus, readable captions and compact-screen padding.

### Don't:
- **Don't** add ornamental shadows, entrance animation or external font loading.
- **Don't** replace familiar financial forms with themed novelty controls.
- **Don't** use low-opacity captions or depend on color alone for financial meaning.
