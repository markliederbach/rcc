# -*- coding: utf-8 -*-

"""Console script for rcc."""
import os
import sys
import time
import click

from rcc.api.unms.client import UNMSClient
from rcc.api.ip_address.client import PublicIPAddress
from rcc.file_manager import FileManager
from rcc.parsers.boot import BootParser
from rcc.utils import signal_timeout


@click.command()
@click.option("--device-id", envvar="RCC_DEVICE_ID")
@click.option("-w", "--dns-timeout", default=300, show_default="300s (5 minutes)")
def main(device_id, dns_timeout):
    """Console script for rcc."""
    # Login to UNMS
    client = UNMSClient(
        base_url=os.environ["RCC_UNMS_BASE_URL"],
        username=os.environ["RCC_UNMS_USER"],
        password=os.environ["RCC_UNMS_PASSWORD"],
    )
    ip_client = PublicIPAddress(
        base_url=os.environ["RCC_IP_BASE_URL"],
        ip_address_endpoint=os.environ["RCC_IP_ENDPOINT"],
    )

    # Check if the current public IP address matches the DNS record
    public_ip_address = ip_client.get_public_ip_address()
    timeout_raised = True
    with signal_timeout(dns_timeout):
        while True:
            dns_result = ip_client.dns_lookup(client.get_domain())
            if dns_result == public_ip_address:
                timeout_raised = False
                break
            time.sleep(10)

    if timeout_raised:
        click.echo(
            f"Timeout ({dns_timeout}s) reached while waiting for DNS to match current IP address",
            err=True,
        )
        return 0

    # Create new backup for specified router ID
    backup_id = client.create_backup(device_id)
    click.echo(f"Created new backup {backup_id}")

    # Download and unarchive new backup, delete remote backup
    filepath = os.environ["RCC_UNMS_BACKUP_FILEPATH"]
    target_dir = os.environ["RCC_UNMS_BACKUP_DIR"]
    client.get_backup(device_id, backup_id, filepath)
    click.echo(f"Downloaded backup to {filepath}")
    client.delete_backup(device_id, backup_id)
    click.echo(f"Deleted remote backup {backup_id}")
    file_manager = FileManager(filepath, target_dir)
    file_manager.untar()

    click.echo(f"Current public IP address is {public_ip_address}")

    # Replace netflow IP with new IP address
    config_dir = os.environ["RCC_UNMS_CONFIG_DIR"]
    config_rel_filepath = os.path.join(
        config_dir, os.environ["RCC_UNMS_CONFIG_REL_FILE"]
    )
    parser = BootParser(filepath=os.path.join(target_dir, config_rel_filepath))
    current_ip_address = parser.find_netflow_server()
    click.echo(f"Router is configured with Netflow IP address {current_ip_address}")
    if current_ip_address == public_ip_address:
        click.echo(f"IP addresses match, nothing to do")
        return 0
    parser.set_netflow_server(public_ip_address)
    parser.dump()

    # Archive file again
    file_manager.tar(filepath, config_dir)

    # Upload to UNMS
    backup_id = client.upload_backup(device_id, filepath)
    click.echo(f"Uploaded changed backup as {backup_id}")

    # Apply backup to router
    resp = client.apply_backup(device_id, backup_id)
    if resp.get("result", False):
        click.echo(f"Configuration successfully applied")
    else:
        click.echo(f"Something went wrong with configuration application")

    # Reboot device
    resp = client.reboot_device(device_id)
    if resp.get("result", False):
        click.echo(f"Successfully sent reboot command to router")
    else:
        click.echo(f"Something went wrong with the reboot command")

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
