from abc import ABC, abstractmethod

from healthchain.io.containers import Document


class BaseComponent(ABC):
    """
    Abstract base class for all components in the pipeline.

    This class should be subclassed to create specific components.
    Subclasses must implement the __call__ method.
    """

    @abstractmethod
    def __call__(self, data: Document) -> Document:
        """
        Process the input document and return the processed document.

        Args:
            data (Document): The input document to be processed.

        Returns:
            Document: The processed document.
        """
        pass


class Component(BaseComponent):
    """
    A concrete implementation of the BaseComponent class.

    This class can be used as a base for creating specific components
    that do not require any additional processing logic.

    Methods:
        __call__(data: Document) -> Document:
            Process the input document and return the processed document.
            In this implementation, the input document is returned unmodified.
    """

    def __call__(self, data: Document) -> Document:
        return data
