# -*- coding: utf-8 -*-

"""Console script for rcc."""
import sys
import click


@click.command()
def main(args=None):
    """Console script for rcc."""
    # Login to UNMS
    # Create new backup for specified router ID
    # Download and unarchive new backup
    # Delete remote instance of new backup
    # Get current public IP address
    # Replace netflow IP with new IP address
    # Archive file again
    # Upload to UNMS
    # Apply backup to router
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
