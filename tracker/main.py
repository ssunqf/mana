import argparse

from tracker.tracker import Tracker

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i",
                        "--infohash",
                        help="A torrents infohash or a file path consisting of infohashes",
                        # type=check_infohash,
                        default="95105D919C10E64AE4FA31067A8D37CCD33FE92D,9EBADF83777C3C4C4B0C90D209C038CC6D9F0801,95105D919C10E64AE4FA31067A8D37CCD33FE92D")
    parser.add_argument("-t",
                        "--tracker",
                        help="Entered in the format :tracker",
                        type=str,
                        default="62.138.0.158")
    parser.add_argument("-p",
                        "--port",
                        help="Entered in the format :port",
                        type=int,
                        default=6969)
    parser.add_argument("-j",
                        "--json",
                        help="Output in json format",
                        dest='json',
                        action='store_true')
    parser.add_argument("-to",
                        "--timeout",
                        help="Enter the timeout in seconds",
                        type=int,
                        default=150)
    parser.set_defaults(json=False)

    args, unknown = parser.parse_known_args()
    scraper = Tracker(args.tracker, args.port, args.json, args.timeout)
    scraper.scrape(args.infohash)
