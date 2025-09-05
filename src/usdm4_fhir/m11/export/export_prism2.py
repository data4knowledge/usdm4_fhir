import datetime
from simple_error_log.error_location import KlassMethodLocation
from usdm4_fhir.m11.export.export_base import ExportBase
from usdm4.api.narrative_content import NarrativeContent
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference


class ExportPRISM2(ExportBase):
    MODULE = "usdm4_fhir.m11.export.ExportPRISM2"

    class LogicError(Exception):
        pass

    def to_message(self):
        try:
            sections = self._process_sections()
            type_code = CodeableConcept(text="EvidenceReport")
            date_now = datetime.datetime.now(tz=datetime.timezone.utc)
            date_str = date_now.isoformat()
            author = Reference(display="USDM")
            title = self.study_version.official_title_text()
            composition = Composition(
                title=title,
                type=type_code,
                section=sections,
                date=date_str,
                status="preliminary",
                author=[author],
            )
            identifier = Identifier(
                system="urn:ietf:rfc:3986", value=f"urn:uuid:{self._uuid}"
            )
            bundle_entry = BundleEntry(
                resource=composition, fullUrl="https://www.example.com/Composition/1234"
            )
            bundle = Bundle(
                id=None,
                entry=[bundle_entry],
                type="document",
                identifier=identifier,
                timestamp=date_str,
            )
            return bundle.json()
        except Exception as e:
            self._errors.exception(
                "Exception raised generating FHIR PRISM2 M11 message.",
                e,
                KlassMethodLocation(self.MODULE, "to_message")
            )
            return None

