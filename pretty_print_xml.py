#!/usr/bin/env python3
"""
Pretty-print an XML file so elements are on separate lines,
making lxml.etree.Element.sourceline useful.
Creates a backup: <file>.bak
"""
import shutil
import sys
import logging
from lxml import etree

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def backup(path):
    bak = path + ".bak"
    shutil.copy2(path, bak)
    logging.info(f"Backup created: {bak}")
    return bak

def try_pretty(path, outpath=None):
    if outpath is None:
        outpath = path
    parser = etree.XMLParser(remove_blank_text=True, recover=True)
    try:
        tree = etree.parse(path, parser)
        tree.write(outpath, encoding="utf-8", pretty_print=True, xml_declaration=True)
        logging.info(f"Pretty printed XML saved to: {outpath}")
        return True
    except etree.XMLSyntaxError as e:
        logging.error(f"XMLSyntaxError during pretty print: {e}")
        return False

def try_wrap_and_pretty(path, outpath=None):
    """
    Fallback: wrap content in a temporary root element, pretty print.
    Note: this will add the wrapper element to the output — inspect result and remove wrapper if needed.
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    wrapped = "<__WRAPPER__>\n" + content + "\n</__WRAPPER__>"
    parser = etree.XMLParser(remove_blank_text=True, recover=True)
    try:
        root = etree.fromstring(wrapped.encode("utf-8"), parser)
        tree = etree.ElementTree(root)
        out = path if outpath is None else outpath
        tree.write(out, encoding="utf-8", pretty_print=True, xml_declaration=True)
        logging.info(f"Wrapped and pretty printed to: {out} (contains a __WRAPPER__ root tag)")
        return True
    except etree.XMLSyntaxError as e:
        logging.error(f"Fallback wrap failed: {e}")
        return False

def print_sample_lines(path, tag_localname="Unit", limit=20):
    """
    Reparse and print sourceline for elements with given localname.
    """
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(path, parser)
    root = tree.getroot()
    count = 0
    for elem in root.iter():
        # get localname (works with namespaces)
        local = etree.QName(elem).localname
        if local == tag_localname:
            print(f"Line {elem.sourceline}: <{local}> -> {elem.text!r}")
            count += 1
            if count >= limit:
                break
    if count == 0:
        logging.info(f"No elements named '{tag_localname}' found (check tag name or namespace).")

def main(path):
    backup(path)
    ok = try_pretty(path)
    if not ok:
        logging.warning("Attempting fallback wrap-and-pretty. Output will include wrapper element; inspect it.")
        ok2 = try_wrap_and_pretty(path)
        if not ok2:
            logging.error("Both pretty-print attempts failed. File may be badly malformed.")
            sys.exit(2)
    # show some sample 'Unit' elements with line numbers
    print_sample_lines(path, tag_localname="Unit", limit=50)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pretty_fix_xml.py path/to/file.xml")
        sys.exit(1)
    main(sys.argv[1])
