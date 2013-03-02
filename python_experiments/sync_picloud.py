import optparse
import cloud

parser = optparse.OptionParser()

parser.add_option("--pull", action="store_true", dest="pull")
parser.add_option("--push", action="store_true", dest="push")
(options, args) = parser.parse_args()

#cloud.volume.create('stockdata', '/data')

if options.push:
    cloud.volume.sync('/Users/peter/Documents/research/preddb/crosscat-samples/', 'crosscat-samples:')
    cloud.volume.sync('/Users/peter/Documents/research/preddb/data/', 'crosscat-data:')

if options.pull:
    cloud.volume.sync('crosscat-samples:', '/Users/peter/Documents/research/preddb/crosscat-samples/')
    cloud.volume.sync( 'crosscat-data:', '/Users/peter/Documents/research/preddb/data/')

