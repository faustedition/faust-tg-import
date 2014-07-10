#!/usr/bin/env python
# coding=UTF-8
#
# Generate TextGrid Objects for import

from lxml import etree
import sys
import os.path

ns = {
    'tei': 'http://www.tei-c.org/ns/1.0',
    'ge': 'http://www.tei-c.org/ns/geneticEditions',
    'f': 'http://www.faustedition.net/ns',
    'svg': 'http://www.w3.org/2000/svg',
    'xml': 'http://www.w3.org/XML/1998/namespace',
    'ore': 'http://www.openarchives.org/ore/terms/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'tns': 'http://textgrid.info/namespaces/metadata/core/2010'
}

# document -> item (aggregation)
# document -> item.metadata
# transcript -> item (xml as is)
# transcript -> item.metadata

# TODO title or note contains: documentary or textual

def write_file(path, tree):
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    print
    print 'writing to', path
    print
    tree.write(sys.stdout)
    outfile = open(path, 'w')
    tree.write(outfile)
    outfile.close()
    print

def generate_document_metadata(document_descriptor):
    document_metadata = etree.parse('xml-templates/document-metadata.xml')

    # extract document metadata
    title = document_descriptor.xpath('/f:archivalDocument/f:metadata/f:idno', namespaces=ns)[0].text
    identifier = title
    format = 'application/tei+xml'
    notes = 'A manuscript of the Faust Edition. http://faustedition.de'
    
    title_element = document_metadata.xpath('//tns:title', namespaces=ns)[0]
    title_element.text = title

    return document_metadata

def generate_document_aggregation(document_descriptor, xml_base):
    doc_transcripts = document_descriptor.xpath('//f:docTranscript/@uri', namespaces=ns)
    document_item = etree.parse('xml-templates/document-item.xml')
    for doc_transcript in doc_transcripts:
        full_doc_transcript_path = xml_base + doc_transcript
        rdf_description = document_item.xpath('//rdf:Description', namespaces=ns)[0]
        rdf_description.append(etree.fromstring('<aggregates resource="' + full_doc_transcript_path + '"/>'))
    return document_item

def generate_objects_for_document(document_descriptor_path, xml_dir_path, output_dir_path):

    print
    print '==== handling document', os.path.basename(document_descriptor_path), ' ===='
    print

    document_descriptor = etree.parse(document_descriptor_path)
    xml_base = document_descriptor.xpath('/f:archivalDocument/@xml:base', namespaces=ns)[0]
    relative_base_output_path = os.path.relpath(document_descriptor_path, xml_dir_path)
    base_output_path = os.path.join (output_dir_path, relative_base_output_path)

    # generate aggregation as a textgrid item for the document
    document_aggregation = generate_document_aggregation(document_descriptor, xml_base)
    write_file (base_output_path + '.item', document_aggregation)
    
    # generate metadata for the document aggregation item
    document_metadata = generate_document_metadata(document_descriptor)
    write_file (base_output_path + '.metadata', document_metadata)


def generate_textgrid_objects (xml_dir_path, output_dir_path):
    documents_dir_path = os.path.join(xml_dir_path, 'document')
    for dirpath, dnames, fnames in os.walk(documents_dir_path):
        for document_descriptor_fname in fnames:
            document_descriptor_path = os.path.join(dirpath, document_descriptor_fname)
            generate_objects_for_document(document_descriptor_path, xml_dir_path, output_dir_path)

if len(sys.argv) != 3:
    print
    print 'wrong number of arguments.'
    print '   usage: generate-tg-objects.py path-to-xml-dir path-to-output-dir'
    print
    exit(2)

xml_dir_path = sys.argv[1]
output_dir_path = sys.argv[2]
generate_textgrid_objects(xml_dir_path, output_dir_path)
#generate_objects_for_document(sys.argv[1])
