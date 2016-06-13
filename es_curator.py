#!/usr/bin/env python
"""
ES Curator.

Usage:
  es_curator -h | --help
  es_curator [--dry] [--period <days>] [--aws-region aws_reg] [--aws-key <aws_key>] [--aws-secret <aws_secret>] <url>

Options:
  <url>                     The base url to use.
  -p --period <days>        Retention period in days [default: 7]
  -h --help                 Show this help.
  --dry                     Dry run, do not change anything.
  --aws-key <aws_key>       AWS access key ID
  --aws-secret <aws_secret> AWS secret access key
  --aws-region <aws_reg>    AWS region: [default: eu-west-1]

Examples:

  es_curator https://user:password@localholst:9200

"""
import datetime
import requests
import arrow
from requests_aws4auth import AWS4Auth

TODAY = arrow.utcnow().floor('day')


def main():
    """
    Entry point for the command line application.
    We use docopt to parse command line arguments.

    """
    from docopt import docopt

    arguments = docopt(__doc__, version='ES Curator')

    url = arguments.get('<url>', None)
    if not url:
        print 'Invalid ES URL'
        return

    period = arguments.get('--period')
    if not period:
        print 'Invalid retention period'
        return

    aws_key = arguments.get('--aws-key')
    if not aws_key and 'AWS_ACCESS_KEY_ID' in os.environ:
        aws_key = os.environ['AWS_ACCESS_KEY_ID']

    aws_secret = arguments.get('--aws-secret')
    if not aws_secret and 'AWS_SECRET_ACCESS_KEY' in os.environ:
        aws_secret = os.environ['AWS_SECRET_ACCESS_KEY']

    aws_reg = arguments.get('--aws-region')
    if not aws_reg and 'AWS_REGION' in os.environ:
        aws_reg = os.environ['AWS_REGION']

    retention = datetime.timedelta(days=int(period))

    auth=None
    if aws_key and aws_secret:
        print 'Creating AWS authorization'
        auth = AWS4Auth(aws_key, aws_secret, aws_reg, 'es')

    print 'Using url: %s' % url
    r = requests.get(url + '/_aliases', auth=auth)
    if r.status_code != requests.codes.ok:
        print "Error %s\n " % r.text
        exit(1)

    indices = r.json().keys()

    indices = filter(lambda index: index.startswith('events-'), indices)

    print 'Total %s indices' % len(indices)

    index_time_map = dict([(name, arrow.get(name[-10:])) for name in indices])

    indices_to_delete = dict([(name, arrow.get(name[-10:]))
                              for name, time in index_time_map.items()
                              if TODAY - time > retention])

    indices_to_delete = sorted(indices_to_delete.keys())

    print 'Indices to delete:'
    for name in indices_to_delete:
        print '  '+name

    if arguments.get('--dry'):
        print 'DRY mode, no changes made.'
        return

    for name in indices_to_delete:
        print 'Deleting index: %s ... ' % name,
        r = requests.delete(url + '/%s' % name, auth=auth)
        if r.status_code != requests.codes.ok:
            print "Error %s\n " % r.text
            exit(1)

    print 'Deleted %s indices' % len(indices_to_delete)

if __name__ == '__main__':
    main()
