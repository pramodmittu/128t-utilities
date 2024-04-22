# Copyright (c) 2021 Pindrop Security, Inc.

import ipaddress
import logging
import os
import sys

from .base_provisioner import BaseProvisioner

logger = logging.getLogger(_name_)


def main():
    logging.basicConfig(format='[%(levelname)s]\t%(message)s')
    logger.setLevel(logging.INFO)

    if os.getuid() != 0:
        logging.error('This script must be run as root!')
        sys.exit(1)

    if len(sys.argv) == 1:
        logging.error('Must provide EIP ID or cidr/tag!')
        sys.exit(1)

    eip_id = None
    try:
        eip_cidr = sys.argv[1]
        ipaddress.ip_network(eip_cidr)
    except ValueError:
        eip_cidr = None
        if sys.argv[1].startswith('eipalloc'):
            eip_id = sys.argv[1]
        else:
            logging.error('Argument must be EIP ID or CIDR block')
            sys.exit(1)

    try:
        bp = BaseProvisioner()
        bp.associate_any_eip(eip_id=eip_id, eip_cidr=eip_cidr)
    except Exception:
        logger.exception('EIP association procedure failed')
        sys.exit(1)


if _name_ == '_main_':
    main()
