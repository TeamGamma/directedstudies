#!/usr/bin/env python
from lxml import etree
from lxml.cssselect import CSSSelector
import csv
import sys

stats_tables = CSSSelector('#stats table.stats')
stats_tables = CSSSelector('#stats table.stats')

def process(filenames):
    print >> sys.stderr, 'Filenames to process:'
    print >> sys.stderr, filenames

    writer = csv.writer(sys.stdout)
    writer.writerow(('Session', 'Highest 10sec mean', 'Lowest 10sec mean', 'Highest Rate', 'Mean'))

    for i, filename in enumerate(filenames):
        page = etree.parse(open(filename, 'rU'))
        stats_table = stats_tables(page)[0]

        _, highest_mean, lowest_mean, highest_rate, mean, count = [
                element.text.split(' ')[0]
                for element in stats_table.xpath('tr[4]/td')]

        writer.writerow((i, highest_mean, lowest_mean, highest_rate, mean))


if __name__ == '__main__':
    from sys import argv
    if len(argv) < 2:
        print 'usage: %s filenames' % argv[0]
        exit(1)
    process(argv[1:])
