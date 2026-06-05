# Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview

The objective of this project is to build a **facts-only FAQ assistant** for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources, such as:
- **Asset Management Company (AMC)** websites
- **Association of Mutual Funds in India (AMFI)**
- **Securities and Exchange Board of India (SEBI)**

> [!IMPORTANT]
> The system must strictly avoid providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

---

## Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)**-based assistant that:
1. **Answers factual queries** about mutual fund schemes.
2. **Uses a curated corpus** of official documents.
3. **Provides concise, source-backed responses** directly to the user.

---

## Target Users

- **Retail Investors**: Individuals looking to compare mutual fund schemes based on objective data.
- **Customer Support & Content Teams**: Internal teams handling repetitive mutual fund queries who require quick and accurate information access.

---

## Scope of Work

### 1. Corpus Definition
- **Selected AMC**: HDFC Mutual Fund
- **Corpus Limit**: The corpus is currently limited to the following 5 Groww mutual fund scheme pages:
  - [HDFC Mid-Cap Opportunities Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)
  - [HDFC Top 100 Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth)
  - [HDFC Small Cap Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth)
  - [HDFC Gold ETF Fund of Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth)
  - [HDFC Defence Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth)

### 2. FAQ Assistant Requirements
The assistant must answer factual queries, including but not limited to:
- **Expense ratio** of a scheme
- **Exit load** details
- **Minimum SIP** amount
- **ELSS lock-in** period
- **Riskometer** classification
- **Benchmark index**
- **Fund management** data (e.g., fund manager names, experience, tenure, and other managed schemes)
- **Process** to download statements or capital gains reports

> [!IMPORTANT]
> **Response Quality Standards:**
> - Each response is limited to a **maximum of 3 sentences**.
> - Each response must include **exactly one citation link**.
> - Each response must include a footer:
>   `"Last updated from sources: <date>"`

### 3. Refusal Handling
The assistant **must refuse** non-factual or advisory queries, such as:
- *"Should I invest in this fund?"*
- *"Which fund is better?"*

**Refusal responses should:**
- Be polite and clearly worded.
- Reinforce the facts-only limitation.
- Provide a relevant educational link (e.g., AMFI or SEBI resource).

### 4. User Interface (Minimal)
The solution should include a simple, modern interface with:
- A welcome message.
- Three example questions to guide the user.
- A prominent and visible disclaimer:
  > **Facts-only. No investment advice.**

---

## Constraints

| Category | Constraint Details |
| :--- | :--- |
| **Data & Sources** | Use only official public sources (AMC, AMFI, SEBI). Do not use third-party blogs or aggregator websites. |
| **Privacy & Security** | **Do not** collect, store, or process: PAN, Aadhaar, Account numbers, OTPs, Email addresses, or Phone numbers. |
| **Content Restrictions** | No investment advice, opinions, recommendations, performance comparisons, or return calculations. For performance queries, provide a link to the official factsheet only. |
| **Transparency** | Responses must be short, factual, and verifiable. Every answer must include a source link and a "Last updated" date. |

---

## Expected Deliverables

1. **README Document**
   - Setup and installation instructions.
   - Selected AMC and schemes covered.
   - Architecture overview (RAG approach, models, database).
   - Known limitations.
2. **Disclaimer Snippet**
   - `"Facts-only. No investment advice."` clearly integrated.

---

## Success Criteria

* **Accurate Retrieval**: Correctly fetches factual mutual fund information.
* **Strict Compliance**: Zero instances of offering financial advice or speculative opinions.
* **Consistent Citations**: Every single fact-based response includes a valid, verifiable source link.
* **Robust Refusals**: Gracefully and politely refuses all subjective, comparative, or advisory queries.
* **Clean Interface**: A minimal, elegant, and user-friendly chat interface.

---

## Summary

The goal is to build a trustworthy, transparent, and compliant mutual fund FAQ assistant that **prioritizes accuracy over intelligence**. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
