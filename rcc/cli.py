# -*- coding: utf-8 -*-

"""Console script for rcc."""
import os
import sys
import time
import click
import logging

from rcc.settings.logging_settings import configure_logger
from rcc.api.unms.client import UNMSClient
from rcc.api.ip_address.client import PublicIPAddress
from rcc.file_manager import FileManager
from rcc.parsers.boot import BootParser
from rcc.utils import do_until, check_dns, check_unms


logger = logging.getLogger(__name__)


@click.command()
@click.option("--device-id", envvar="RCC_DEVICE_ID")
@click.option("-w", "--dns-timeout", default=300, show_default="300s (5 minutes)")
@click.option("-u", "--unms-timeout", default=60, show_default="60s (1 minute)")
@click.option(
    "-v", "--verbose", count=True, help="Increase logging by adding more v's."
)
def main(device_id, dns_timeout, unms_timeout, verbose):
    """Console script for rcc."""

    configure_logger(verbose)

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

    public_ip_address = ip_client.get_public_ip_address()

    # Check if the current public IP address matches the DNS record
    if dns_timeout >= 0:

        dns_timeout_raised = do_until(
            check_dns, dns_timeout, 10, client, ip_client, public_ip_address
        )

        if dns_timeout_raised:
            logger.critical(
                f"Timeout ({dns_timeout}s) reached while waiting for DNS to match current IP address"
            )
            return 0

    # Check if UNMS is running yet (wait to see if it comes up)
    unms_timeout_raised = do_until(check_unms, unms_timeout, 15, client, device_id)

    if unms_timeout_raised:
        logger.critical(
            f"Timeout ({unms_timeout}s) reached while waiting for UNMS to come up"
        )
        return 0

    # Create new backup for specified router ID
    backup_id = client.create_backup(device_id)
    logger.info(f"Created new backup {backup_id}")

    # Download and unarchive new backup, delete remote backup
    filepath = os.environ["RCC_UNMS_BACKUP_FILEPATH"]
    target_dir = os.environ["RCC_UNMS_BACKUP_DIR"]
    client.get_backup(device_id, backup_id, filepath)
    logger.info(f"Downloaded backup to {filepath}")
    client.delete_backup(device_id, backup_id)
    logger.info(f"Deleted remote backup {backup_id}")
    file_manager = FileManager(filepath, target_dir)
    file_manager.untar()

    logger.info(f"Current public IP address is {public_ip_address}")

    # Replace netflow IP with new IP address
    config_dir = os.environ["RCC_UNMS_CONFIG_DIR"]
    config_rel_filepath = os.path.join(
        config_dir, os.environ["RCC_UNMS_CONFIG_REL_FILE"]
    )
    parser = BootParser(filepath=os.path.join(target_dir, config_rel_filepath))
    current_ip_address = parser.find_netflow_server()
    logger.info(f"Router is configured with Netflow IP address {current_ip_address}")
    if current_ip_address == public_ip_address:
        logger.info(f"IP addresses match, nothing to do")
        return 0
    parser.set_netflow_server(public_ip_address)
    parser.dump()

    # Archive file again
    file_manager.tar(filepath, config_dir)

    # Upload to UNMS
    backup_id = client.upload_backup(device_id, filepath)
    logger.info(f"Uploaded changed backup as {backup_id}")

    # Apply backup to router
    resp = client.apply_backup(device_id, backup_id)
    if resp.get("result", False):
        logger.info(f"Configuration successfully applied")
    else:
        logger.info(f"Something went wrong with configuration application")

    # Reboot device
    resp = client.reboot_device(device_id)
    if resp.get("result", False):
        logger.info(f"Successfully sent reboot command to router")
    else:
        logger.error(f"Something went wrong with the reboot command")

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
