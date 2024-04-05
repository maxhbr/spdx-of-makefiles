import re
import os
import sys
import csv
import json
import logging
import uuid
from datetime import datetime, timezone
import subprocess
import multiprocessing
from collections import defaultdict
import argparse
from pathlib import Path

from . import spdx3_0 as spdx



class SPDXBuilder:
    def __init__(self, verbose):
        self.logger = logging.getLogger('SPDXBuilder')
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())
        logging.info('INFO: SPDXBuilder initialization ...')

        self.uuid = uuid.uuid4()
        logging.info(f'INFO: UUID: {self.uuid}')

        agent = spdx.SoftwareAgent()
        agent.spdxId = 'SPDXRef-SPDXBuilder'
        agent.name = 'SPDXBuilder'

        creationInfo = spdx.CreationInfo()
        creationInfo.created = datetime.now(timezone.utc)
        creationInfo.createdBy = [ agent.spdxId ]
        creationInfo.comment = 'SPDX data generated by SPDXBuilder'
        creationInfo.specVersion = '3.0.0'
        self.creationInfo = creationInfo

        agent.creationInfo = creationInfo

        # TODO: nedes to be an URI
        self.baseId = f'SPDXRef-{self.uuid}'

        document = spdx.SpdxDocument()
        document.spdxId = self.mk_spdx_id('DOCUMENT')
        document.creationInfo = self.creationInfo
        document.element = [ agent ]
        self.document = document

    def mk_spdx_id(self, appendix=None):
        if not appendix:
            return self.mk_spdx_id(f'{uuid.uuid4()}')
        return f'{self.baseId}-{appendix}'

    def mk_spdx_id_for(self, obj):
        return self.mk_spdx_id(f'{type(obj).__name__}-{uuid.uuid4()}')

    def add_object(self, obj, id_appendix=None):
        if not obj.spdxId:
            if id_appendix:
                obj.spdxId = self.mk_spdx_id(id_appendix)
            else:
                obj.spdxId = self.mk_spdx_id_for(obj)
        obj.creationInfo = self.creationInfo
        self.document.element.append(obj)
        return obj

    def debug_log(self):
        self.logger.info('DEBUG:')
        if self.logger.level == logging.DEBUG:
            spdx.print_tree([self.document])

    def write_to(self, out_file):
        shacl_doc = spdx.SHACLDocument([self.document])
        with out_file.open("wb") as f:
            s = spdx.JSONLDSerializer()
            s.write(shacl_doc, f, force_graph=True)

class SrcDirInput:
    def __init__(self, spdx_builder, src_dir, prefixes_to_strip):
        self.spdx_builder = spdx_builder
        self.src_dir = src_dir
        self.prefixes_to_strip = prefixes_to_strip
        self.prefixes_to_strip.append(str(src_dir))

    def sanitize_path(self, path):
        for prefix in self.prefixes_to_strip:
            if path.startswith(prefix):
                return f".{path[len(prefix):]}"
        return path

    def mk_and_add_spdx_file(self, raw_file_path):
        file_path = self.sanitize_path(raw_file_path)
        file = spdx.software_File()
        file.name = file_path
        local_file_path = self.src_dir / file_path
        if local_file_path.exists():
            sha256 = subprocess.check_output(['sha256sum', self.src_dir / file_path]).split()[0].decode('utf-8')
            hash = spdx.Hash()
            hash.algorithm = spdx.HashAlgorithm.sha256
            hash.hashValue = sha256
            file.verifiedUsing = [hash]
        else:
            logging.warning(f'WARNING: File not found: {local_file_path}')
        return self.spdx_builder.add_object(file, 'FILE-' + file_path.replace('/', '-'))

def main():
    parser = argparse.ArgumentParser(
                    prog='SPDXBuilder',
                    description='Build SPDX file from source directory and analyzer results')
    parser.add_argument('--src', type=Path, required=True)
    parser.add_argument('--src_strip_prefix', action='append')
    parser.add_argument('--artifact', type=str)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('out_dir', type=Path)

    args = parser.parse_args()

    src_dir = args.src

    spdx_builder = SPDXBuilder(args.verbose)

    src_dir_input = SrcDirInput(spdx_builder, src_dir, args.src_strip_prefix)
    src_dir_input.mk_and_add_spdx_file("src/hello.c")
    src_dir_input.mk_and_add_spdx_file("src/hello.o")

    if args.artifact:
        artifact_file = src_dir_input.mk_and_add_spdx_file(args.artifact)
        package = spdx.software_Package()
        package = spdx_builder.add_object(package, 'ARTIFACT')
        # package.name = args.package.name
        # package.comment = 'Artifact file'
        package_to_file_relationship = spdx.Relationship()
        package_to_file_relationship.from_ = package
        package_to_file_relationship.relationshipType = spdx.RelationshipType.hasDistributionArtifact
        package_to_file_relationship.to = [artifact_file]
        spdx_builder.add_object(package_to_file_relationship)

    spdx_builder.debug_log()
    out_dir = args.out_dir
    if not out_dir.exists():
        out_dir.mkdir()
    out_file = out_dir / 'spdx.jsonld'
    spdx_builder.write_to(out_file)
