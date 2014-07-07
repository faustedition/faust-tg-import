#!/usr/bin/env python
# coding=UTF-8
#
# Generate TextGrid Objects for import

from lxml import etree
import sys

ns = {
    'tei': 'http://www.tei-c.org/ns/1.0',
    'ge': 'http://www.tei-c.org/ns/geneticEditions',
    'f': 'http://www.faustedition.net/ns',
    'svg': 'http://www.w3.org/2000/svg',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    'ore': 'http://www.openarchives.org/ore/terms/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
}

# document -> item
# document -> item.metadata

def generate_objects_for_document(path):
    document_descriptor = etree.parse(path)
    xml_base = document_descriptor.xpath('/f:archivalDocument/@xml:base', namespaces=ns)[0]

    # extract document metadata

    title = document_descriptor.xpath('/f:archivalDocument/f:metadata/f:idno', namespaces=ns)[0].text
    identifier = title
    format = 'application/tei+xml'
    notes = 'A manuscript of the Faust Edition. http://faustedition.de'
    doc_transcripts = document_descriptor.xpath('//f:docTranscript/@uri', namespaces=ns)
    
    # generate textgrid item for document

    document_item = etree.parse('xml-templates/document-item.xml')
    for doc_transcript in doc_transcripts:
        full_doc_transcript_path = xml_base + doc_transcript
        rdf_description = document_item.xpath('//rdf:Description', namespaces=ns)[0]
        rdf_description.append(etree.fromstring('<aggregates resource="' + full_doc_transcript_path + '"/>'))
    document_item.write(sys.stdout)

if len(sys.argv) != 2:
    print 'usage: generate-tg-objects.py path-to-document'

generate_objects_for_document(sys.argv[1])
