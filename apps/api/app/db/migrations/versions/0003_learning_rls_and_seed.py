"""learning rls and seed modules

Revision ID: 0003_learning_rls_and_seed
Revises: 0002_auth_and_rls
Create Date: 2026-10-08 21:40:00.000000

"""
import json
import uuid
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_learning_rls_and_seed"
down_revision: Union[str, None] = "0002_auth_and_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED_MODULES = [
    {
        "id": "11111111-1111-4111-8111-111111111101",
        "slug": "compounding-and-horizon",
        "title": "The Power of Compound Growth & Time Horizon",
        "category": "Basics",
        "difficulty": "beginner",
        "content": json.dumps({
            "summary": "Understand how exponential growth transforms small, consistent capital additions over long time horizons.",
            "concept": "Compounding occurs when the earnings generated on an initial principal are reinvested to generate their own returns. Rather than linear addition (Simple Interest: $A = P(1 + rt)$), compound interest behaves exponentially ($A = P(1 + r)^t$). Over multi-decade investment horizons, reinvested gains eclipse original principal by multiples.",
            "example": "Consider two investors: Alice invests $500/month starting at age 25 until 35 (10 years, $60,000 total principal) at a 7% annual return and stops adding capital. Bob waits until age 35 and invests $500/month continuously until age 65 (30 years, $180,000 total principal) at the same 7% return. At age 65, Alice's balance is ~$560,000 while Bob's is ~$566,000. Despite investing 3x less capital, Alice achieves parity solely through 10 extra years of compound duration.",
            "eli5": "Imagine a snowball rolling down a snowy mountain. At first, it's tiny and picks up very little snow. But the longer the hill, the bigger the snowball gets, and each roll picks up massive layers. The length of the hill (time) matters far more than how hard you push it initially.",
            "quant": "The discrete compound growth equation with monthly compounding and contributions is: B_n = B_0 * (1 + r/12)^n + PMT * [((1 + r/12)^n - 1) / (r/12)]. When n is large, the exponential term dominates polynomial growth by orders of magnitude.",
            "visual_type": "compounding_calculator",
            "key_takeaways": [
                "Time horizon is the single most asymmetric advantage in investing.",
                "Compounding returns are back-loaded: the majority of dollar gains occur in the final quartile of the investment horizon.",
                "Frequent interruptions or premature withdrawals reset the exponential compounding curve."
            ],
            "quiz": [
                {
                    "id": "q1",
                    "question": "What is the primary mathematical driver of exponential compound growth?",
                    "options": [
                        "Paying higher transaction commissions",
                        "Earning returns on previously reinvested returns over extended time",
                        "Timing short-term daily intraday price fluctuations",
                        "Keeping all capital in non-interest-bearing checking cash"
                    ],
                    "correct_index": 1,
                    "explanation": "Compounding works because earnings generate their own earnings when reinvested, creating an exponential curve rather than a linear slope."
                },
                {
                    "id": "q2",
                    "question": "According to the Rule of 72, approximately how many years does it take an investment to double at an 8% annual return?",
                    "options": [
                        "12 years",
                        "9 years",
                        "6 years",
                        "15 years"
                    ],
                    "correct_index": 1,
                    "explanation": "The Rule of 72 estimates doubling time: 72 / annual return = 72 / 8 = 9 years."
                },
                {
                    "id": "q3",
                    "question": "Why is starting to invest early so critical, even with modest monthly contributions?",
                    "options": [
                        "Brokers give lower trading fees to younger clients",
                        "Capital gains taxes are completely waived for early investors",
                        "The back-loaded nature of compounding rewards time duration exponentially over capital size",
                        "Older investors are barred by regulation from buying index funds"
                    ],
                    "correct_index": 2,
                    "explanation": "Because compounding is exponential, the number of compounding periods (t) has a disproportionately greater impact than initial principal."
                }
            ]
        })
    },
    {
        "id": "22222222-2222-4222-8222-222222222202",
        "slug": "risk-return-and-volatility",
        "title": "Risk vs. Return & Geometric Volatility Drag",
        "category": "Risk",
        "difficulty": "beginner",
        "content": json.dumps({
            "summary": "Learn why volatility is not just emotional discomfort, but a mathematical drag on compound annualized returns.",
            "concept": "In finance, risk and expected return are intrinsically linked. However, average arithmetic return differs markedly from realized geometric return (CAGR). High volatility induces 'volatility drag': the loss of compounding efficiency caused by large drawdowns.",
            "example": "If a portfolio drops 50% in Year 1, it requires a 100% gain in Year 2 just to break even. The arithmetic average of (-50% + 100%) / 2 is +25%, yet the investor's actual net gain is exactly 0.00%. The higher the variance, the wider the gap between arithmetic and compound returns.",
            "eli5": "If you have $100 and lose 50%, you now have $50. If you then make 50% back, you only have $75! You didn't break even because the percentage gain applied to a smaller base. Volatility makes you work twice as hard to recover.",
            "quant": "The relationship is approximated by: CAGR ≈ Arithmetic Mean - (Variance / 2). Hence, an asset with 10% average return and 20% annual standard deviation achieves a realized compound return of approximately 10% - (0.04 / 2) = 8.0%.",
            "visual_type": "volatility_drag_simulator",
            "key_takeaways": [
                "Drawdowns are asymmetric: recovering from large losses requires exponentially larger gains.",
                "Volatility drag directly degrades terminal wealth over long horizons.",
                "Risk tolerance must balance psychological comfort with mathematical capital preservation."
            ],
            "quiz": [
                {
                    "id": "q1",
                    "question": "If an investment loses 20% of its value, what percentage gain is required to restore the initial balance?",
                    "options": [
                        "20%",
                        "25%",
                        "30%",
                        "15%"
                    ],
                    "correct_index": 1,
                    "explanation": "Starting at 100, a 20% loss brings it to 80. To return to 100, 20 / 80 = 25% gain is required."
                },
                {
                    "id": "q2",
                    "question": "What is 'volatility drag' in portfolio management?",
                    "options": [
                        "The brokerage fee charged on high beta transactions",
                        "The reduction in compound geometric return (CAGR) caused by return variance",
                        "The legal penalty for holding volatile derivatives overnight",
                        "The time lag in receiving dividends from foreign assets"
                    ],
                    "correct_index": 1,
                    "explanation": "Volatility drag describes how dispersion in returns lowers geometric compound growth relative to arithmetic average returns."
                },
                {
                    "id": "q3",
                    "question": "Which metric evaluates excess return per unit of total volatility risk?",
                    "options": [
                        "Sharpe Ratio",
                        "Price-to-Earnings Ratio",
                        "Debt-to-Equity Ratio",
                        "Gross Margin"
                    ],
                    "correct_index": 0,
                    "explanation": "The Sharpe ratio measures excess return over the risk-free rate divided by the portfolio's standard deviation: (R_p - R_f) / σ_p."
                }
            ]
        })
    },
    {
        "id": "33333333-3333-4333-8333-333333333303",
        "slug": "asset-allocation-and-mpt",
        "title": "Modern Portfolio Theory & Uncorrelated Assets",
        "category": "Portfolio",
        "difficulty": "intermediate",
        "content": json.dumps({
            "summary": "Discover why Harry Markowitz called diversification 'the only free lunch in finance'.",
            "concept": "Modern Portfolio Theory (MPT) demonstrates that combining assets with low or negative correlation creates a portfolio whose total variance is lower than the weighted average of its individual components, without necessarily sacrificing expected return.",
            "example": "Asset A has 10% expected return and 15% volatility. Asset B has 8% expected return and 12% volatility. If correlation between A and B is ρ = 0.10, an equal-weight portfolio (50% A, 50% B) has an expected return of 9.0%, but its volatility drops to ~10.2%, substantially below both individual holdings.",
            "eli5": "If you sell umbrellas, you make money on rainy days. If you sell sunglasses, you make money on sunny days. If you sell both, you make a steady living no matter the weather, smoothing out your income throughout the year.",
            "quant": "Portfolio variance for two assets: σ_p^2 = w_1^2 σ_1^2 + w_2^2 σ_2^2 + 2 w_1 w_2 Cov(1,2), where Cov(1,2) = ρ_12 σ_1 σ_2. When ρ < 1, σ_p is strictly less than the weighted average standard deviation.",
            "visual_type": "asset_allocator",
            "key_takeaways": [
                "Correlation coefficient (-1.0 to +1.0) dictates the magnitude of diversification benefit.",
                "The efficient frontier represents portfolios maximizing expected return for each unit of risk.",
                "Rebalancing systematically enforces buying low and selling high across asset classes."
            ],
            "quiz": [
                {
                    "id": "q1",
                    "question": "Why is diversification termed 'the only free lunch in finance'?",
                    "options": [
                        "It eliminates all systematic market risk completely",
                        "It allows risk reduction without a proportional sacrifice in expected return when assets are imperfectly correlated",
                        "It guarantees zero capital losses during any bear market",
                        "It provides tax deductions for holding multiple brokerage accounts"
                    ],
                    "correct_index": 1,
                    "explanation": "Combining imperfectly correlated assets reduces portfolio variance while preserving the weighted expected return, delivering improved risk-adjusted performance."
                },
                {
                    "id": "q2",
                    "question": "What happens to portfolio volatility as the correlation coefficient (ρ) between two assets approaches -1.0?",
                    "options": [
                        "Portfolio risk approaches zero through perfect counter-cyclical hedging",
                        "Portfolio risk doubles due to conflicting signals",
                        "Portfolio return drops to zero permanently",
                        "No mathematical effect occurs"
                    ],
                    "correct_index": 0,
                    "explanation": "A correlation of -1.0 means assets move in perfect opposition, allowing variance to be completely hedged at appropriate weights."
                },
                {
                    "id": "q3",
                    "question": "What is the primary benefit of systematic quarterly or annual portfolio rebalancing?",
                    "options": [
                        "Generating maximum trading commission fees",
                        "Disciplined adherence to target risk allocations by trimming outperformers and buying underperformers",
                        "Guaranteeing that all holdings become equal in dollar value",
                        "Avoiding federal income tax filing requirements"
                    ],
                    "correct_index": 1,
                    "explanation": "Rebalancing restores the target risk profile and enforces the discipline of buying depressed assets and locking in gains from outperforming assets."
                }
            ]
        })
    },
    {
        "id": "44444444-4444-4444-8444-444444444404",
        "slug": "equity-fundamentals",
        "title": "Equity Ownership & Fundamental Drivers of Stock Value",
        "category": "Stocks",
        "difficulty": "beginner",
        "content": json.dumps({
            "summary": "Master what a stock represents: fractional equity ownership in an operating business generating cash flows.",
            "concept": "A share of common stock is not a lottery ticket; it is a fractional claim on the assets, cash flows, and future profits of a corporate enterprise. In the short run, stock prices are driven by market sentiment and liquidity; in the long run, they converge to corporate earnings power and return on invested capital (ROIC).",
            "example": "If Company X generates $5.00 in earnings per share (EPS) and trades at $100, its Price-to-Earnings (P/E) multiple is 20x. If EPS grows at 15% annually to $10.05 over 5 years, even if the multiple contracts to 16x, the stock price rises to $160.80, delivering healthy shareholder wealth driven by underlying business expansion.",
            "eli5": "Owning a stock is like owning 1% of a profitable neighborhood bakery. You care how many cakes they bake, how much flour costs, and how much cash they bring home at the end of the month—not what someone shouts on the street corner today.",
            "quant": "Stock Return = Dividend Yield + EPS Growth + Multiple Expansion (Δ P/E). Over multi-decade periods, EPS growth and dividend reinvestment account for >90% of total equity returns.",
            "visual_type": "pe_ratio_breakdown",
            "key_takeaways": [
                "Stock ownership grants residual claims on corporate net cash flow.",
                "Economic moats (pricing power, network effects, cost advantages) protect sustained high returns on capital.",
                "Market prices fluctuate wider than intrinsic business value, creating opportunities for disciplined investors."
            ],
            "quiz": [
                {
                    "id": "q1",
                    "question": "What does a share of common stock legally confer to the holder?",
                    "options": [
                        "A guaranteed weekly coupon interest payment from the government",
                        "A fractional ownership claim on the corporation's assets and residual earnings",
                        "Senior debt claim ahead of all bondholders in liquidation",
                        "Immunity from corporate bankruptcy consequences"
                    ],
                    "correct_index": 1,
                    "explanation": "Common stock is equity, representing fractional ownership and the residual claim on corporate profits after debt obligations are satisfied."
                },
                {
                    "id": "q2",
                    "question": "Which three fundamental drivers dictate the long-term total return of a stock?",
                    "options": [
                        "Brokerage incentives, exchange fees, and margin loan rates",
                        "Dividend yield, earnings growth, and changes in valuation multiple",
                        "Social media trending volume, ticker letter count, and trading volume",
                        "Option implied volatility, daily high-low spread, and RSI"
                    ],
                    "correct_index": 1,
                    "explanation": "Total shareholder return equals Dividend Yield + Growth in Earnings + Expansion/Contraction of Valuation Multiples."
                },
                {
                    "id": "q3",
                    "question": "What is an 'economic moat' as described by institutional investors?",
                    "options": [
                        "A physical water barrier around corporate headquarters",
                        "A durable competitive advantage that protects corporate margins and return on capital from rivals",
                        "A government subsidy granted exclusively to distressed companies",
                        "An algorithm used to avoid regulatory disclosure requirements"
                    ],
                    "correct_index": 1,
                    "explanation": "An economic moat represents structural advantages—such as network effects, patents, high switching costs, or scale—that sustain profitability over competitors."
                }
            ]
        })
    },
    {
        "id": "55555555-5555-4555-8555-555555555505",
        "slug": "funds-etfs-and-fee-drag",
        "title": "Index Funds vs Active ETFs & Fee Drag Mechanics",
        "category": "Funds",
        "difficulty": "intermediate",
        "content": json.dumps({
            "summary": "Understand how expense ratios and active management drag compound over decades to erode investor wealth.",
            "concept": "Index funds passively track benchmark indices (like the S&P 500 or Total Stock Market) with rock-bottom expense ratios (often 0.03%–0.08%). Active funds attempt to beat benchmarks through stock picking and market timing, charging 0.75%–1.50%+. Empirical research (SPIVA) reveals that over 15-year periods, over 90% of active managers underperform their passive index after accounting for fees.",
            "example": "Assume two identical $100,000 portfolios earning 7% gross annual return over 30 years. Portfolio A has a 0.05% index expense ratio. Portfolio B has a 1.25% active management fee. Portfolio A terminates at ~$750,000. Portfolio B terminates at ~$520,000. That seemingly modest 1.20% fee differential consumed $230,000—over 30% of total wealth!",
            "eli5": "Imagine entering a marathon where one runner carries an empty backpack, and another carries a 30-pound rock (high fees). Even if the second runner is skilled, the heavy backpack slowly exhausts them over 26 miles.",
            "quant": "Net Return = Gross Return - Expense Ratio. Compounded capital: FV = PV * (1 + r_gross - fee)^t. Fee erosion percentage: 1 - ((1 + r - fee)^t / (1 + r)^t). At fee=1.5% and t=30, fee drag consumes over 35% of cumulative terminal value.",
            "visual_type": "fee_drag_calculator",
            "key_takeaways": [
                "Fees are guaranteed; outperformance is probabilistic and ephemeral.",
                "Expense ratios compound destructively over multi-decade horizons.",
                "ETFs offer tax efficiency via in-kind creation and redemption mechanisms."
            ],
            "quiz": [
                {
                    "id": "q1",
                    "question": "According to multi-decade SPIVA research reports, what percentage of active equity managers fail to beat their benchmark after fees?",
                    "options": [
                        "Under 20%",
                        "Approximately 50%",
                        "Over 85% to 90%",
                        "Exactly 100%"
                    ],
                    "correct_index": 2,
                    "explanation": "Over 15-to-20-year horizons, empirical SPIVA data consistently shows 85-92% of active mutual funds lag their corresponding benchmark index."
                },
                {
                    "id": "q2",
                    "question": "How does a 1.0% annual management fee affect long-term compounding over a 30-year horizon?",
                    "options": [
                        "It consumes roughly 1% of your final portfolio value",
                        "It consumes approximately 25% to 30% of your total potential terminal wealth",
                        "It has zero impact because fees are fully refunded by tax credits",
                        "It increases overall returns through active leverage"
                    ],
                    "correct_index": 1,
                    "explanation": "Because fees are deducted every year from both principal and previous gains, a 1% fee reduces terminal wealth by nearly 25-30% over 30 years."
                },
                {
                    "id": "q3",
                    "question": "What is the primary structural tax advantage of Exchange-Traded Funds (ETFs) over traditional mutual funds?",
                    "options": [
                        "ETFs are exempt from all federal capital gains taxes",
                        "Authorized Participants use in-kind creation and redemption baskets, minimizing taxable capital gains distributions",
                        "ETFs can only invest in tax-free municipal bonds",
                        "Mutual funds must pay corporate tax rates on investor profits"
                    ],
                    "correct_index": 1,
                    "explanation": "ETFs use institutional in-kind share exchanges with Authorized Participants, allowing funds to wash out low-basis shares without triggering taxable capital gains distributions to fund holders."
                }
            ]
        })
    },
    {
        "id": "66666666-6666-4666-8666-666666666606",
        "slug": "three-statement-analysis",
        "title": "Three-Statement Analysis: Income, Balance Sheet & Cash Flow",
        "category": "Financial Statements",
        "difficulty": "intermediate",
        "content": json.dumps({
            "summary": "Learn how the Income Statement, Balance Sheet, and Statement of Cash Flows interconnect to reveal economic reality.",
            "concept": "Financial analysis requires verifying whether accounting earnings match underlying cash generation. The Income Statement records revenues and expenses via accrual accounting. The Balance Sheet snapshots assets, liabilities, and equity at a single point in time. The Cash Flow Statement reconciles net income to actual cash through Operating, Investing, and Financing activities.",
            "example": "A company reports $100M Net Income on its Income Statement. However, its Accounts Receivable rose by $80M and Inventory rose by $40M. On the Cash Flow Statement, Operating Cash Flow (OCF) is negative (-$20M). This divergence is a major warning flag: the business is recognizing sales on paper that customers have not yet paid for.",
            "eli5": "The Income Statement is your resume (what you claimed to accomplish). The Balance Sheet is your bank account snapshot (what you own and owe today). The Cash Flow Statement is the video camera in your wallet (where the dollar bills actually went).",
            "quant": "Free Cash Flow (FCF) = Cash Flow from Operations (CFO) - Capital Expenditures (CapEx). Retained Earnings_t = Retained Earnings_{t-1} + Net Income_t - Dividends Paid_t. Assets = Liabilities + Shareholders' Equity.",
            "visual_type": "statement_interconnection_diagram",
            "key_takeaways": [
                "Net Income is an accounting construct; Free Cash Flow is raw economic oxygen.",
                "Working capital expansion consumes cash and can conceal declining customer credit quality.",
                "Check debt maturities on the balance sheet against normalized operating cash flow generation."
            ],
            "quiz": [
                {
                    "id": "q1",
                    "question": "What does a persistent divergence between growing Net Income and declining Cash Flow from Operations typically signal?",
                    "options": [
                        "Exceptional operational efficiency and premium pricing power",
                        "Aggressive revenue recognition or deteriorating working capital collections",
                        "An impending reduction in corporate tax liabilities",
                        "A mandatory stock split"
                    ],
                    "correct_index": 1,
                    "explanation": "When Net Income grows while Operating Cash Flow falls, earnings quality is suspect—often indicating uncollected receivables or unsold inventory buildup."
                },
                {
                    "id": "q2",
                    "question": "How is Free Cash Flow (FCF) standardly computed from financial filings?",
                    "options": [
                        "Gross Profit minus General & Administrative Expenses",
                        "Operating Cash Flow minus Capital Expenditures (CapEx)",
                        "Total Revenue minus Total Debt",
                        "EBITDA multiplied by Price-to-Earnings Ratio"
                    ],
                    "correct_index": 1,
                    "explanation": "Free Cash Flow represents the discretionary cash remaining after essential capital expenditures: FCF = Operating Cash Flow - CapEx."
                },
                {
                    "id": "q3",
                    "question": "Where does Net Income flow into the Balance Sheet at the close of an accounting period?",
                    "options": [
                        "Directly into Short-Term Debt",
                        "Into Shareholders' Equity via Retained Earnings (net of dividends)",
                        "Into Intangible Goodwill Assets",
                        "Into Accounts Payable"
                    ],
                    "correct_index": 1,
                    "explanation": "Net Income minus dividends declared rolls into Retained Earnings under the Shareholders' Equity section of the Balance Sheet."
                }
            ]
        })
    },
    {
        "id": "77777777-7777-4777-8777-777777777707",
        "slug": "valuation-dcf-and-multiples",
        "title": "Intrinsic Value: Discounted Cash Flows (DCF) vs Price Multiples",
        "category": "Valuation",
        "difficulty": "advanced",
        "content": json.dumps({
            "summary": "Master the twin pillars of equity valuation: intrinsic cash flow discounting and relative trading multiples.",
            "concept": "The intrinsic value of any financial asset is the present discounted value of all future cash flows it generates over its lifetime. Relative valuation uses comparable trading multiples (P/E, EV/EBITDA, P/FCF) to assess how the market currently prices peers. While multiples offer fast comparative context, DCF forces rigorous explicit modeling of growth, margins, reinvestment, and cost of capital (WACC).",
            "example": "If a company produces $100M in FCF growing at 5% in perpetuity, and its Weighted Average Cost of Capital (WACC) is 9%, the Gordon Growth intrinsic equity value is: FCF_1 / (WACC - g) = ($100M * 1.05) / (0.09 - 0.05) = $105M / 0.04 = $2.625 Billion. If market cap is $1.8 Billion, the stock trades at an attractive margin of safety.",
            "eli5": "Would you buy a golden goose? The DCF asks: how many golden eggs will it lay over the next 10 years, and how much is each future egg worth to you today? Relative valuation asks: what did your neighbor pay for their golden goose down the street?",
            "quant": "Enterprise Value = Sum_{t=1}^N [FCFF_t / (1 + WACC)^t] + [Terminal Value_N / (1 + WACC)^N]. Terminal Value = [FCFF_N * (1 + g)] / (WACC - g). Equity Value = Enterprise Value - Net Debt.",
            "visual_type": "dcf_sensitivity_table",
            "key_takeaways": [
                "Price is what you pay; value is what you get.",
                "DCF outputs are hypersensitive to terminal growth rate and discount rate assumptions.",
                "A margin of safety provides cushion against forecasting errors and unforeseen headwinds."
            ],
            "quiz": [
                {
                    "id": "q1",
                    "question": "In a Discounted Cash Flow (DCF) analysis, what happens to intrinsic value when the discount rate (WACC) is increased?",
                    "options": [
                        "Intrinsic value increases because capital is worth more",
                        "Intrinsic value decreases because future cash flows are penalized more heavily today",
                        "Intrinsic value is completely unchanged",
                        "The company's revenue doubles automatically"
                    ],
                    "correct_index": 1,
                    "explanation": "The discount rate is in the denominator. A higher discount rate (reflecting greater risk or higher cost of capital) reduces the present value of future cash flows."
                },
                {
                    "id": "q2",
                    "question": "Why is EV/EBITDA often preferred over P/E when comparing companies across different capital structures?",
                    "options": [
                        "EV/EBITDA is calculated by credit rating agencies exclusively",
                        "It neutralizes differences in leverage (debt) and non-cash depreciation/amortization accounting",
                        "EBITDA includes all future dividend payments",
                        "P/E ratios cannot be computed for profitable companies"
                    ],
                    "correct_index": 1,
                    "explanation": "Enterprise Value includes debt and equity, and EBITDA is pre-interest and taxes, enabling capital-structure-neutral operational comparisons."
                },
                {
                    "id": "q3",
                    "question": "What is Benjamin Graham's concept of 'Margin of Safety'?",
                    "options": [
                        "Purchasing an asset at a substantial discount to conservative intrinsic value to absorb analytical errors or bad luck",
                        "Maintaining 100% of your portfolio in cash collateral at all times",
                        "Purchasing protective put options on every position regardless of cost",
                        "Borrowing at maximum margin limits when markets hit all-time highs"
                    ],
                    "correct_index": 0,
                    "explanation": "Margin of safety is the gap between intrinsic value and market price that protects the investor against inevitable valuation errors or unforeseen adversities."
                }
            ]
        })
    },
    {
        "id": "88888888-8888-4888-8888-888888888808",
        "slug": "interest-rates-and-macro-cycles",
        "title": "Central Banks, Interest Rates & Macroeconomic Cycles",
        "category": "Macroeconomics",
        "difficulty": "intermediate",
        "content": json.dumps({
            "summary": "Understand how monetary policy, yield curve inversions, and credit cycles impact asset prices.",
            "concept": "Interest rates represent the cost of money and the benchmark hurdle rate for all capital investments. When central banks hike rates to curb inflation, borrowing costs rise, consumer demand softens, and the discount rate applied to corporate future cash flows increases—compressing equity valuations, especially for high-duration growth companies.",
            "example": "When the Federal Reserve raised the Fed Funds rate from 0% to >5% in 2022-2023, the yield on 10-year US Treasuries climbed from 1.5% to ~4.5%. This triggered sharp multiple contraction in tech stocks because distant future cash flows were discounted at substantially higher hurdle rates.",
            "eli5": "Interest rates are the gravity of financial markets. When gravity is low (rates at 0%), assets float effortlessly upward. When gravity increases (rates jump to 5%), heavy valuations get pulled firmly back toward earth.",
            "quant": "Bond Price Duration: Δ P / P ≈ - Modified Duration * Δ y. A bond with 10-year duration loses approximately 10% in price for every 1.0% (100 bps) increase in market yields.",
            "visual_type": "macro_cycle_diagram",
            "key_takeaways": [
                "Interest rates set the foundational discount rate for all global asset classes.",
                "An inverted yield curve (2-year yield > 10-year yield) historically signals recessionary risk within 12-24 months.",
                "Fixed-income bonds exhibit negative correlation to yields through duration risk."
            ],
            "quiz": [
                {
                    "id": "q1",
                    "question": "Why do high interest rates disproportionately penalize long-duration growth tech stocks compared to mature dividend payers?",
                    "options": [
                        "Tech companies are legally banned from borrowing from banks",
                        "The bulk of growth company cash flows lie in distant future years, making their present value highly sensitive to higher discount rates",
                        "Dividend payers are exempt from federal interest rate changes",
                        "Growth stocks have no employees"
                    ],
                    "correct_index": 1,
                    "explanation": "Long-duration assets have cash flows far into the future. When the discount rate rises, exponential discounting reduces distant cash flows much more severely than near-term cash flows."
                },
                {
                    "id": "q2",
                    "question": "What does an inverted Treasury yield curve (e.g. 2-year yield higher than 10-year yield) traditionally indicate?",
                    "options": [
                        "The economy is expanding at an unprecedented boom pace",
                        "Markets anticipate imminent economic deceleration or recession, expecting central banks to cut rates in the future",
                        "Stock markets will rise 50% over the next month",
                        "Inflation has permanently stabilized at zero"
                    ],
                    "correct_index": 1,
                    "explanation": "Yield curve inversion indicates investors expect near-term tight policy will cause economic slowdown, forcing central banks to lower longer-term interest rates."
                },
                {
                    "id": "q3",
                    "question": "If a Treasury bond has a Modified Duration of 8 years and market yields rise by 100 basis points (+1.0%), what happens to the bond price?",
                    "options": [
                        "It rises by approximately 8%",
                        "It falls by approximately 8%",
                        "It remains exactly constant",
                        "It pays an extra 8% cash bonus immediately"
                    ],
                    "correct_index": 1,
                    "explanation": "By duration approximation: ΔP/P ≈ -Duration * Δy = -8 * (+0.01) = -8% drop in bond price."
                }
            ]
        })
    }
]


def upgrade() -> None:
    # 1. RLS Policies for learning_progress & quiz_attempts (§11, §30)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE tablename = 'learning_progress' AND policyname = 'learning_progress_isolation_policy'
            ) THEN
                CREATE POLICY learning_progress_isolation_policy ON learning_progress
                FOR ALL
                USING (
                    user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                    OR current_setting('app.is_admin', true) = 'true'
                    OR current_setting('app.bypass_rls', true) = 'true'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE tablename = 'quiz_attempts' AND policyname = 'quiz_attempts_isolation_policy'
            ) THEN
                CREATE POLICY quiz_attempts_isolation_policy ON quiz_attempts
                FOR ALL
                USING (
                    user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                    OR current_setting('app.is_admin', true) = 'true'
                    OR current_setting('app.bypass_rls', true) = 'true'
                );
            END IF;
        END $$;
    """)

    # 2. Seed initial learning modules across all 8 required categories (§29)
    conn = op.get_bind()
    for mod in SEED_MODULES:
        conn.execute(
            sa.text("""
                INSERT INTO learning_modules (id, slug, title, category, difficulty, content, created_at, updated_at)
                VALUES (:id, :slug, :title, :category, :difficulty, :content, NOW(), NOW())
                ON CONFLICT (slug) DO UPDATE SET
                    title = EXCLUDED.title,
                    category = EXCLUDED.category,
                    difficulty = EXCLUDED.difficulty,
                    content = EXCLUDED.content,
                    updated_at = NOW();
            """),
            {
                "id": mod["id"],
                "slug": mod["slug"],
                "title": mod["title"],
                "category": mod["category"],
                "difficulty": mod["difficulty"],
                "content": mod["content"],
            }
        )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS learning_progress_isolation_policy ON learning_progress;")
    op.execute("DROP POLICY IF EXISTS quiz_attempts_isolation_policy ON quiz_attempts;")
    # Clean seeded modules
    slugs = tuple(m["slug"] for m in SEED_MODULES)
    if slugs:
        op.execute(sa.text(f"DELETE FROM learning_modules WHERE slug IN :slugs").bindparams(slugs=slugs))
