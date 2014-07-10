#!/usr/bin/env python
# coding=UTF-8
#
# Generate TextGrid Objects for import

from lxml import etree
import sys
import os.path
import shutil

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


    print 'writing to', path

    # tree.write(sys.stdout)
    outfile = open(path, 'w')
    tree.write(outfile)
    outfile.close()


def generate_document_metadata(document_descriptor, document_title):
    document_metadata = etree.parse('xml-templates/document-metadata.xml')

    # extract document metadata
    format = 'application/tei+xml'
    notes = 'A manuscript of the Faust Edition. http://faustedition.de'
    
    title_element = document_metadata.xpath('//tns:title', namespaces=ns)[0]
    title_element.text = document_title

    return document_metadata

def document_transcript_faust_uris(document_descriptor):
    xml_base = document_descriptor.xpath('/f:archivalDocument/@xml:base', namespaces=ns)[0]
    local_names = document_descriptor.xpath('//f:docTranscript/@uri', namespaces=ns)
    faust_uris = [os.path.join(xml_base, local_name) for local_name in local_names]
    return faust_uris

def generate_document_aggregation(document_descriptor, path_from_document_descriptor_to_xml_dir):
    doc_transcript_faust_uris = document_transcript_faust_uris(document_descriptor)

    document_transcripts_relative_from_xml_dir = [faust_uri[len('faust://xml/'):] for faust_uri in doc_transcript_faust_uris]
    paths_relative_from_document_descriptor = [os.path.join(path_from_document_descriptor_to_xml_dir, path_relative_from_xml_dir) 
                                               for path_relative_from_xml_dir in document_transcripts_relative_from_xml_dir]
    
    document_item = etree.parse('xml-templates/document-item.xml')
    for doc_transcript in paths_relative_from_document_descriptor:
        rdf_description = document_item.xpath('//rdf:Description', namespaces=ns)[0]
        rdf_description.append(etree.fromstring('<aggregates resource="' + doc_transcript + '"/>'))
    return document_item

def generate_transcript_metadata(transcript, pagenum, document_title):
    transcript_metadata = etree.parse('xml-templates/transcript-metadata.xml')
    title_element = transcript_metadata.xpath('//tns:title', namespaces=ns)[0]
    title_element.text = document_title + ', Seite ' + str(pagenum)
    return transcript_metadata

def generate_objects_for_document(document_descriptor_path, xml_dir_path, output_dir_path):

    print '==== handling document', os.path.basename(document_descriptor_path), ' ===='

    document_descriptor = etree.parse(document_descriptor_path)

    relative_base_output_path = os.path.relpath(document_descriptor_path, xml_dir_path)
    base_output_path = os.path.join (output_dir_path, relative_base_output_path)

    # generate aggregation as a textgrid item for the document

    path_from_document_descriptor_to_xml_dir = os.path.relpath(xml_dir_path, document_descriptor_path)
    document_aggregation = generate_document_aggregation(document_descriptor, path_from_document_descriptor_to_xml_dir)
    write_file (base_output_path + '.item', document_aggregation)
    
    # generate metadata for the document aggregation item
    document_title = document_descriptor.xpath('/f:archivalDocument/f:metadata/f:idno', namespaces=ns)[0].text
    document_metadata = generate_document_metadata(document_descriptor, document_title)
    write_file (base_output_path + '.metadata', document_metadata)

    # generate metadata for transcripts
    document_transcript_uris = document_transcript_faust_uris(document_descriptor)
    document_transcripts_relative_from_xml_dir = [faust_uri[len('faust://xml/'):] for faust_uri in document_transcript_uris]

    for (pagenum, document_transcript_relative_from_xml_dir) in enumerate(document_transcripts_relative_from_xml_dir, start=1):
            document_transcript_absolute_path = os.path.join(xml_dir_path, document_transcript_relative_from_xml_dir)
            document_transcript_output_path = os.path.join(output_dir_path, document_transcript_relative_from_xml_dir)
            transcript_metadata_output_path = document_transcript_output_path + '.metadata'
            print 'generating metadata for transcript in', transcript_metadata_output_path            
            transcript = etree.parse(document_transcript_absolute_path)
            transcript_metadata = generate_transcript_metadata(transcript, pagenum, document_title)
            write_file (transcript_metadata_output_path, transcript_metadata)

def generate_textgrid_objects (xml_dir_path, output_dir_path):

    transcripts_dir_path = os.path.join(xml_dir_path, 'transcript')
    transcripts_destination_dir_path = os.path.join(output_dir_path, 'transcript')
    print '==== copying all transcripts to', transcripts_destination_dir_path, '===='
    shutil.copytree(transcripts_dir_path, transcripts_destination_dir_path)
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
