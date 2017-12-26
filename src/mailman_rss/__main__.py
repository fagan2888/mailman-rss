# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import argparse
import json
import logging
import sys
from mailman_rss import MailmanArchive, RSSWriter, HeaderScraper


logger = logging.getLogger(__file__)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="mailman-rss",
        description="Fetch Mailman archive and export to RSS")
    parser.add_argument("--command", metavar="COMMAND",
                        help="Command to execute, rss or twitter")
    parser.add_argument("--config", default=None, type=str,
                        help="mailman-rss config json file, default None")
    parser.add_argument("--archive-url", metavar="URL",
                        help="Archive URL to fetch")
    parser.add_argument("--max-items", type=int,
                        help="number of messages to convert to rss")
    parser.add_argument("-o", "--output", type=str,
                        help="output file name, default stdout")
    parser.add_argument("-l", "--loglevel", type=str,
                        help="logging level for debugging, default warning")
    parser.add_argument("--encoding", type=str,
                        help="email message encoding, default None")
    parser.add_argument("--language", type=str,
                        help="language specification, default None")
    return parser.parse_args()


def get_config(args):
    config = dict(
        command="rss",
        archive_url=None,
        db=":memory:",
        max_items=25,
        output=None,
        encoding=None,
        language=None,
        loglevel="warning",
        consumer_key=None,
        consumer_secret=None,
        access_token_key=None,
        access_token_secret=None
    )
    if args.config:
        with open(args.config, "r") as f:
            config.update(json.load(f))
    for key in config:
        if hasattr(args, key) and getattr(args, key):
            config[key] = getattr(args, key)
    return config


def main():
    args = parse_args()
    config = get_config(args)
    logging.basicConfig(level=getattr(logging, args.loglevel.upper()),
                        stream=sys.stderr)
    logger.debug("config = {}".format(config))

    if config["command"] == "rss":
        archive = MailmanArchive(config["archive_url"],
                                 encoding=config["encoding"])
        writer = RSSWriter(fp=args.output if args.output else sys.stdout,
                           max_items=config["max_items"],
                           language=config["language"])
        writer.write(archive)
    elif config["command"] == "twitter":
        import twitter
        api = twitter.Api(consumer_key=config["consumer_key"],
                          consumer_secret=config["consumer_secret"],
                          access_token_key=config["access_token_key"],
                          access_token_secret=config["access_token_secret"])
        scraper = HeaderScraper(config["archive_url"], config["db"])
        scraper.fetch(max_items=config["max_items"])
        logger.info("Unread items: {}".format(scraper.count(unread=True)))
        for header in scraper.iter_unread(True):
            subject = "{} {}".format(header["subject"], header["author"])
            if len(header["subject"]) > 139:
                subject = subject[:138] + "\u2026"
            status = "{} {}".format(subject, header["url"])
            logger.info("Post: {}".format(status))
            api.PostUpdate(status)


if __name__ == '__main__':
    main()
