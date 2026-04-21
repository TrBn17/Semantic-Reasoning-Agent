class UnsupportedDocumentTypeError(ValueError):
    """Raised when the upload format is not supported."""


class DocumentNotFoundError(ValueError):
    """Raised when a document id does not exist."""


class DocumentProcessingError(ValueError):
    """Raised when a document fails to process."""
