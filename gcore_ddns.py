import os
import time
import logging
import yaml
import requests
import argparse
from gcore import Gcore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG_FILE = os.environ.get("GCORE_CONFIG_PATH", "config.yaml")

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file {CONFIG_FILE} not found.")
        return None
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def get_public_ip():
    try:
        # Try multiple services for robustness
        services = [
            "https://api.ipify.org?format=json",
            "https://ifconfig.me/all.json",
            "https://ipapi.co/json/"
        ]
        for service in services:
            try:
                response = requests.get(service, timeout=10)
                response.raise_for_status()
                data = response.json()
                ip = data.get("ip") or data.get("ip_addr") or data.get("query")
                if ip:
                    return ip
            except Exception:
                continue
        return None
    except Exception as e:
        logger.error(f"Failed to fetch public IP: {e}")
        return None

def update_ddns(dry_run=False):
    config = load_config()
    if not config:
        return

    api_key = config.get("gcore_api_key")
    if not api_key:
        logger.error("gcore_api_key not found in config.")
        return

    records_to_update = config.get("records", [])
    if not records_to_update:
        logger.warning("No records configured to update.")
        return

    current_ip = get_public_ip()
    if not current_ip:
        logger.error("Could not determine public IP. Skipping update.")
        return

    logger.info(f"Current public IP: {current_ip}")
    if dry_run:
        logger.info("[DRY RUN] No actual API calls will be made to Gcore.")

    client = Gcore(api_key=api_key)

    for record in records_to_update:
        zone_name = record.get("zone")
        rrset_name = record.get("name")
        rrset_type = record.get("type", "A")
        ttl = record.get("ttl", 300)

        if not zone_name or not rrset_name:
            logger.error(f"Invalid record configuration: {record}")
            continue

        try:
            if rrset_name == "@":
                full_name = zone_name
            elif rrset_name == "*":
                full_name = f"*.{zone_name}"
            else:
                full_name = f"{rrset_name}.{zone_name}"
            
            logger.info(f"Checking {rrset_type} record for {full_name}...")

            if dry_run:
                logger.info(f"[DRY RUN] Would check and update {full_name} to {current_ip}")
                continue

            # Fetch existing RRsets for the zone
            rrsets_response = client.dns.zones.rrsets.list(zone_name=zone_name)
            
            # The RrsetListResponse has an 'rrsets' attribute containing the list
            rrsets = getattr(rrsets_response, "rrsets", [])
            
            existing_rrset = None
            for r in rrsets:
                if r.name.rstrip('.') == full_name.rstrip('.') and r.type == rrset_type:
                    existing_rrset = r
                    break
            
            if existing_rrset:
                current_values = []
                for rr in existing_rrset.resource_records:
                    # Content can be a single string or a list (for some types)
                    content = rr.content
                    if isinstance(content, list):
                        current_values.extend([str(c) for c in content])
                    else:
                        current_values.append(str(content))
                
                if current_ip in current_values and len(current_values) == 1:
                    logger.info(f"Record {full_name} is already up to date ({current_ip}).")
                    continue
                else:
                    logger.info(f"Record {full_name} needs update. Current values: {current_values}")
            else:
                logger.info(f"Record {full_name} does not exist. Creating...")

            # Update (replace) or Create
            client.dns.zones.rrsets.replace(
                rrset_type=rrset_type,
                zone_name=zone_name,
                rrset_name=full_name,
                resource_records=[{"content": current_ip}],
                ttl=ttl
            )
            logger.info(f"Successfully updated {full_name} to {current_ip}")

        except Exception as e:
            logger.error(f"Error updating record {rrset_name} in zone {zone_name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gcore DDNS Updater")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making API calls")
    args = parser.parse_args()

    config = load_config()
    if not config:
        return

    interval = config.get("interval_minutes", 5) * 60
    logger.info(f"Starting Gcore DDNS service. Interval: {interval/60} minutes.")

    while True:
        try:
            update_ddns(dry_run=args.dry_run)
        except Exception as e:
            logger.error(f"Unexpected error in update loop: {e}")
        
        if args.dry_run:
            logger.info("Dry run completed. Exiting.")
            break
            
        logger.info(f"Waiting {interval/60} minutes for next update...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
