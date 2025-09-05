from d4k_ms_base import Service, ServiceEnvironment

class AddressService(Service):
    def __init__(self):
        se = ServiceEnvironment()
        super().__init__(se.get["ADDRESS_SERVER_URL"])

    def parser(self, address: str) -> dict:
        return super().post("parser", data={"query": address})
