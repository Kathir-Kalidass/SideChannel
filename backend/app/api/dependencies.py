from starlette.requests import HTTPConnection

from app.services.simulation_service import SimulationService


def get_simulation_service(connection: HTTPConnection) -> SimulationService:
    return connection.app.state.simulation_service
