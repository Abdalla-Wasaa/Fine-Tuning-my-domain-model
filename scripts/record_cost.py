"""Record observed billing duration and actual contracted compute rate."""
import argparse
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import ROOT, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--billed-seconds', type=float, required=True)
parser.add_argument('--hourly-rate-usd', type=float, required=True)
parser.add_argument('--billing-reference', required=True, help='Non-secret invoice or usage report reference')
args = parser.parse_args()
if any(not math.isfinite(v) or v < 0 for v in (args.billed_seconds, args.hourly_rate_usd)):
    parser.error('Billing duration and rate must be finite and nonnegative')
write_json(ROOT / 'reports/compute_cost.json', {'billed_seconds': args.billed_seconds,
    'hourly_rate_usd': args.hourly_rate_usd, 'compute_usd': args.billed_seconds/3600*args.hourly_rate_usd,
    'billing_reference': args.billing_reference, 'excludes': ['storage', 'network', 'judge API']})
