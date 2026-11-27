import logging

from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel

from healthchain.gateway.base import BaseProtocolHandler
from healthchain.gateway.cds.events import create_cds_hook_event
from healthchain.gateway.events.dispatcher import EventDispatcher
from healthchain.models.requests.cdsrequest import CDSRequest
from healthchain.models.responses.cdsdiscovery import CDSService, CDSServiceInformation
from healthchain.models.responses.cdsresponse import CDSResponse
from healthchain.sandbox.workflows import UseCaseMapping


logger = logging.getLogger(__name__)

# Type variable for self-referencing return types
T = TypeVar("T", bound="CDSHooksService")


class CDSHooksConfig(BaseModel):
    """Configuration options for CDS Hooks service"""

    system_type: str = "CDS-HOOKS"
    base_path: str = "/cds"
    discovery_path: str = "/cds-discovery"
    service_path: str = "/cds-services"
    allowed_hooks: List[str] = UseCaseMapping.ClinicalDecisionSupport.allowed_workflows


class CDSHooksService(BaseProtocolHandler[CDSRequest, CDSResponse], APIRouter):
    """
    Service for CDS Hooks protocol integration.

    This service implements the CDS Hooks standard for integrating clinical decision
    support with EHR systems. It provides discovery and hook execution endpoints
    that conform to the CDS Hooks specification.

    Example:
        ```python
        # Create a CDS Hooks service
        cds_service = CDSHooksService()

        # Register a hook handler
        @cds_service.hook("patient-view", id="patient-summary")
        def handle_patient_view(request: CDSRequest) -> CDSResponse:
            # Create cards based on the patient context
            return CDSResponse(
                cards=[
                    {
                        "summary": "Patient has allergies",
                        "indicator": "warning",
                        "detail": "Patient has multiple allergies that may be relevant"
                    }
                ]
            )

        # Register the service with the API
        app.register_service(cds_service)
        ```
    """

    def __init__(
        self,
        config: Optional[CDSHooksConfig] = None,
        event_dispatcher: Optional[EventDispatcher] = None,
        use_events: bool = True,
        **options,
    ):
        """
        Initialize a new CDS Hooks service.

        Args:
            config: Configuration options for the service
            event_dispatcher: Optional event dispatcher for publishing events
            use_events: Whether to enable event dispatching functionality
            **options: Additional options for the service
        """
        # Initialize the base protocol handler
        BaseProtocolHandler.__init__(self, use_events=use_events, **options)

        # Initialize specific configuration
        self.config = config or CDSHooksConfig()

        # Initialize APIRouter with configuration
        APIRouter.__init__(self, prefix=self.config.base_path, tags=["CDS Hooks"])

        self._handler_metadata = {}
        self._service_handlers: Dict[str, Callable] = {}
        self._service_metadata: Dict[str, Dict[str, Any]] = {}

        # Set event dispatcher if provided
        if event_dispatcher and use_events:
            self.events.set_dispatcher(event_dispatcher)

        self._register_base_routes()

    def _get_service_dependency(self):
        """Create a dependency function that returns this service instance."""

        def get_self_service():
            return self

        return get_self_service

    def _register_base_routes(self):
        """Register base routes for CDS Hooks service."""
        get_self_service = self._get_service_dependency()

        # Discovery endpoint
        discovery_path = self.config.discovery_path.lstrip("/")

        @self.get(
            f"/{discovery_path}",
            response_model=CDSServiceInformation,
            response_model_exclude_none=True,
        )
        async def discovery_handler(cds: "CDSHooksService" = Depends(get_self_service)):
            """CDS Hooks discovery endpoint."""
            return cds.handle_discovery()

    def _register_hook_route(self, hook_id: str):
        """Register a route for a specific hook ID."""
        get_self_service = self._get_service_dependency()
        service_path = self.config.service_path.lstrip("/")
        endpoint = f"/{service_path}/{hook_id}"

        async def service_handler(
            request: CDSRequest = Body(...),
            cds: "CDSHooksService" = Depends(get_self_service),
        ):
            """CDS Hook service endpoint."""
            return cds.handle_request(request, service_id=hook_id)

        self.add_api_route(
            path=endpoint,
            endpoint=service_handler,
            methods=["POST"],
            response_model=CDSResponse,
            response_model_exclude_none=True,
            summary=f"CDS Hook: {hook_id}",
            description=f"Execute CDS Hook service: {hook_id}",
        )

        logger.debug(f"Registered CDS Hook endpoint: {self.prefix}{endpoint}")

    def hook(
        self,
        hook_type: str,
        id: str,
        title: Optional[str] = None,
        description: Optional[str] = "CDS Hook service created by HealthChain",
        usage_requirements: Optional[str] = None,
    ) -> Callable:
        """
        Decorator to register a handler for a specific CDS hook type.

        Args:
            hook_type: The CDS Hook type (e.g., "patient-view")
            id: Unique identifier for this specific hook
            title: Human-readable title for this hook. If not provided, the hook type will be used.
            description: Human-readable description of this hook
            usage_requirements: Human-readable description of any preconditions for the use of this CDS service.

        Returns:
            Decorator function that registers the handler
        """

        def decorator(handler):
            if hook_type not in self.config.allowed_hooks:
                raise ValueError(
                    f"Hook type {hook_type} is not allowed. Must be one of: {self.config.allowed_hooks}"
                )
            if id in self._service_handlers:
                raise ValueError(
                    f"CDS hook service with id '{id}' is already registered"
                )

            service_title = title or hook_type.replace("-", " ").title()

            # Track handlers and metadata by service id so multiple services can share a hook type
            self._service_handlers[id] = handler
            self._service_metadata[id] = {
                "hook": hook_type,
                "id": id,
                "title": service_title,
                "description": description,
                "usage_requirements": usage_requirements,
            }

            # Maintain hook-type mapping for backward compatibility with direct dispatch()
            self.register_handler(hook_type, handler)
            self._handler_metadata[hook_type] = {
                "id": id,
                "title": service_title,
                "description": description,
                "usage_requirements": usage_requirements,
            }

            # Register the route for this hook
            self._register_hook_route(id)

            return handler

        return decorator

    def handle_discovery(self) -> CDSServiceInformation:
        """
        Get the CDS Hooks service definition for discovery.

        Returns:
            CDSServiceInformation containing the CDS Hooks service definition
        """
        services = []
        hook_metadata = self.get_metadata()

        for metadata in hook_metadata:
            service_info = CDSService(
                hook=metadata["hook"],
                description=metadata["description"],
                id=metadata["id"],
                title=metadata["title"],
                usage_requirements=metadata["usage_requirements"],
            )
            services.append(service_info)

        return CDSServiceInformation(services=services)

    def handle_request(
        self, request: CDSRequest, service_id: Optional[str] = None
    ) -> CDSResponse:
        """
        CDS service endpoint handler.

        Args:
            request: CDSRequest object
            service_id: Optional registered service id from the endpoint route

        Returns:
            CDSResponse object
        """
        hook_type = request.hook

        if service_id is not None:
            handler = self._service_handlers.get(service_id)
            if handler is None:
                logger.warning(f"No handler registered for CDS service id: {service_id}")
                response = CDSResponse(cards=[])
            else:
                response = self._invoke_handler(
                    handler, request, f"service id: {service_id}"
                )
        else:
            response = self.dispatch(hook_type, request=request)

        # If we have an event dispatcher, emit an event for the hook execution
        if self.events.dispatcher and self.use_events:
            try:
                self._emit_hook_event(hook_type, request, response)
            except Exception as e:
                # Log error but don't fail the request
                logger.error(
                    f"Error dispatching event for CDS hook: {str(e)}", exc_info=True
                )

        return response

    def _extract_request(self, operation: str, params: Dict) -> Optional[CDSRequest]:
        """
        Extract or construct a CDSRequest from parameters.

        Args:
            operation: The hook type e.g. "patient-view"
            params: The parameters passed to dispatch

        Returns:
            CDSRequest object or None if request couldn't be constructed
        """
        try:
            # Case 1: Direct CDSRequest passed as a parameter
            if "request" in params and isinstance(params["request"], CDSRequest):
                return params["request"]

            # Case 2: First parameter is a CDSRequest
            if len(params) == 1 and isinstance(next(iter(params.values())), CDSRequest):
                return next(iter(params.values()))

            # Case 3: Operation matches a hook type - build a CDSRequest
            if operation in self._handlers:
                # Build a CDSRequest from operation and params
                return CDSRequest(**params)

            # No valid request could be constructed
            logger.warning(f"Unable to construct CDSRequest for hook type: {operation}")
            return None

        except Exception as e:
            logger.warning(f"Error constructing CDSRequest: {str(e)}", exc_info=True)
            return None

    def dispatch(self, operation: str, **params) -> Union[CDSResponse, Dict]:
        """
        Process a CDS Hooks request using registered handlers.

        Args:
            operation: The hook type being triggered e.g. "patient-view"
            **params: Either a CDSRequest object or raw parameters

        Returns:
            CDSResponse object with the results of the operation
        """
        if operation not in self._handlers:
            logger.warning(f"No handler registered for hook type: {operation}")
            return CDSResponse(cards=[])

        # Handle direct CDSRequest objects
        request = self._extract_request(operation, params)
        if not request:
            return CDSResponse(cards=[])

        # Execute the handler with the request
        return self._execute_handler(request)

    def _invoke_handler(
        self, handler: Callable, request: CDSRequest, target: str
    ) -> CDSResponse:
        """Execute a CDS handler and normalize its result to a CDSResponse."""
        try:
            logger.debug(f"Calling handler for {target}")
            result = handler(request)
            return self._process_result(result)
        except Exception as e:
            logger.error(f"Error in CDS hook handler: {str(e)}", exc_info=True)
            return CDSResponse(cards=[])

    def _execute_handler(self, request: CDSRequest) -> CDSResponse:
        """
        Execute a registered CDS hook with the given request.

        Args:
            request: CDSRequest object containing hook parameters

        Returns:
            CDSResponse object with cards
        """
        hook_type = request.hook
        handler = self._handlers[hook_type]
        return self._invoke_handler(handler, request, f"hook type: {hook_type}")

    def _process_result(self, result: Any) -> CDSResponse:
        """
        Convert handler result to a CDSResponse.

        Args:
            result: The result returned by the handler

        Returns:
            CDSResponse object
        """
        # If the result is already a CDSResponse, return it
        if isinstance(result, CDSResponse):
            return result

        try:
            # Otherwise, create a CDSResponse from the result
            if isinstance(result, dict) and "cards" in result:
                return CDSResponse(**result)
            logger.warning(f"Unexpected result type from handler: {type(result)}")
            return CDSResponse(cards=[])
        except Exception as e:
            logger.error(f"Error processing result to CDSResponse: {str(e)}")
            return CDSResponse(cards=[])

    def _emit_hook_event(
        self, hook_type: str, request: CDSRequest, response: CDSResponse
    ):
        """
        Emit an event for CDS hook invocation.

        Args:
            hook_type: The hook type being invoked (e.g., "patient-view")
            request: The CDSRequest object
            response: The CDSResponse object
        """
        self.events.emit_event(
            create_cds_hook_event,
            hook_type,
            request,
            response,
            use_events=self.use_events,
        )

    def get_metadata(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all registered hooks.

        Returns:
            List of hook metadata dictionaries
        """
        if self._service_metadata:
            return [dict(meta) for meta in self._service_metadata.values()]

        metadata = []
        for hook_type in self._handlers.keys():
            hook_metadata = self._handler_metadata.get(hook_type, {})
            metadata.append(
                {
                    "hook": hook_type,
                    "id": hook_metadata.get("id"),
                    "title": hook_metadata.get("title"),
                    "description": hook_metadata.get("description"),
                    "usage_requirements": hook_metadata.get("usage_requirements"),
                }
            )

        return metadata
