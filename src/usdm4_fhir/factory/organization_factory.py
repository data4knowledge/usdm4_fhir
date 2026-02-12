from simple_error_log import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.organization import Organization as FHIROrganization
from usdm4.api.organization import Organization as USDMOrganization
from .address_factory import AddressFactory
from uuid import uuid4


class OrganizationFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.organization_factory.OrganizationFactory"

    def __init__(self, errors: Errors, organization: USDMOrganization):
        try:
            super().__init__(errors, **{})
            address = AddressFactory(
                errors=self._errors, address=organization.legalAddress
            )
            self._errors.debug(
                f"Address created: {address} from {organization.legalAddress}",
                KlassMethodLocation(self.MODULE, "__init__"),
            )
            name = organization.label if organization.label else organization.name
            self.item = FHIROrganization(
                id=str(uuid4()), name=name, contact=[{"address": address.item}]
            )
            self._errors.debug(
                f"Organization created: {self.item}",
                KlassMethodLocation(self.MODULE, "__init__"),
            )
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
