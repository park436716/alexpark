"""Generate 100 chargeback Q&A contexts across networks and question types.

Each context maps a realistic merchant/issuer/cardholder question to:
  - the applicable network reason code(s)
  - suggested evidence
  - a short expected answer summary

Output: data/contexts.json (list of 100 items).
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
RULES = json.loads((ROOT / "data" / "rules.json").read_text())

# Question templates: (category_key, question_template, canonical_codes_by_network)
TEMPLATES = [
    ("fraud_cnp",
     "Cardholder claims an online purchase of {amount} at {merchant} was not made by them. What are our options on {network}?",
     {"visa": "10.4", "mastercard": "4837", "amex": "F29"}),
    ("fraud_cp",
     "In-store purchase of {amount} at {merchant} — cardholder says card was in their wallet. How does {network} handle this?",
     {"visa": "10.3", "mastercard": "4837", "amex": "F24"}),
    ("emv_counterfeit",
     "Counterfeit card used at a magstripe-only terminal for {amount}. Which {network} code applies and who bears loss?",
     {"visa": "10.1", "mastercard": "4870", "amex": "F30"}),
    ("no_auth",
     "Merchant force-posted {amount} without authorization approval. How does {network} classify this?",
     {"visa": "11.3", "mastercard": "4808", "amex": "A02"}),
    ("declined_auth",
     "Auth was declined but merchant settled {amount} anyway. Reason code under {network}?",
     {"visa": "11.2", "mastercard": "4808", "amex": "A02"}),
    ("expired_auth",
     "Auth was obtained 45 days before capture for {amount}. What is the {network} position?",
     {"visa": "11.3", "mastercard": "4808", "amex": "A08"}),
    ("amount_exceeds_auth",
     "Auth was for $50 but merchant captured {amount}. {network} handling?",
     {"visa": "12.5", "mastercard": "4834", "amex": "A01"}),
    ("late_presentment",
     "Transaction settled 45 days after auth for {amount}. Chargeback risk on {network}?",
     {"visa": "12.1", "mastercard": "4842", "amex": "P07"}),
    ("duplicate",
     "Cardholder was charged twice for the same {amount} order at {merchant}. Which {network} code covers this?",
     {"visa": "12.6.1", "mastercard": "4834", "amex": "P08"}),
    ("paid_other_means",
     "Cardholder paid cash on delivery but card was also charged {amount}. {network} reason code?",
     {"visa": "12.6.2", "mastercard": "4834", "amex": "C14"}),
    ("incorrect_amount",
     "Merchant billed {amount} but signed slip shows a different total. {network} handling?",
     {"visa": "12.5", "mastercard": "4834", "amex": "P05"}),
    ("not_received",
     "Cardholder never received an ordered item worth {amount} from {merchant}. {network} reason code and window?",
     {"visa": "13.1", "mastercard": "4855", "amex": "C08"}),
    ("services_not_rendered",
     "Cardholder paid {amount} for a service that was never performed. {network} approach?",
     {"visa": "13.1", "mastercard": "4859", "amex": "C08"}),
    ("cancelled_recurring",
     "Cardholder cancelled a subscription but merchant continued to bill {amount}. {network} code?",
     {"visa": "13.2", "mastercard": "4853", "amex": "C28"}),
    ("not_as_described",
     "Item received from {merchant} is materially different from listing (paid {amount}). {network} code?",
     {"visa": "13.3", "mastercard": "4853", "amex": "C31"}),
    ("defective",
     "Product for {amount} arrived defective and merchant refuses return. {network} handling?",
     {"visa": "13.3", "mastercard": "4853", "amex": "C32"}),
    ("credit_not_processed",
     "Merchant issued a return credit for {amount} but it never posted after 30 days. {network} code?",
     {"visa": "13.6", "mastercard": "4860", "amex": "C02"}),
    ("cancelled_goods",
     "Cardholder cancelled order for {amount} before shipment but was charged. {network} code?",
     {"visa": "13.7", "mastercard": "4853", "amex": "C05"}),
    ("goods_returned",
     "Cardholder returned goods worth {amount}; merchant received but did not refund. {network} approach?",
     {"visa": "13.6", "mastercard": "4860", "amex": "C04"}),
    ("misrepresentation",
     "Merchant advertised a warranty that does not exist; charge {amount}. {network} code?",
     {"visa": "13.5", "mastercard": "4853", "amex": "C31"}),
    ("does_not_recognize",
     "Cardholder does not recognize a {amount} charge but has not confirmed fraud. {network} first step?",
     {"visa": "10.4", "mastercard": "4863", "amex": "F24"}),
    ("questionable_merchant",
     "Multiple cardholders report the same unauthorized {amount} pattern from one merchant. {network} response?",
     {"visa": "10.4", "mastercard": "4849", "amex": "F24"}),
    ("currency_error",
     "Merchant settled in wrong currency causing a {amount} discrepancy. {network} code?",
     {"visa": "12.5", "mastercard": "4846", "amex": "P05"}),
    ("chip_pin_shift",
     "PIN-preferring chip card used without PIN for {amount}. {network} liability?",
     {"visa": "10.1", "mastercard": "4871", "amex": "F30"}),
    ("no_show_hotel",
     "Hotel no-show billed {amount} but cardholder claims they cancelled. {network} handling?",
     {"visa": "13.7", "mastercard": "4853", "amex": "C05"}),
]

MERCHANTS = ["Acme Electronics", "SkyBooks", "GreenGrocer Online", "TravelWorld", "StreamPlus", "FitPro Gym"]
AMOUNTS = ["$45.00", "$120.00", "$299.99", "$1,250.00", "$78.50", "$540.00"]

NETWORKS = ["visa", "mastercard", "amex"]


def build_answer(net_key: str, code: str) -> dict:
    net = RULES["networks"][net_key]
    rc = net["reason_codes"][code]
    evidence = RULES["evidence_matrix"].get(rc["category"], [])
    return {
        "network": net["name"],
        "framework": net["framework"],
        "reason_code": code,
        "reason_title": rc["title"],
        "category": rc["category"],
        "time_limit_days": rc.get("time_limit_days"),
        "requires_pre_arbitration": rc.get("requires_pre_arbitration", False),
        "evidence_checklist": evidence,
        "source_ref": net["source"],
    }


def main():
    contexts = []
    cid = 1
    # 25 templates × 3 networks = 75
    for t_idx, (ckey, template, code_map) in enumerate(TEMPLATES):
        for n_idx, net in enumerate(NETWORKS):
            code = code_map[net]
            merchant = MERCHANTS[(t_idx + n_idx) % len(MERCHANTS)]
            amount = AMOUNTS[(t_idx * 2 + n_idx) % len(AMOUNTS)]
            question = template.format(
                amount=amount,
                merchant=merchant,
                network=RULES["networks"][net]["name"],
            )
            contexts.append({
                "id": f"ctx-{cid:03d}",
                "category": ckey,
                "network": net,
                "question": question,
                "answer": build_answer(net, code),
            })
            cid += 1
    # 25 comparison prompts to reach 100
    for t_idx, (ckey, _template, code_map) in enumerate(TEMPLATES):
        q = (
            f"For a '{ckey.replace('_', ' ')}' scenario, compare Visa, Mastercard, and Amex: "
            "reason code, filing window, and evidence required."
        )
        contexts.append({
            "id": f"ctx-{cid:03d}",
            "category": ckey,
            "network": "comparison",
            "question": q,
            "answer": {
                "networks": [build_answer(net, code_map[net]) for net in NETWORKS],
                "note": RULES["cross_network_notes"]["chargeback_timeframe_default"],
            },
        })
        cid += 1

    assert len(contexts) == 100, f"Expected 100, got {len(contexts)}"

    out = ROOT / "data" / "contexts.json"
    out.write_text(json.dumps(contexts, indent=2, ensure_ascii=False))
    print(f"Wrote {len(contexts)} contexts to {out}")


if __name__ == "__main__":
    main()
