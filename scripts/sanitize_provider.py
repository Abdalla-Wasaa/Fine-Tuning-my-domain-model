"""Keep auditable billing/state fields; exclude provider tokens and environment data."""
import json
import sys
from datetime import datetime, timezone

FIELDS = ('id', 'actual_status', 'intended_status', 'cur_state', 'dph_base', 'dph_total',
          'storage_total_cost', 'start_date', 'duration', 'gpu_name', 'gpu_ram',
          'internet_down_cost_per_tb', 'internet_up_cost_per_tb')


def sanitize(value):
    value = value.get('instances', value)
    if not isinstance(value, dict):
        raise ValueError('Expected a single instance object')
    result = {key: value[key] for key in FIELDS if key in value}
    if isinstance(value.get('status'), dict) and 'state' in value['status']:
        result['status'] = {'state': value['status']['state']}
    result['observed_at_utc'] = datetime.now(timezone.utc).isoformat()
    return result


if __name__ == '__main__':
    print(json.dumps(sanitize(json.load(sys.stdin)), indent=2))
