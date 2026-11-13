# prediction: rules for every session

Research question: can a simple, pre-registered rule make money on Kalshi or Polymarket after real costs? A "no" is a good outcome.
Owner: Amit (Israel, under $5,000, free tools only, small token budget). Use plain, short language and explain jargon.

## Hard rules
- Paper only. No order-placing code until Amit writes otherwise.
- Pre-register every idea in `research/prereg/PMn.md` BEFORE any outcome data is read. Never edit a plan after results exist.
- One primary test per idea. Extra cuts are labelled exploratory and never count as a pass.
- Compare to a random control. Use real costs: buy at the ask, sell at the bid, plus fees. Never midpoint or last trade.
- Point-in-time data only. No look-ahead.
- Holdout: the most recent ~25% of events by date stays untouched until the one final test.
- LLM-derived features only count on markets that resolved after that model's training cutoff.
- Count events, not contracts. Report the effective sample size.
- Never print or log secrets. Free tools only. Say when something paid would help, don't buy it.
- No platform building: no dashboards, ledgers, multiple models or paper accounts until one idea passes on unseen data. The ML pipeline in the brief (Step 4) is parked until then.
- Never suggest a VPN or any way around access limits.

## Process agreed with Amit (11 Nov 2026)
- One step per session. Each ends with a short report Amit signs off. About 40 tool calls per session.
- Show funnel counts (pulled, kept, dropped and why) BEFORE computing any returns.
- Never swap an idea without telling Amit first. New ideas join a queue (PM2, PM3...), each with its own plan and his OK, run one at a time.
- No cap on ideas, but the pass bar rises with each idea tried: t >= 3.0 for the 1st, 3.2 for the 2nd, 3.3 for the 3rd, about 3.6 by the 10th.
- Any pass must be confirmed on new data (forward logger) before real money is discussed.
- A near-miss may be retried only with the same rule, untouched, on data that did not exist at the first test, with Amit's OK. It counts as one more idea.
- Dollar floor: an edge must plausibly net $100 a month on $5,000 at small fill sizes. More is welcome. Below the floor, stop even on a pass.
- Fills assume small size at the best quote. Order-book depth history is not free, so capacity is an open question.
- Use the skills `preregistered-study` and `prediction-market-data-qa` when available.

## Status log
- Ideas tried: 1. PM1 FAILED on the holdout 12 Nov 2026 (-5.1 cents per contract, t = -24): see `research/step3_pm1_result.md`. Holdout days up to 9 Nov 2026 are now used.
- Step 1 (eligibility) done 11 Nov 2026: see `research/step1_eligibility.md`. Not a hard no on either platform. Israeli tax treatment is an open risk for a professional.
- Step 2 done and signed off 12 Nov 2026: see `research/step2_data_checks.md`. PM1 Amendment 1 (section 17) approved by Amit before any outcome data: Sports, holdout = snapshot days from 18 Jun 2026, two bug fixes. Next: Step 3, the one test, in a new session. Listings are saved in the project Library under `data/`.
- Kalshi pull notes: go series by series (an unfiltered pull is ~100k markets a day); the full listing pull takes about 3 hours and is not stored in the repo.
- Amit (11 Nov 2026): has an account; tax is closed on his side.
