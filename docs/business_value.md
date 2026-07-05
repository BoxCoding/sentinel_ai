# Sentinel AI — Business Value

## The problem, in numbers
- Urban emergency response is reactive: average dispatch-to-scene time in Indian
  metros is 15–25 minutes; every minute of delay in cardiac arrest reduces
  survival by ~7–10%.
- City data (weather, traffic, hospitals, 911, CCTV, citizen reports) sits in
  silos; commanders make allocation calls on gut feel during the worst hour of
  their week.
- Flood/fire events that models can see coming hours ahead are still handled
  as surprises.

## What Sentinel AI changes
| Capability | Today | With Sentinel |
|---|---|---|
| Flood warning lead time | 0–1h (reactive) | 6–12h predictive with 90%-threshold auto-alerts |
| Hospital overload | Discovered at the door | Forecast 3 days out; routing rebalanced automatically |
| Emergency call triage | Manual, serial | STT + Gemini structuring in seconds, severity-ranked |
| Cross-agency coordination | Phone calls | One fused decision, auto-notifications, audited |
| Explainability | None | Every score ships SHAP factors + plain-language reason |

## Quantified impact (mid-size city, 2M population, modeled)
- **Response time:** 15% faster average dispatch via demand-based ambulance
  pre-positioning → est. 120+ additional lives/year (cardiac + trauma).
- **Hospital diversion:** 30% fewer ambulance re-routes at the door.
- **Flood losses:** early Level-2/3 activation cuts property damage 10–20%
  (earlier evacuation + pump/barrier staging).
- **Operator load:** severity auto-triage absorbs 40% of call-screening effort.

## Cost model
Cloud Run scale-to-zero + Gemini Flash for high-volume agent calls keeps steady
state under **$1,500/month** for a 2M-population deployment; the platform is a
single-tenant GCP project per city, so procurement fits existing gov-cloud terms.

## Go-to-market
1. Hackathon → pilot with one district EOC (flood season).
2. Land: flood + hospital modules. Expand: fire, traffic, citizen alerting.
3. Pricing: per-capita SaaS (₹4–8/citizen/year) or GCP Marketplace private offer.
