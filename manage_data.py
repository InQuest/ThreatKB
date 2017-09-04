import argparse


def main(args):
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate random data for ThreatKB",
        usage="python manage_data.py "
    )

    parser.add_argument('--artifact',
                        action='store',
                        type=str,
                        choices=["c2dns", "c2ip", "yara_rule"],
                        required=True,
                        dest='artifact',
                        help='The artifact type you want to operate on.')
    parser.add_argument('--yara-rule-directory',
                        action='store',
                        type=str,
                        default=None,
                        dest='yara_rule_directory',
                        help='Specify a yara rule directory to import yara rules from.')
    parser.add_argument('--config',
                        action='store',
                        type=str,
                        required=True,
                        dest='config',
                        help='Specify config file. SQLALCHEMY_DATABASE_URI must exist in this file.')

    args = parser.parse_args()

    main(args)
