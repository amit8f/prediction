# Step 1: Eligibility report (Israel resident)

Checked 11 Nov 2026. Ideas tried so far: 0. This is not legal or tax advice.

## Verdict

Not a hard "no". Neither platform's written terms exclude an Israel resident. The open risk is Israeli tax and gambling law, which could erase a small edge. That needs a professional before any real money, but it doesn't block the research.

## Polymarket (international site)

Israel is not on the restricted list. The Terms of Use (effective 11 Aug 2026) define restricted places by the list in Polymarket's docs. That list has three groups: fully blocked (Iran, Syria, Cuba, North Korea, parts of Ukraine), "close-only" (38 places including the US, UK, France, Germany, Lebanon, Iraq), and close-only on the website only (Ireland, Japan, Netherlands, South Korea, Malta for sports). Israel (IL) is in none of them.

Lines from the Terms of Use:

- "IF YOU ARE A RESTRICTED PERSON, THEN DO NOT ATTEMPT TO USE THE SITE, PLATFORM OR ANY OF THE TECHNOLOGY FEATURES TO TRADE."
- "You do not, and will not, use VPN software or any other privacy or anonymization tools or techniques to circumvent" the restrictions.
- You "will comply with all Applicable Laws". So the terms push Israeli-law compliance onto you.
- "It is your sole responsibility to determine whether there are any tax consequences from any transactions you initiate."

Automated trading: the terms ban using "data mining tools, robots, crawlers, or similar data gathering and extraction tools to scrape" the site. They don't address trading bots directly. Polymarket publishes an official trading API, and its geoblock page describes API orders as a normal path. My reading is that API trading from a personal account is allowed and scraping the website is not. The terms also limit data access for some professional firms, which doesn't apply to an individual.

Funding and withdrawal: the terms have no funding section. Transactions are "irreversible, final and there are no refunds" and carry network fees. In practice it is crypto in and out (not verified from the terms).

Polymarket's US arm: not checked in detail. It's built for US persons, and the US is "close-only" on the international site. I assume it's not relevant to you.

## Kalshi

Israel is not on the prohibited list. Section VI of the Member Agreement says: "You are prohibited from trading Event Contracts on the Platform if You are domiciled in, organized in, or located in" a listed country. The list (about 55 places, including the UK, France, Canada, Australia, UAE, Lebanon, Iraq, Iran) does not include Israel. One caveat: Kalshi publishes no list of supported countries, so the real proof is whether signup accepts an Israeli ID.

From Kalshi's help page on international access (dated 20 Mar 2026):

- "Yes, you can trade on Kalshi from many countries."
- "During signup, you will be asked to verify your identity and confirm your country of residence."
- Deposits, "depending on their region": debit card (Visa/Mastercard), wire transfer (minimum $1,000), cryptocurrency.
- "For withdrawals, international users can use debit card or cryptocurrency."

Automated trading: the Member Agreement doesn't mention bots or API use. Kalshi runs an official trading API. I'll confirm its terms when I open the API docs in Step 2.

## Israeli tax and gambling law (question for a professional)

This is the part that worries me. A Maariv article (23 Feb 2026) quoting a tax expert says:

- There is no official Tax Authority position on Polymarket.
- If treated as gambling, winnings are taxed at 35% or more on the gross, and "losses from gambling cannot be offset. The result may be a tax liability even though the user lost money."
- The crypto used to bet may trigger a separate capital gains event.
- If the activity is systematic, it may be classed as a business: up to about 50%, but losses and expenses would be deductible.
- The usual exemption for small wins applies to legal Israeli frameworks (Lotto, Toto) and may not apply here.

Separately, Israeli law generally bans gambling outside the state-licensed bodies (from my general knowledge, not verified today). Whether a prediction market counts is unsettled.

Why it matters for the scale check: suppose you buy 100 contracts at 90 cents and 92 win. Before tax you make 92 x $0.10 - 8 x $0.90 = +$2.00. If each win is taxed at 35% with no loss offset, tax is $3.22 and you end at -$1.22. Under that treatment a small edge is a loss. Under business treatment it would survive, at a lower net.

Questions to take to an Israeli tax adviser: (1) gambling, capital gain, or business income? (2) can losses be offset? (3) is taking part legal for a resident? (4) reporting duties for the crypto leg.

## What I did not verify

- Kalshi signup with an Israeli ID (only you can test this, and it's free).
- Polymarket US terms.
- Kalshi API terms on bots.
- Any official Israel Tax Authority document.

## Sources

- Polymarket Terms of Use: https://polymarket.com/tos
- Polymarket geoblock list: https://docs.polymarket.com/api-reference/geoblock.md
- Kalshi Member Agreement: https://kalshi.com/docs/kalshi-member-agreement.pdf
- Kalshi international access: https://help.kalshi.com/en/articles/14026044-international-access-eligibility
- Third-party summary of Kalshi's list: https://www.coinperps.com/learn/kalshi-restricted-countries
- Maariv on Israeli tax treatment: https://www.maariv.co.il/economy/israel/article-1288212
