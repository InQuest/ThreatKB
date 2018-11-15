def main():
    import os
    os.environ["SQLALCHEMY_ECHO"] = "0"

    from app import *
    from app.models.c2ip import C2ip
    from sqlalchemy import or_
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Fix C2ip ASN, state, and country if any are empty. Use --force to force update against all C2ip."
    )

    parser.add_argument('--force',
                        action='store_true',
                        default=False,
                        dest='force',
                        help='Force all C2ip ASN, state, and country to be updated.')

    args = parser.parse_args()

    c2ips = db.session.query(C2ip)

    if not args.force:
        c2ips = c2ips.filter(or_(C2ip.asn == None, C2ip.country == None))

    c2ips = c2ips.all()

    fixed_ips = []
    for ip in c2ips:
        updated_c2ip = C2ip.get_c2ip_from_ip(ip.ip, {})
        fixed_ips.append(updated_c2ip)

    for i in range(len(c2ips)):
        try:
            print("IP: %s\tASN: %s->%s\tCountry: %s->%s" % (
                c2ips[i].ip, c2ips[i].asn, fixed_ips[i].asn, c2ips[i].country, fixed_ips[i].country))
        except:
            pass

    response = ""
    while response not in ("Y", "N"):
        response = raw_input("Changes to be made above. There are %s total. Proceed? (Y/N) " % (len(fixed_ips)))

    not_fully_fixed = []
    if response == "Y":
        for i in range(len(c2ips)):
            c2ips[i].asn, c2ips[i].country = fixed_ips[i].asn, fixed_ips[i].country
            if not c2ips[i].asn or not c2ips[i].country:
                not_fully_fixed.append(c2ips[i])
            db.session.add(c2ips[i])
        db.session.commit()

        if len(not_fully_fixed) > 0:
            print("We did not find or set ASN or country for the following because it couldn't be looked up")
            for ip in not_fully_fixed:
                print("IP: %s\tASN: %s\tCountry: %s" % (ip.ip, ip.asn, ip.country))
            print("We did not find or set ASN or country for the above because it couldn't be looked up")

    print("All done.")
    sys.exit(0)


if __name__ == "__main__":
    main()
