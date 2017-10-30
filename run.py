#from app import app

import argparse

parser = argparse.ArgumentParser(
    description="ThreatKB is THE knowledge base workflow management tool for Yara rules and C2 artifacts (IP, DNS, SSL Certificates)."
)

# Define accepted arguments and metadata.
parser.add_argument('--listen-on',
                    action='store',
                    type=str,
                    default="127.0.0.1",
                    dest='listen_on',
                    help='Specify the IP address to listen on.')
parser.add_argument('--listen-port',
                    action='store',
                    type=int,
                    default=5000,
                    dest='listen_port',
                    help='Specify the port to listen on.')

args = parser.parse_args()
#app.run(debug=True)
import app

app.run(debug=True, host=args.listen_on, port=args.listen_port)
