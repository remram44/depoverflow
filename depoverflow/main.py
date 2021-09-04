import asyncio
from collections import OrderedDict
import logging
import pathlib
from pkg_resources import iter_entry_points
import re
import sys
import toml

from .base import InvalidReference, batching


logger = logging.getLogger(__name__)


item_classes = None


re_url = re.compile(r'https?://[a-zA-Z0-9$=?_@.&+!*(),%/:-]+')


def load_item_classes():
    classes = {}
    for entry_point in iter_entry_points('depoverflow.items'):
        logger.info("Loading item type %s", entry_point.name)
        class_ = entry_point.load()
        assert entry_point.name == class_.TYPE
        classes[entry_point.name] = class_
    return classes


async def check(items):
    """Check whether referenced items have changed.
    """
    changed = False
    futures = []

    for item in items:
        ret = item.refresh()
        if asyncio.isfuture(ret):
            futures.append((item, ret))
        elif ret is True:
            changed = True
            logger.warning("Item has changed: %s", item.url())
        elif ret is not False:
            raise AssertionError("Returned value is not True or False")

    batching.flush()

    for item, future in futures:
        ret = await future
        if ret is True:
            changed = True
            logger.warning("Item has changed: %s", item.url())
        elif ret is not False:
            raise AssertionError("Returned value is not True or False")

    return changed


def extract(stored_items, files):
    """Find references in source code, update `depoverflow.toml`.
    """
    # Find URLs
    urls = set()
    # Loop on files
    for filename in files:
        with open(filename) as file:
            # Loop on lines of the file
            for line in file:
                # Find URLs
                for m in re_url.finditer(line):
                    logger.info("Found URL %s", m.group(0))
                    urls.add(m.group(0))
    logger.info("Found %d URLs in source code", len(urls))

    # Identify items from URLs
    source_items = set()
    for url in urls:
        for cls in item_classes.values():
            try:
                item = cls.create(url)
            except InvalidReference:
                pass
            else:
                source_items.add(item)
    logger.info("Identified %d items in source code", len(source_items))

    changed = False

    # Remove items from status that are no longer in source
    for item in list(stored_items):
        if item not in source_items:
            logger.info("Removed from source: %s", item.url())
            stored_items.remove(item)
            changed = True

    # Add items to status that have been found in source
    for item in source_items:
        if item not in stored_items:
            logger.info("Added from source: %s", item.url())
            stored_items.add(item)
            changed = True

    return stored_items, changed


def main():
    global item_classes

    logging.basicConfig(level=logging.INFO)

    # Load known item types from entrypoints
    item_classes = load_item_classes()

    # Load config
    try:
        with open('depoverflow.toml') as fp:
            config = toml.load(fp)
    except FileNotFoundError:
        logger.critical("No config file")
        sys.exit(1)

    # Load items from status file
    try:
        with open('depoverflow.status') as fp:
            status = toml.load(fp)
    except FileNotFoundError:
        status = {'items': []}
    items = set()
    for obj in status['items']:
        type_ = obj.pop('type')
        class_ = item_classes[type_]
        items.add(class_.from_json(obj))
    logger.info("Loaded %d items from status file", len(items))

    # Update status from source files
    source_files = set()
    for pattern in config['sources']:
        matches = pathlib.Path('.').glob(pattern)
        did_match = False
        for match in matches:
            did_match = True
            if match.is_dir():
                for path in match.glob('**'):
                    if path.is_file():
                        source_files.add(path)
            elif match.is_file():
                source_files.add(match)
        if not did_match:
            logger.warning("Source doesn't match anything: %s", pattern)
    logger.info("Reading %d files", len(source_files))
    items, source_changed = extract(items, source_files)

    # Check items online
    loop = asyncio.get_event_loop()
    items_changed = loop.run_until_complete(check(items))

    # Save status file
    logger.info("Saving %d items to status file", len(items))
    items_json = [
        OrderedDict(sorted(dict(item.to_json(), type=item.TYPE).items()))
        for item in sorted(
            items,
            key=lambda i: (i.TYPE, i.url()),
        )
    ]
    with open('depoverflow.status', 'w') as fp:
        toml.dump({'items': items_json}, fp)

    # Warn of changes
    if source_changed or items_changed:
        sys.exit(3)
    else:
        sys.exit(0)
