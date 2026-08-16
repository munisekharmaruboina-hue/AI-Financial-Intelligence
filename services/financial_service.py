class FinancialService:

    def analyze(self, market):

        score = 0

        reasons = []

        pe = market["pe_ratio"]

        eps = market["eps"]

        cap = market["market_cap"]

        if pe and pe < 30:
            score += 30
            reasons.append("Healthy PE Ratio")

        if eps and eps > 50:
            score += 30
            reasons.append("Strong EPS")

        if cap and cap > 1_000_000_000:
            score += 40
            reasons.append("Large Market Cap")

        return {

            "score":score,

            "reasons":reasons

        }