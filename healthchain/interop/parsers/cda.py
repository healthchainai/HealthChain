"""
CDA Parser for HealthChain Interoperability Engine

This module provides functionality for parsing CDA XML documents.
"""

import xmltodict
import logging
from typing import Dict, List

from healthchain.interop.models.cda import ClinicalDocument
from healthchain.interop.models.sections import Section
from healthchain.interop.config_manager import InteropConfigManager
from healthchain.interop.parsers.base import BaseParser

log = logging.getLogger(__name__)


class CDAParser(BaseParser):
    """Parser for CDA XML documents.

    The CDAParser class provides functionality to parse Clinical Document Architecture (CDA)
    XML documents and extract structured data from their sections. It works in conjunction with
    the InteropConfigManager to identify and process sections based on configuration.

    Key capabilities:
    - Parse complete CDA XML documents
    - Extract entries from configured sections based on template IDs or codes
    - Convert and validate section entries into structured dictionaries (xmltodict)

    The parser uses configuration from InteropConfigManager to:
    - Identify sections by template ID or code
    - Map section contents to the appropriate data structures
    - Apply any configured transformations

    Attributes:
        config (InteropConfigManager): Configuration manager instance
        clinical_document (ClinicalDocument): Currently loaded CDA document
    """

    def __init__(self, config: InteropConfigManager):
        """Initialize the CDA parser.

        Args:
            config: InteropConfigManager instance containing section configurations,
                   templates, and mapping rules for CDA document parsing
        """
        super().__init__(config)
        self.clinical_document = None

    def from_string(self, data: str) -> dict:
        """
        Parse input data and convert it to a structured format.

        Args:
            data: The CDA XML document string to parse

        Returns:
            A dictionary containing the parsed data structure with sections
        """
        return self.parse_document(data)

    def parse_document(self, xml: str) -> Dict[str, List[Dict]]:
        """Parse a complete CDA document and extract entries from all configured sections.

        This method parses a CDA XML document and extracts entries from each section that is
        defined in the configuration. It uses xmltodict to parse the XML into a dictionary
        and then processes each configured section to extract its entries.

        Args:
            xml: The CDA XML document string to parse

        Returns:
            Dict[str, List[Dict]]: Dictionary mapping section keys (e.g. "problems",
                "medications") to lists of entry dictionaries containing the parsed data
                from that section (xmltodict format).

        Raises:
            ValueError: If the XML string is empty or invalid
            Exception: If there is an error parsing the document or any section

        Example:
            >>> parser = CDAParser(config)
            >>> sections = parser.from_string(cda_xml)
            >>> problems = sections.get("problems", [])
        """
        section_entries = {}

        # Parse the document once
        try:
            doc_dict = xmltodict.parse(xml)
            self.clinical_document = ClinicalDocument(**doc_dict["ClinicalDocument"])
        except Exception as e:
            log.error(f"Error parsing CDA document: {str(e)}")
            return section_entries

        # Get section configurations
        sections = self.config.get_cda_section_configs()
        if not sections:
            log.warning("No sections found in configuration")
            return section_entries

        # Warn (never silently drop) about any sections present in the document
        # that don't match a configured section, e.g. an allergies section when
        # only problems/medications/notes are configured
        self._warn_unconfigured_sections(sections)

        # Process each section from the configuration
        for section_key in sections.keys():
            try:
                entries = self._parse_section_entries_from_document(section_key)
                if entries:
                    section_entries[section_key] = entries
            except Exception as e:
                log.error(f"Failed to parse section {section_key}: {str(e)}")
                continue

        return section_entries

    def _parse_section_entries_from_document(self, section_key: str) -> List[Dict]:
        """Extract entries from a CDA section using an already parsed document.

        Args:
            section_key: Key identifying the section in the configuration (e.g. "problems",
                "medications"). Must match a section defined in the configuration.

        Returns:
            List[Dict]: List of entry dictionaries from the matched section. Each dictionary
                contains the parsed data from a single entry in the section. Returns an empty
                list if no entries are found or if an error occurs.

        Raises:
            ValueError: If no template_id or code is configured for the section_key, or if
                no matching section is found in the document.
            Exception: If there is an error parsing the section or its entries.
        """
        entries_dicts = []
        if not self.clinical_document:
            log.error("No document loaded. Call parse_document first.")
            return entries_dicts

        try:
            # Get all components
            components = self.clinical_document.component.structuredBody.component
            if not isinstance(components, list):
                components = [components]

            # Find matching section
            section = None
            for component in components:
                curr_section = component.section

                # Get template_id and code from config_manager
                template_id = self.config.get_config_value(
                    f"cda.sections.{section_key}.identifiers.template_id"
                )
                code = self.config.get_config_value(
                    f"cda.sections.{section_key}.identifiers.code"
                )

                if not template_id and not code:
                    raise ValueError(
                        f"No template_id or code found for section {section_key}: \
                            configure one of the following: \
                            cda.sections.{section_key}.identifiers.template_id \
                            or cda.sections.{section_key}.identifiers.code"
                    )

                if template_id and self._find_section_by_template_id(
                    curr_section, template_id
                ):
                    section = curr_section
                    break

                if code and self._find_section_by_code(curr_section, code):
                    section = curr_section
                    break

            if not section:
                log.warning(
                    f"Section with template_id: {template_id} or code: {code} not found in CDA document for key: {section_key}"
                )
                return entries_dicts

            # Check if this is a notes section (which doesn't have entries but has text) - temporary workaround
            if section_key == "notes":
                # For notes section, create a synthetic entry with the section's text content
                section_dict = section.model_dump(exclude_none=True, by_alias=True)
                log.debug(
                    f"Created synthetic entry for notes section with text: {type(section.text)}"
                )
                # Return the entire section as the entry for DocumentReference
                return [section_dict]

            # Get entries from section (normal case for other sections)
            if section.entry:
                entries_dicts = (
                    section.entry
                    if isinstance(section.entry, list)
                    else [section.entry]
                )
            else:
                log.warning(f"No entries found for section {section_key}")
                return entries_dicts

            # Convert entries to dictionaries
            entry_dicts = [
                entry.model_dump(exclude_none=True, by_alias=True)
                for entry in entries_dicts
                if entry
            ]

            log.debug(f"Found {len(entry_dicts)} entries in section {section_key}")

            return entry_dicts

        except Exception as e:
            log.error(f"Error parsing section {section_key}: {str(e)}")
            return entries_dicts

    def _warn_unconfigured_sections(self, sections_config: Dict) -> None:
        """Log a warning for each CDA section in the document with no matching
        section configuration, so unconfigured content (e.g. an allergies
        section when only problems/medications/notes are configured) is
        surfaced rather than silently skipped.

        Args:
            sections_config: Mapping of configured section keys to their
                configuration, as returned by
                InteropConfigManager.get_cda_section_configs()
        """
        if not self.clinical_document:
            return

        try:
            components = self.clinical_document.component.structuredBody.component
        except AttributeError:
            return

        if not isinstance(components, list):
            components = [components]

        # Collect (template_id, code) identifiers for all configured sections once
        configured_identifiers = [
            (
                section_config.get("identifiers", {}).get("template_id")
                if isinstance(section_config, dict)
                else None,
                section_config.get("identifiers", {}).get("code")
                if isinstance(section_config, dict)
                else None,
            )
            for section_config in sections_config.values()
        ]

        for component in components:
            section = component.section

            matched = any(
                (
                    template_id
                    and self._find_section_by_template_id(section, template_id)
                )
                or (code and self._find_section_by_code(section, code))
                for template_id, code in configured_identifiers
            )

            if matched:
                continue

            section_code = section.code.code if section.code else None
            section_display = section.code.displayName if section.code else None

            log.warning(
                "Skipping CDA section not configured for conversion: "
                f"title={section.title!r}, code={section_code!r}, "
                f"display={section_display!r}. This section will not be "
                "converted to FHIR. Configure it under "
                "cda.sections.<key>.identifiers to include it."
            )

    def _find_section_by_template_id(self, section: Section, template_id: str) -> bool:
        """Returns True if section has matching template ID"""
        if not section.templateId:
            return False

        template_ids = (
            section.templateId
            if isinstance(section.templateId, list)
            else [section.templateId]
        )
        return any(tid.root == template_id for tid in template_ids)

    def _find_section_by_code(self, section: Section, code: str) -> bool:
        """Returns True if section has matching code"""
        return bool(section.code and section.code.code == code)
