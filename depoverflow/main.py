from collections import OrderedDict
import logging
import pathlib
from pkg_resources import iter_entry_points
import re
import sys
import toml

from .base import InvalidReference


logger = logging.getLogger(__name__)


re_url = re.compile(r'https?://[a-zA-Z0-9$=?_@.&+!*(),%/:-]+')


def load_item_classes():
    classes = {}
    for entry_point in iter_entry_points('depoverflow.items'):
        logger.info("Loading item type %s", entry_point.name)
        class_ = entry_point.load()
        assert entry_point.name == class_.TYPE
        classes[entry_point.name] = class_
    return classes


def check(items):
    """Check whether referenced items have changed.
    """
    # TODO

    changed = False

    return changed


def extract(files):
    """Find references in source code, update `depoverflow.toml`.
    """
    # Load known item types from entrypoints
    item_classes = load_item_classes()

    # Load items from status file
    try:
        with open('depoverflow.status') as fp:
            status = toml.load(fp)
    except FileNotFoundError:
        status = {'items': []}
    stored_items = set()
    for obj in status['items']:
        type_ = obj.pop('type')
        class_ = item_classes[type_]
        stored_items.add(class_.from_json(obj))
    logger.info("Loaded %d items from status file", len(stored_items))

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

    # Save status file
    logger.info("Saving %d items to status file", len(stored_items))
    stored_items_json = [
        OrderedDict(sorted(dict(item.to_json(), type=item.TYPE).items()))
        for item in sorted(
            stored_items,
            key=lambda i: (i.TYPE, i.url()),
        )
    ]
    with open('depoverflow.status', 'w') as fp:
        toml.dump({'items': stored_items_json}, fp)

    return stored_items, changed


def main():
    logging.basicConfig(level=logging.INFO)

    # Load config
    try:
        with open('depoverflow.toml') as fp:
            config = toml.load(fp)
    except FileNotFoundError:
        logger.critical("No config file")
        sys.exit(1)

    # Update status from source files
    source_files = set()
    for pattern in config['sources']:
        source_files.update(pathlib.Path('.').glob(pattern))
    items, source_changed = extract(source_files)

    # Check items online
    items_changed = check(items)

    # Warn of changes
    if source_changed or items_changed:
        sys.exit(3)
    else:
        sys.exit(0)
