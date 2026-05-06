#!/usr/bin/env python3
"""Add QQ bot configuration to Hermes config.yaml"""

import yaml
from pathlib import Path

config_path = Path.home() / ".hermes" / "config.yaml"

# Load existing config
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Add QQ platform configuration
if 'platforms' not in config:
    config['platforms'] = {}

config['platforms']['qq'] = {
    'enabled': True,
    'extra': {
        'app_id': '1903842713',
        'client_secret': 'pa8UeaKq9F7nHYcT',
        'markdown_support': True,
        'dm_policy': 'open',
        'group_policy': 'open',
        'stt': {
            'provider': 'zai',
            'baseUrl': 'https://open.bigmodel.cn/api/coding/paas/v4',
            'model': 'glm-asr'
        }
    }
}

# Backup original config
backup_path = config_path.with_suffix('.yaml.bak')
backup_path.write_text(config_path.read_text(encoding='utf-8'), encoding='utf-8')
print(f"✓ Backup created: {backup_path}")

# Write updated config
with open(config_path, 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

print(f"✓ QQ bot configuration added to {config_path}")
print("\nConfiguration summary:")
print(f"  - App ID: 1903842713")
print(f"  - Client Secret: pa8UeaKq9F7nHYcT")
print(f"  - DM Policy: open (allows all users)")
print(f"  - Group Policy: open (allows all groups)")
print(f"  - STT Provider: zai (GLM-ASR)")
print("\nNext steps:")
print("1. Start the gateway: hermes gateway")
print("2. The QQ bot will connect automatically")
