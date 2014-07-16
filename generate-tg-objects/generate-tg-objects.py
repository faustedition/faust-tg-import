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

# TODO title or note contains: documentary or textual

def write_file(path, tree):
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    print 'writing to', path

    # tree.write(sys.stdout)
    outfile = open(path, 'w')
    tree.write(outfile)
    outfile.close()

def append_idno_nodes(idno_nodes, metadata_tree):
    provided_element = metadata_tree.xpath('//tns:provided', namespaces=ns)[0]

    for (type_attr, idno) in idno_nodes:
            identifier_node = etree.fromstring(
                '<tns:identifier xmlns:tns="' + ns['tns'] + '" type="' + type_attr + '"/>')
            identifier_node.text = idno
            provided_element.insert(len(provided_element) - 1, identifier_node)

def generate_document_metadata(document_descriptor, document_title, idno_nodes):
    document_metadata = etree.parse('xml-templates/document.aggregation.meta')

    # extract document metadata
    format = 'application/tei+xml'
    notes = 'A manuscript of the Faust Edition. http://faustedition.de'
    
    title_element = document_metadata.xpath('//tns:title', namespaces=ns)[0]
    title_element.text = document_title
    
    append_idno_nodes(idno_nodes, document_metadata)

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

    document_item = etree.parse('xml-templates/document.aggregation')

    for doc_transcript in paths_relative_from_document_descriptor:
        rdf_description = document_item.xpath('//rdf:Description', namespaces=ns)[0]

        rdf_description.append(etree.fromstring('<ore:aggregates xmlns:ore="' + ns['ore'] + '" xmlns:rdf="'+ ns['rdf'] +'" rdf:resource="' + doc_transcript + '"/>'))
    return document_item

def generate_transcript_metadata(transcript, pagenum, document_title, idno_nodes):
    transcript_metadata = etree.parse('xml-templates/transcript.meta')
    title_element = transcript_metadata.xpath('//tns:title', namespaces=ns)[0]
    title_element.text = document_title + ', Seite ' + str(pagenum)

    append_idno_nodes(idno_nodes, transcript_metadata)

    return transcript_metadata

def generate_objects_for_document(document_descriptor_path, xml_dir_path, output_dir_path):

    print '==== handling document', os.path.basename(document_descriptor_path), ' ===='

    document_descriptor = etree.parse(document_descriptor_path)

    relative_base_output_path = os.path.relpath(document_descriptor_path, xml_dir_path)
    base_output_path = os.path.join (output_dir_path, relative_base_output_path)

    # generate aggregation as a textgrid item for the document

    path_from_document_descriptor_to_xml_dir = os.path.relpath(xml_dir_path, document_descriptor_path)
    document_aggregation = generate_document_aggregation(document_descriptor, path_from_document_descriptor_to_xml_dir)
    document_out_path = base_output_path + '.aggregation'
    write_file (document_out_path, document_aggregation)
    
    # generate metadata for the document aggregation item
    document_title = document_descriptor.xpath('/f:archivalDocument/f:metadata/f:idno', namespaces=ns)[0].text
    idno_nodes = [(node.get('type'), node.text) for node in document_descriptor.xpath('/f:archivalDocument/f:metadata/f:idno', namespaces=ns)]
    document_metadata = generate_document_metadata(document_descriptor, document_title, idno_nodes)
    write_file (base_output_path + '.aggregation.meta', document_metadata)

    # generate metadata for transcripts
    document_transcript_uris = document_transcript_faust_uris(document_descriptor)
    document_transcripts_relative_from_xml_dir = [faust_uri[len('faust://xml/'):] for faust_uri in document_transcript_uris]

    for (pagenum, document_transcript_relative_from_xml_dir) in enumerate(document_transcripts_relative_from_xml_dir, start=1):
            document_transcript_absolute_path = os.path.join(xml_dir_path, document_transcript_relative_from_xml_dir)
            document_transcript_output_path = os.path.join(output_dir_path, document_transcript_relative_from_xml_dir)
            transcript_metadata_output_path = document_transcript_output_path + '.meta'
            print 'generating metadata for transcript in', transcript_metadata_output_path            
            transcript = etree.parse(document_transcript_absolute_path)
            transcript_metadata = generate_transcript_metadata(transcript, pagenum, document_title, idno_nodes)
            write_file (transcript_metadata_output_path, transcript_metadata)
    
    return document_out_path

def generate_edition(document_out_paths):
    edition = etree.parse('xml-templates/faustedition.edition')
    rdf_description = edition.xpath('//rdf:Description', namespaces=ns)[0]
    for document_out_path in document_out_paths:
        rdf_description.append(etree.fromstring('<ore:aggregates xmlns:ore="' + ns['ore'] + '" xmlns:rdf="' + ns['rdf'] + '" rdf:resource="' + document_out_path + '"/>'))
    return edition

def generate_textgrid_objects (xml_dir_path, output_dir_path):

    # copy all transcripts

    transcripts_dir_path = os.path.join(xml_dir_path, 'transcript')
    transcripts_destination_dir_path = os.path.join(output_dir_path, 'transcript')
    print '==== copying all transcripts to', transcripts_destination_dir_path, '===='
    shutil.copytree(transcripts_dir_path, transcripts_destination_dir_path)

    # copy faust work, faust work metadata, edition metadata

    shutil.copy('xml-templates/faust.work', output_dir_path)
    shutil.copy('xml-templates/faust.work.meta', output_dir_path)
    shutil.copy('xml-templates/faustedition.edition.meta', output_dir_path)

    # iterate over all documents

    documents_dir_path = os.path.join(xml_dir_path, 'document')
    document_out_paths = []
    for dirpath, dnames, fnames in os.walk(documents_dir_path):
        for document_descriptor_fname in fnames:
            document_descriptor_path = os.path.join(dirpath, document_descriptor_fname)

            # print relative_document_descriptor_path

            document_out_path = generate_objects_for_document(document_descriptor_path, xml_dir_path, output_dir_path)
            relative_document_out_path = os.path.relpath(document_out_path, output_dir_path )
            document_out_paths.append(relative_document_out_path)
          
    # edition aggregates all documents

    edition = generate_edition(document_out_paths)
    write_file(os.path.join(output_dir_path, 'faustedition.edition'), edition)
    
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
