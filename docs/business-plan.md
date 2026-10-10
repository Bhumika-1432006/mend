# Mend - business plan (built with cfo.ai)

The model was built in cfo.ai on 10 Oct 2026 and exported to
[`business-plan-cfo-ai.xlsx`](business-plan-cfo-ai.xlsx). It has three sheets: base vs growth,
an 18-month forecast, and the model inputs. This page summarises it. Every number below is in
the sheet.

## Inputs
| Input | Value | Source |
|---|---|---|
| Price | $49 per team per month, 20 repair rounds included, $2 per extra round | assumption |
| Cost per repair round | $1.50 (28 Haiku tasks at about $0.04, plus an Opus diagnosis at about $0.38) | built from our measured runs; the round total is an estimate |
| Infrastructure | $200 per month | assumption |
| Founders | 4; cfo.ai's model pays $2,000 per month each from April 2027 | assumption added in cfo.ai |
| Starting cash | $10,000 | assumption |
| Customers | Base: 50 teams, flat. Growth: 50 teams, +10% per month | assumption |

## What the model shows
- **Gross margin is 31%.** 20 included rounds at $1.50 is $30 of model cost per $49 team.
  Gross profit is $750 per month at 50 teams.
- **Runway:** Base closing cash peaks at $14,500 (March 2027), reaches $0 in May 2027 once
  founder pay starts, and ends at -$72,500 in March 2028. Growth reaches 252 teams and
  $12,383 monthly revenue by March 2028, but cash goes negative in June 2027 and ends at
  -$46,281.

## What we take from it
The price does not cover the cost per round. At $1.50 per round, each team adds about $15 of
gross profit per month. That means roughly 550 teams to cover $8,200 per month of payroll
and infrastructure (our arithmetic from the model's inputs). Two levers, both to model next
in cfo.ai:
1. **Cheaper rounds.** Our own self-repair round 1 already cut worker tokens by 8.8%, and
   fewer included rounds or smaller task suites reduce cost directly.
2. **Higher price.** At $99 per team with the same costs, gross profit is about $69 per team,
   so roughly 120 teams cover the same $8,200 (same arithmetic, not yet in cfo.ai).
